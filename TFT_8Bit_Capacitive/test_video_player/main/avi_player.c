#include "avi_player.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <dirent.h>
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "esp_jpeg_dec.h"
#include "perf.h"
#include "lcd_bus.h"

static const char *TAG = "AVI_PLAYER_SIMD";

static FILE *s_file = NULL;
static char *s_file_vbuf = NULL;
static avi_info_t s_info;
static long s_movi_start_offset = 0;
static uint32_t *s_index_table = NULL;
static bool s_need_index_seek = true;

#define JPEG_INBUF_SIZE (36 * 1024)
static uint8_t *s_jpeg_buf = NULL;

static jpeg_dec_handle_t s_dec_full = NULL;
static jpeg_dec_handle_t s_dec_studio = NULL;

// Búferes DMA internos alineados a 16 B para decodificación por franjas (P2)
static uint16_t *s_strip_bufs[2] = {NULL, NULL};
static size_t s_strip_buf_len = 0;

static char **s_scanned_avi_files = NULL;
static int s_scanned_avi_count = 0;

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
        cfg_full.block_enable = true;
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

    if (!s_file_vbuf) {
        s_file_vbuf = (char *)heap_caps_malloc(32 * 1024, MALLOC_CAP_SPIRAM);
    }
    if (s_file_vbuf) {
        setvbuf(s_file, s_file_vbuf, _IOFBF, 32 * 1024);
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
            avih_pos = (int)i;
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
        s_info.duration_sec = (s_info.fps > 0) ? (s_info.total_frames / s_info.fps) : 0;
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
            movi_pos = (int)i + 12;
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
        long scan_bytes = (file_size > 512 * 1024) ? 512 * 1024 : file_size;
        fseek(s_file, file_size - scan_bytes, SEEK_SET);
        uint8_t *tail = (uint8_t *)malloc(scan_bytes);
        if (tail) {
            size_t tr = fread(tail, 1, scan_bytes, s_file);
            for (long i = 0; i + 8 <= (long)tr; i++) {
                if (memcmp(tail + i, "idx1", 4) == 0) {
                    uint32_t idx_size = *(uint32_t *)(tail + i + 4);
                    uint32_t num_entries = idx_size / 16;
                    long idx_file_pos = (file_size - scan_bytes) + i + 8;
                    if (num_entries > 0 && num_entries <= s_info.total_frames + 500) {
                        s_index_table = (uint32_t *)heap_caps_malloc(num_entries * sizeof(uint32_t), MALLOC_CAP_SPIRAM);
                        if (s_index_table) {
                            fseek(s_file, idx_file_pos, SEEK_SET);
                            uint32_t valid_cnt = 0;
                            uint8_t ent_buf[2048];
                            uint32_t bytes_left = idx_size;
                            while (bytes_left >= 16 && valid_cnt < num_entries) {
                                size_t to_read = (bytes_left > sizeof(ent_buf)) ? sizeof(ent_buf) : bytes_left;
                                to_read = (to_read / 16) * 16;
                                size_t nr = fread(ent_buf, 1, to_read, s_file);
                                if (nr < 16) break;
                                for (size_t k = 0; k + 16 <= nr && valid_cnt < num_entries; k += 16) {
                                    if (memcmp(ent_buf + k, "00dc", 4) == 0 || memcmp(ent_buf + k, "00db", 4) == 0) {
                                        uint32_t off = *(uint32_t *)(ent_buf + k + 8);
                                        s_index_table[valid_cnt++] = (s_movi_start_offset - 4) + off;
                                    }
                                }
                                bytes_left -= (uint32_t)nr;
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
    s_need_index_seek = false;

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
    if (s_file_vbuf) {
        free(s_file_vbuf);
        s_file_vbuf = NULL;
    }
    if (s_index_table) {
        free(s_index_table);
        s_index_table = NULL;
    }
    s_info.is_open = false;
    s_info.is_eof = true;
    s_need_index_seek = true;
}

esp_err_t avi_player_read_next_frame(uint16_t *out_rgb565, uint8_t scale) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    // Si hubo un seek previo, posicionar en la tabla de índice
    if (s_need_index_seek && s_index_table && s_info.current_frame < s_info.total_frames) {
        fseek(s_file, s_index_table[s_info.current_frame], SEEK_SET);
        s_need_index_seek = false;
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
                perf_mark_oversize();
                return ESP_ERR_NO_MEM;
            }

            int64_t t_rd_start = esp_timer_get_time();
            size_t jr = fread(s_jpeg_buf, 1, chunk_len, s_file);
            if (chunk_len & 1) fseek(s_file, 1, SEEK_CUR); // Alinear word
            int64_t t_rd_end = esp_timer_get_time();
            perf_mark_read((uint32_t)(t_rd_end - t_rd_start));

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

            int64_t t_dec_start = esp_timer_get_time();
            jpeg_dec_header_info_t hdr_info;
            jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr_info);
            if (jerr != JPEG_ERR_OK) {
                ESP_LOGW(TAG, "Fallo al parsear cabecera JPEG: %d", jerr);
                return ESP_FAIL;
            }

            jerr = jpeg_dec_process(dec, &io);
            int64_t t_dec_end = esp_timer_get_time();
            perf_mark_decode((uint32_t)(t_dec_end - t_dec_start));

            if (jerr != JPEG_ERR_OK) {
                ESP_LOGW(TAG, "Fallo al decodificar JPEG SIMD: %d", jerr);
                return ESP_FAIL;
            }

            s_info.current_frame++;
            s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
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

esp_err_t avi_player_read_and_blit_direct(void) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    if (s_need_index_seek && s_index_table && s_info.current_frame < s_info.total_frames) {
        fseek(s_file, s_index_table[s_info.current_frame], SEEK_SET);
        s_need_index_seek = false;
    }

    uint8_t chunk_hdr[8];
    while (1) {
        size_t r = fread(chunk_hdr, 1, 8, s_file);
        if (r < 8) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        }

        uint32_t chunk_len = *(uint32_t *)(chunk_hdr + 4);

        if (memcmp(chunk_hdr, "00dc", 4) == 0 || memcmp(chunk_hdr, "00db", 4) == 0) {
            if (chunk_len > JPEG_INBUF_SIZE) {
                ESP_LOGE(TAG, "Cuadro JPEG demasiado grande: %u bytes", (unsigned int)chunk_len);
                fseek(s_file, chunk_len + (chunk_len & 1), SEEK_CUR);
                perf_mark_oversize();
                return ESP_ERR_NO_MEM;
            }

            int64_t t_rd_start = esp_timer_get_time();
            size_t jr = fread(s_jpeg_buf, 1, chunk_len, s_file);
            if (chunk_len & 1) fseek(s_file, 1, SEEK_CUR);
            int64_t t_rd_end = esp_timer_get_time();
            perf_mark_read((uint32_t)(t_rd_end - t_rd_start));

            if (jr < chunk_len) {
                s_info.is_eof = true;
                return ESP_ERR_NOT_FOUND;
            }

            jpeg_dec_handle_t dec = s_dec_full;
            if (!dec) return ESP_FAIL;

            jpeg_dec_io_t io = {
                .inbuf = s_jpeg_buf,
                .inbuf_len = (int)chunk_len,
            };

            jpeg_dec_header_info_t hdr_info;
            jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr_info);
            if (jerr != JPEG_ERR_OK) {
                ESP_LOGW(TAG, "Fallo al parsear cabecera JPEG en direct: %d", jerr);
                return ESP_FAIL;
            }

            int outbuf_len = 0;
            jpeg_dec_get_outbuf_len(dec, &outbuf_len);
            int process_count = 0;
            jpeg_dec_get_process_count(dec, &process_count);
            if (process_count <= 0 || outbuf_len <= 0) {
                ESP_LOGW(TAG, "process_count=%d outbuf_len=%d invalido", process_count, outbuf_len);
                return ESP_FAIL;
            }

            // Asegurar que los búferes DMA internos de franja estén asignados
            if (!s_strip_bufs[0] || s_strip_buf_len < (size_t)outbuf_len) {
                for (int i = 0; i < 2; i++) {
                    if (s_strip_bufs[i]) free(s_strip_bufs[i]);
                    s_strip_bufs[i] = (uint16_t *)heap_caps_aligned_alloc(16, outbuf_len, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
                    if (!s_strip_bufs[i]) {
                        ESP_LOGE(TAG, "Fallo al reservar strip_buf[%d] (%d bytes DMA)", i, outbuf_len);
                        return ESP_ERR_NO_MEM;
                    }
                }
                s_strip_buf_len = (size_t)outbuf_len;
            }

            int16_t vx, vy, vw, vh;
            lcd_bus_get_video_rect(&vx, &vy, &vw, &vh);

            int line_y = 0;
            bool dma_in_flight = false;
            uint32_t strip_dma_us = 0;
            uint32_t total_frame_blit_us = 0;
            uint32_t strips_sent_count = 0;

            lcd_bus_lock();

            for (int b = 0; b < process_count; b++) {
                io.outbuf = (uint8_t *)s_strip_bufs[b & 1];

                int64_t t_dec_start = esp_timer_get_time();
                jerr = jpeg_dec_process(dec, &io);
                int64_t t_dec_end = esp_timer_get_time();
                perf_mark_decode((uint32_t)(t_dec_end - t_dec_start));

                if (jerr != JPEG_ERR_OK) {
                    ESP_LOGW(TAG, "Fallo en jpeg_dec_process bloque %d/%d: %d", b, process_count, jerr);
                    if (dma_in_flight) {
                        lcd_bus_wait_strip_done(NULL);
                    }
                    lcd_bus_unlock();
                    return ESP_FAIL;
                }

                // Si habia un DMA previo en vuelo, esperar a que termine antes de lanzar el siguiente
                if (dma_in_flight) {
                    lcd_bus_wait_strip_done(&strip_dma_us);
                    dma_in_flight = false;
                    total_frame_blit_us += strip_dma_us;
                    perf_mark_strip(strip_dma_us);
                }

                int cur_lines = (hdr_info.width > 0) ? (io.out_size / (hdr_info.width * 2)) : 0;
                int cur_y1 = line_y;
                int cur_y2 = line_y + cur_lines - 1;
                line_y += cur_lines;

                // Verificar recorte contra video_rect
                if (vw > 0 && vh > 0) {
                    int clip_y1 = (cur_y1 > vy) ? cur_y1 : vy;
                    int clip_y2 = (cur_y2 < (vy + vh - 1)) ? cur_y2 : (vy + vh - 1);

                    if (clip_y1 <= clip_y2) {
                        size_t offset_bytes = (size_t)(clip_y1 - cur_y1) * (hdr_info.width * 2);
                        size_t visible_bytes = (size_t)(clip_y2 - clip_y1 + 1) * (hdr_info.width * 2);
                        const uint16_t *strip_px = (const uint16_t *)((uint8_t *)s_strip_bufs[b & 1] + offset_bytes);

                        lcd_bus_draw_strip_async(0, (uint16_t)clip_y1, hdr_info.width - 1, (uint16_t)clip_y2, strip_px, visible_bytes);
                        dma_in_flight = true;
                        strips_sent_count++;
                    }
                }
            }

            // Esperar al ultimo DMA si quedo en vuelo
            if (dma_in_flight) {
                lcd_bus_wait_strip_done(&strip_dma_us);
                dma_in_flight = false;
                total_frame_blit_us += strip_dma_us;
                perf_mark_strip(strip_dma_us);
            }
            lcd_bus_unlock();

            // Registro de frame presentado y metricas direct
            perf_mark_direct_frame(strips_sent_count, total_frame_blit_us);
            perf_mark_presented();

            s_info.current_frame++;
            s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
            return ESP_OK;
        } else if (memcmp(chunk_hdr, "idx1", 4) == 0) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        } else {
            fseek(s_file, chunk_len + (chunk_len & 1), SEEK_CUR);
        }
    }
}

esp_err_t avi_player_skip_next_frame(void) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    if (s_info.total_frames > 0 && s_info.current_frame >= s_info.total_frames) {
        s_info.is_eof = true;
        return ESP_ERR_NOT_FOUND;
    }

    // Si hubo un seek previo, posicionar en la tabla de índice
    if (s_need_index_seek && s_index_table && s_info.current_frame < s_info.total_frames) {
        fseek(s_file, s_index_table[s_info.current_frame], SEEK_SET);
        s_need_index_seek = false;
    }

    uint8_t chunk_hdr[8];
    while (1) {
        size_t r = fread(chunk_hdr, 1, 8, s_file);
        if (r < 8) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        }

        uint32_t chunk_len = *(uint32_t *)(chunk_hdr + 4);

        if (memcmp(chunk_hdr, "00dc", 4) == 0 || memcmp(chunk_hdr, "00db", 4) == 0) {
            // Saltar chunk de video sin decodificar
            fseek(s_file, chunk_len + (chunk_len & 1), SEEK_CUR);
            s_info.current_frame++;
            s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
            return ESP_OK;
        } else if (memcmp(chunk_hdr, "idx1", 4) == 0) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        } else {
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
        s_info.elapsed_sec = (s_info.fps > 0) ? (target_frame / s_info.fps) : 0;
        s_need_index_seek = false;
    } else {
        // Búsqueda por aproximación de archivo
        fseek(s_file, 0, SEEK_END);
        long sz = ftell(s_file);
        long target_pos = s_movi_start_offset + (long)(((sz - s_movi_start_offset) * (int64_t)percent) / 100);
        fseek(s_file, target_pos, SEEK_SET);
        s_info.current_frame = target_frame;
        s_info.elapsed_sec = (s_info.fps > 0) ? (target_frame / s_info.fps) : 0;
        s_need_index_seek = false;
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
        s_need_index_seek = false;
    }
}

