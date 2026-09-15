#include "avi_player.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "esp_jpeg_dec.h"

static const char *TAG = "AVI_PLAYER_SIMD";

static FILE *s_file = NULL;
static avi_info_t s_info;
static long s_movi_start_offset = 0;
static uint32_t *s_index_table = NULL;

#define JPEG_INBUF_SIZE (36 * 1024)
static uint8_t *s_jpeg_buf = NULL;

static jpeg_dec_handle_t s_dec_full = NULL;
static jpeg_dec_handle_t s_dec_studio = NULL;

esp_err_t avi_player_init(void) {
    ESP_LOGI(TAG, "Inicializando motor de video SIMD (esp_new_jpeg)...");

    memset(&s_info, 0, sizeof(s_info));

    if (!s_jpeg_buf) {
        s_jpeg_buf = (uint8_t *)heap_caps_malloc(JPEG_INBUF_SIZE, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
        if (!s_jpeg_buf) s_jpeg_buf = (uint8_t *)malloc(JPEG_INBUF_SIZE);
        if (!s_jpeg_buf) {
            ESP_LOGE(TAG, "Fallo al reservar s_jpeg_buf (36 KB)");
            return ESP_ERR_NO_MEM;
        }
    }

    // 1. Decoder para Fullscreen 480x320 (RGB565 Little Endian)
    if (!s_dec_full) {
        jpeg_dec_config_t cfg_full = DEFAULT_JPEG_DEC_CONFIG();
        cfg_full.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;
        cfg_full.rotate = JPEG_ROTATE_0D;
        cfg_full.block_enable = false;
        jpeg_error_t err = jpeg_dec_open(&cfg_full, &s_dec_full);
        if (err != JPEG_ERR_OK) {
            ESP_LOGE(TAG, "Fallo al crear decoder Fullscreen: %d", err);
            return ESP_FAIL;
        }
    }

    // 2. Decoder para Studio 240x160 con hardware downsampling SIMD
    if (!s_dec_studio) {
        jpeg_dec_config_t cfg_std = DEFAULT_JPEG_DEC_CONFIG();
        cfg_std.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;
        cfg_std.scale.width = 240;
        cfg_std.scale.height = 160;
        cfg_std.rotate = JPEG_ROTATE_0D;
        cfg_std.block_enable = false;
        jpeg_error_t err = jpeg_dec_open(&cfg_std, &s_dec_studio);
        if (err != JPEG_ERR_OK) {
            ESP_LOGE(TAG, "Fallo al crear decoder Studio (Downscale 2:1): %d", err);
            return ESP_FAIL;
        }
    }

    ESP_LOGI(TAG, "Decodificadores SIMD Fullscreen y Studio inicializados con éxito.");
    return ESP_OK;
}

esp_err_t avi_player_open(const char *filepath) {
    avi_player_close();

    ESP_LOGI(TAG, "Abriendo archivo AVI MJPEG: %s", filepath);
    s_file = fopen(filepath, "rb");
    if (!s_file) {
        ESP_LOGE(TAG, "No se pudo abrir el archivo %s", filepath);
        return ESP_FAIL;
    }

    fseek(s_file, 0, SEEK_END);
    long file_size = ftell(s_file);
    fseek(s_file, 0, SEEK_SET);

    uint8_t *hdr = s_jpeg_buf;
    size_t r = fread(hdr, 1, 16 * 1024, s_file);
    if (r < 128 || memcmp(hdr, "RIFF", 4) != 0 || memcmp(hdr + 8, "AVI ", 4) != 0) {
        ESP_LOGE(TAG, "Encabezado RIFF AVI no válido");
        fclose(s_file);
        s_file = NULL;
        return ESP_FAIL;
    }

    // Buscar bloque avih
    int avih_pos = -1;
    for (size_t i = 0; i < r - 56; i++) {
        if (memcmp(hdr + i, "avih", 4) == 0) {
            avih_pos = i;
            break;
        }
    }

    if (avih_pos >= 0) {
        uint8_t *p = hdr + avih_pos + 8;
        uint32_t us_per_frame = *(uint32_t *)(p);
        uint32_t total_frames = *(uint32_t *)(p + 16);
        uint32_t width = *(uint32_t *)(p + 32);
        uint32_t height = *(uint32_t *)(p + 36);

        s_info.width = width ? width : 480;
        s_info.height = height ? height : 320;
        s_info.us_per_frame = us_per_frame ? us_per_frame : 33333;
        s_info.fps = 1000000 / s_info.us_per_frame;
        s_info.total_frames = total_frames;
        s_info.duration_sec = s_info.total_frames / s_info.fps;
        s_info.current_frame = 0;
        s_info.elapsed_sec = 0;
        s_info.is_open = true;
        s_info.is_eof = false;
    } else {
        s_info.width = 480;
        s_info.height = 320;
        s_info.fps = 30;
        s_info.us_per_frame = 33333;
        s_info.total_frames = 6000;
        s_info.duration_sec = 200;
        s_info.is_open = true;
        s_info.is_eof = false;
    }

    // Buscar inicio de lista movi
    int movi_pos = -1;
    for (size_t i = 0; i < r - 12; i++) {
        if (memcmp(hdr + i, "LIST", 4) == 0 && memcmp(hdr + i + 8, "movi", 4) == 0) {
            movi_pos = i + 12;
            break;
        }
    }

    if (movi_pos >= 0) {
        s_movi_start_offset = movi_pos;
    } else {
        s_movi_start_offset = 2048; // Offset estándar por defecto
    }

    // Cargar tabla de índices idx1 desde el final del archivo para O(1) Seek
    if (file_size > 1024 && s_info.total_frames > 0) {
        long scan_bytes = (file_size > 256 * 1024) ? 256 * 1024 : file_size;
        fseek(s_file, file_size - scan_bytes, SEEK_SET);
        uint8_t *tail = (uint8_t *)malloc(scan_bytes);
        if (tail) {
            fread(tail, 1, scan_bytes, s_file);
            for (long i = 0; i < scan_bytes - 16; i++) {
                if (memcmp(tail + i, "idx1", 4) == 0) {
                    uint32_t idx_size = *(uint32_t *)(tail + i + 4);
                    uint32_t num_entries = idx_size / 16;
                    if (num_entries > 0 && num_entries <= s_info.total_frames + 100) {
                        s_index_table = (uint32_t *)heap_caps_malloc(num_entries * sizeof(uint32_t), MALLOC_CAP_SPIRAM);
                        if (s_index_table) {
                            uint8_t *entry_ptr = tail + i + 8;
                            uint32_t valid_cnt = 0;
                            for (uint32_t e = 0; e < num_entries && (entry_ptr + 16 <= tail + scan_bytes); e++) {
                                if (memcmp(entry_ptr, "00dc", 4) == 0 || memcmp(entry_ptr, "00db", 4) == 0) {
                                    uint32_t off = *(uint32_t *)(entry_ptr + 8);
                                    s_index_table[valid_cnt++] = (s_movi_start_offset - 4) + off;
                                }
                                entry_ptr += 16;
                            }
                            ESP_LOGI(TAG, "Tabla idx1 cargada: %u cuadros indexados en PSRAM", (unsigned int)valid_cnt);
                        }
                    }
                    break;
                }
            }
            free(tail);
        }
    }

    fseek(s_file, s_movi_start_offset, SEEK_SET);

    ESP_LOGI(TAG, "AVI Abierto: %ux%u @ %u FPS, %u cuadros (%u:%02u)",
             (unsigned int)s_info.width, (unsigned int)s_info.height,
             (unsigned int)s_info.fps, (unsigned int)s_info.total_frames,
             (unsigned int)(s_info.duration_sec / 60), (unsigned int)(s_info.duration_sec % 60));

    return ESP_OK;
}

void avi_player_close(void) {
    if (s_file) {
        fclose(s_file);
        s_file = NULL;
    }
    if (s_index_table) {
        free(s_index_table);
        s_index_table = NULL;
    }
    s_info.is_open = false;
    s_info.is_eof = true;
}

esp_err_t avi_player_read_next_frame(uint16_t *out_rgb565, uint8_t scale) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    // Si tenemos tabla de índice y estamos dentro de rango, posicionar directamente
    if (s_index_table && s_info.current_frame < s_info.total_frames) {
        fseek(s_file, s_index_table[s_info.current_frame], SEEK_SET);
    }

    // Buscar siguiente chunk 00dc o 00db
    uint8_t chunk_hdr[8];
    while (1) {
        size_t r = fread(chunk_hdr, 1, 8, s_file);
        if (r < 8) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND; // EOF
        }

        uint32_t chunk_len = *(uint32_t *)(chunk_hdr + 4);

        if (memcmp(chunk_hdr, "00dc", 4) == 0 || memcmp(chunk_hdr, "00db", 4) == 0) {
            if (chunk_len > JPEG_INBUF_SIZE) {
                ESP_LOGE(TAG, "Cuadro JPEG demasiado grande: %u bytes", (unsigned int)chunk_len);
                fseek(s_file, chunk_len + (chunk_len & 1), SEEK_CUR);
                return ESP_ERR_NO_MEM;
            }

            size_t jr = fread(s_jpeg_buf, 1, chunk_len, s_file);
            if (chunk_len & 1) fseek(s_file, 1, SEEK_CUR); // Alinear word

            if (jr < chunk_len) {
                s_info.is_eof = true;
                return ESP_ERR_NOT_FOUND;
            }

            // Decodificación acelerada SIMD con esp_new_jpeg
            jpeg_dec_handle_t dec = (scale == 1) ? s_dec_studio : s_dec_full;
            if (!dec) dec = s_dec_full;

            jpeg_dec_io_t io = {
                .inbuf = s_jpeg_buf,
                .inbuf_len = (int)chunk_len,
                .outbuf = (uint8_t *)out_rgb565,
            };

            jpeg_dec_header_info_t hdr_info;
            jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr_info);
            if (jerr != JPEG_ERR_OK) {
                ESP_LOGW(TAG, "Fallo al parsear cabecera JPEG: %d", jerr);
                return ESP_FAIL;
            }

            jerr = jpeg_dec_process(dec, &io);
            if (jerr != JPEG_ERR_OK) {
                ESP_LOGW(TAG, "Fallo al decodificar JPEG SIMD: %d", jerr);
                return ESP_FAIL;
            }

            s_info.current_frame++;
            s_info.elapsed_sec = s_info.current_frame / s_info.fps;
            return ESP_OK;
        } else if (memcmp(chunk_hdr, "idx1", 4) == 0) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        } else {
            // Saltar chunk no relevante (JUNK, audio, etc.)
            fseek(s_file, chunk_len + (chunk_len & 1), SEEK_CUR);
        }
    }
}