const avi_info_t *avi_player_get_info(void) {
    return &s_info;
}

void avi_player_log_media(const char *filepath) {
    if (!filepath) return;
    FILE *f = fopen(filepath, "rb");
    if (!f) {
        ESP_LOGE(TAG, "No se pudo abrir %s para MEDIA", filepath);
        return;
    }

    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    uint8_t hdr[4096];
    size_t r = fread(hdr, 1, sizeof(hdr), f);
    if (r < 128 || memcmp(hdr, "RIFF", 4) != 0 || memcmp(hdr + 8, "AVI ", 4) != 0) {
        ESP_LOGE(TAG, "Cabecera AVI no valida en %s", filepath);
        fclose(f);
        return;
    }

    uint32_t w = 480;
    uint32_t h = 320;
    uint32_t us_per_frame = 33333;
    uint32_t frames = 0;

    int avih_pos = -1;
    for (size_t i = 0; i + 48 <= r; i++) {
        if (memcmp(hdr + i, "avih", 4) == 0) {
            avih_pos = (int)i;
            break;
        }
    }

    if (avih_pos >= 0) {
        uint8_t *p = hdr + avih_pos + 8;
        us_per_frame = *(uint32_t *)(p);
        frames = *(uint32_t *)(p + 16);
        w = *(uint32_t *)(p + 32);
        h = *(uint32_t *)(p + 36);
    }
    if (us_per_frame == 0) us_per_frame = 33333;
    if (w == 0) w = 480;
    if (h == 0) h = 320;

    uint64_t fps_milli = (us_per_frame > 0) ? (1000000000ULL / (uint64_t)us_per_frame) : 0;

    // Subsampling: buscar el primer chunk de video (00dc o 00db) DESPUES de LIST movi
    const char *subsampling = "unknown";
    long movi_pos = -1;
    for (size_t i = 0; i + 12 <= r; i++) {
        if (memcmp(hdr + i, "LIST", 4) == 0 && memcmp(hdr + i + 8, "movi", 4) == 0) {
            movi_pos = (long)i + 12;
            break;
        }
    }
    if (movi_pos < 0) {
        movi_pos = 2048;
    }

    fseek(f, movi_pos, SEEK_SET);
    uint8_t chunk_search_buf[4096];
    long vchunk_data_pos = -1;
    uint32_t vchunk_data_len = 0;

    long cur_pos = movi_pos;
    while (cur_pos < file_size && cur_pos < movi_pos + 256 * 1024) {
        fseek(f, cur_pos, SEEK_SET);
        size_t nr = fread(chunk_search_buf, 1, sizeof(chunk_search_buf), f);
        if (nr < 8) break;
        bool found = false;
        for (size_t i = 0; i + 8 <= nr; i++) {
            if (memcmp(chunk_search_buf + i, "00dc", 4) == 0 || memcmp(chunk_search_buf + i, "00db", 4) == 0) {
                vchunk_data_len = *(uint32_t *)(chunk_search_buf + i + 4);
                vchunk_data_pos = cur_pos + (long)i + 8;
                found = true;
                break;
            }
        }
        if (found) break;
        if (nr <= 8) break;
        cur_pos += (long)(nr - 8);
    }

    if (vchunk_data_pos > 0 && vchunk_data_len > 0) {
        fseek(f, vchunk_data_pos, SEEK_SET);
        uint32_t read_len = (vchunk_data_len > 4096) ? 4096 : vchunk_data_len;
        uint8_t *jbuf = (uint8_t *)malloc(read_len);
        if (jbuf) {
            size_t jread = fread(jbuf, 1, read_len, f);
            if (jread >= 4 && jbuf[0] == 0xFF && jbuf[1] == 0xD8) {
                size_t p = 2;
                while (p + 4 < jread) {
                    if (jbuf[p] != 0xFF) {
                        p++;
                        continue;
                    }
                    while (p < jread && jbuf[p] == 0xFF) p++;
                    if (p >= jread) break;
                    uint8_t marker = jbuf[p++];
                    if (marker == 0xD9 || marker == 0xDA) break;
                    if (p + 2 > jread) break;
                    uint16_t seg_len = ((uint16_t)jbuf[p] << 8) | jbuf[p + 1];
                    if (marker == 0xC0 || marker == 0xC2) {
                        if (p + 8 <= jread) {
                            uint8_t num_components = jbuf[p + 7];
                            if (num_components >= 1 && p + 10 <= jread) {
                                uint8_t sample_byte = jbuf[p + 9];
                                uint8_t h_sample = (sample_byte >> 4) & 0x0F;
                                uint8_t v_sample = sample_byte & 0x0F;
                                if (h_sample == 2 && v_sample == 2) {
                                    subsampling = "420";
                                } else if (h_sample == 2 && v_sample == 1) {
                                    subsampling = "422";
                                } else if (h_sample == 1 && v_sample == 1) {
                                    subsampling = "444";
                                } else if (h_sample == 4 && v_sample == 1) {
                                    subsampling = "411";
                                }
                            }
                        }
                        break;
                    }
                    p += seg_len;
                }
            }
            free(jbuf);
        }
    }

    // chunk_avg/max: recorrer TODAS las entradas 00dc/00db de idx1
    int has_idx1 = 0;
    uint32_t chunk_avg = 0;
    uint32_t chunk_max = 0;

    if (file_size > 1024) {
        long scan_bytes = (file_size > 512 * 1024) ? 512 * 1024 : file_size;
        fseek(f, file_size - scan_bytes, SEEK_SET);
        uint8_t *tail = (uint8_t *)malloc(scan_bytes);
        long idx1_file_pos = -1;
        uint32_t idx_size = 0;

        if (tail) {
            size_t tr = fread(tail, 1, scan_bytes, f);
            for (long i = 0; i + 8 <= (long)tr; i++) {
                if (memcmp(tail + i, "idx1", 4) == 0) {
                    idx1_file_pos = (file_size - scan_bytes) + i;
                    idx_size = *(uint32_t *)(tail + i + 4);
                    has_idx1 = 1;
                    break;
                }
            }
            free(tail);
        }

        if (has_idx1 && idx_size > 0 && idx1_file_pos >= 0) {
            fseek(f, idx1_file_pos + 8, SEEK_SET);
            uint32_t bytes_left = idx_size;
            uint64_t total_chunk_bytes = 0;
            uint32_t count_chunks = 0;
            uint8_t ent_buf[2048]; // 128 entradas de 16 bytes
            while (bytes_left >= 16) {
                size_t to_read = (bytes_left > sizeof(ent_buf)) ? sizeof(ent_buf) : bytes_left;
                to_read = (to_read / 16) * 16;
                size_t nr = fread(ent_buf, 1, to_read, f);
                if (nr < 16) break;
                for (size_t k = 0; k + 16 <= nr; k += 16) {
                    if (memcmp(ent_buf + k, "00dc", 4) == 0 || memcmp(ent_buf + k, "00db", 4) == 0) {
                        uint32_t clen = *(uint32_t *)(ent_buf + k + 12);
                        total_chunk_bytes += clen;
                        count_chunks++;
                        if (clen > chunk_max) {
                            chunk_max = clen;
                        }
                    }
                }
                bytes_left -= (uint32_t)nr;
            }
            if (count_chunks > 0) {
                chunk_avg = (uint32_t)(total_chunk_bytes / count_chunks);
            }
        }
    }

    fclose(f);

    printf("MEDIA,file=%s,size=%ld,w=%u,h=%u,us_per_frame=%u,fps_milli=%llu,frames=%u,idx1=%d,chunk_avg=%u,chunk_max=%u,subsampling=%s\n",
           filepath, file_size, (unsigned int)w, (unsigned int)h,
           (unsigned int)us_per_frame, (unsigned long long)fps_milli,
           (unsigned int)frames, has_idx1,
           (unsigned int)chunk_avg, (unsigned int)chunk_max,
           subsampling);
    fflush(stdout);
}