void avi_player_seek_percent(int percent) {
    if (!s_file) return;

    if (percent < 0) percent = 0;
    if (percent > 99) percent = 99;

    uint32_t target_frame = (percent * s_info.total_frames) / 100;
    if (s_index_table && target_frame < s_info.total_frames) {
        fseek(s_file, s_index_table[target_frame], SEEK_SET);
        s_info.current_frame = target_frame;
        s_info.elapsed_sec = target_frame / s_info.fps;
    } else {
        // Búsqueda por aproximación de archivo
        fseek(s_file, 0, SEEK_END);
        long sz = ftell(s_file);
        long target_pos = s_movi_start_offset + (long)(((sz - s_movi_start_offset) * (int64_t)percent) / 100);
        fseek(s_file, target_pos, SEEK_SET);
        s_info.current_frame = target_frame;
        s_info.elapsed_sec = target_frame / s_info.fps;
    }
    ESP_LOGI(TAG, "Seek completado a %d%% (cuadro %u/%u)",
             percent, (unsigned int)s_info.current_frame, (unsigned int)s_info.total_frames);
}

void avi_player_restart(void) {
    if (s_file) {
        fseek(s_file, s_movi_start_offset, SEEK_SET);
        s_info.current_frame = 0;
        s_info.elapsed_sec = 0;
        s_info.is_eof = false;
    }
}

const avi_info_t *avi_player_get_info(void) {
    return &s_info;
}