static bool is_avi_filename(const char *name) {
    if (!name) return false;
    size_t len = strlen(name);
    if (len < 4) return false;
    return (strcasecmp(name + len - 4, ".avi") == 0);
}

int media_scan_sdcard(void) {
    DIR *dir = opendir("/sdcard");
    if (!dir) {
        ESP_LOGE(TAG, "No se pudo abrir /sdcard para escanear");
        return 0;
    }

    if (s_scanned_avi_files) {
        for (int i = 0; i < s_scanned_avi_count; i++) {
            free(s_scanned_avi_files[i]);
        }
        free(s_scanned_avi_files);
        s_scanned_avi_files = NULL;
    }
    s_scanned_avi_count = 0;
    int cap = 0;

    struct dirent *de;
    while ((de = readdir(dir)) != NULL) {
        if (de->d_name[0] == '.') continue;
        if (is_avi_filename(de->d_name)) {
            char path[256];
            snprintf(path, sizeof(path), "/sdcard/%s", de->d_name);
            if (s_scanned_avi_count >= cap) {
                cap = (cap == 0) ? 8 : cap * 2;
                s_scanned_avi_files = (char **)realloc(s_scanned_avi_files, cap * sizeof(char *));
            }
            s_scanned_avi_files[s_scanned_avi_count++] = strdup(path);
        }
    }
    closedir(dir);

    // Ordenar alfabeticamente para orden determinista
    for (int i = 0; i < s_scanned_avi_count - 1; i++) {
        for (int j = i + 1; j < s_scanned_avi_count; j++) {
            if (strcmp(s_scanned_avi_files[i], s_scanned_avi_files[j]) > 0) {
                char *tmp = s_scanned_avi_files[i];
                s_scanned_avi_files[i] = s_scanned_avi_files[j];
                s_scanned_avi_files[j] = tmp;
            }
        }
    }

    ESP_LOGI(TAG, "MicroSD escaneada: %d archivos AVI encontrados.", s_scanned_avi_count);

    for (int i = 0; i < s_scanned_avi_count; i++) {
        avi_player_log_media(s_scanned_avi_files[i]);
    }

    return s_scanned_avi_count;
}

int media_get_avi_count(void) {
    return s_scanned_avi_count;
}

const char *media_get_avi_path(int index) {
    if (index >= 0 && index < s_scanned_avi_count) {
        return s_scanned_avi_files[index];
    }
    return NULL;
}
