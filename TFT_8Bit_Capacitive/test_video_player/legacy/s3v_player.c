#include "s3v_player.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "lz4.h"

static const char *TAG = "S3V_PLAYER";

static FILE *s_file = NULL;
static s3v_header_t s_header;
static s3v_info_t s_info;
static uint32_t *s_index_table = NULL;

// Búfer canónico en PSRAM para retener el estado de cuadro persistente (480x320 RGB565)
static uint16_t *s_canonical_frame = NULL;

// Búferes de trabajo en PSRAM para descompresión LZ4
static uint8_t *s_compressed_buf = NULL;
static uint16_t *s_block_decomp_buf = NULL;

#define FRAME_PIXELS (480 * 320)
#define FRAME_RAW_BYTES (FRAME_PIXELS * 2) // 307200
#define COMPRESSED_BUF_SIZE (320 * 1024)   // 320 KB en PSRAM

esp_err_t s3v_player_init(void) {
    ESP_LOGI(TAG, "Inicializando motor de video S3V v1...");

    memset(&s_info, 0, sizeof(s_info));

    if (!s_canonical_frame) {
        s_canonical_frame = (uint16_t *)heap_caps_aligned_alloc(64, FRAME_RAW_BYTES, MALLOC_CAP_SPIRAM);
        if (!s_canonical_frame) {
            ESP_LOGE(TAG, "Fallo al reservar s_canonical_frame (307 KB en PSRAM)");
            return ESP_ERR_NO_MEM;
        }
        memset(s_canonical_frame, 0, FRAME_RAW_BYTES);
    }

    if (!s_compressed_buf) {
        s_compressed_buf = (uint8_t *)heap_caps_aligned_alloc(64, COMPRESSED_BUF_SIZE, MALLOC_CAP_SPIRAM);
        if (!s_compressed_buf) {
            ESP_LOGE(TAG, "Fallo al reservar s_compressed_buf (320 KB en PSRAM)");
            return ESP_ERR_NO_MEM;
        }
    }

    if (!s_block_decomp_buf) {
        s_block_decomp_buf = (uint16_t *)heap_caps_aligned_alloc(64, FRAME_RAW_BYTES, MALLOC_CAP_SPIRAM);
        if (!s_block_decomp_buf) {
            ESP_LOGE(TAG, "Fallo al reservar s_block_decomp_buf (307 KB en PSRAM)");
            return ESP_ERR_NO_MEM;
        }
    }

    ESP_LOGI(TAG, "Motor S3V inicializado con exito en PSRAM.");
    return ESP_OK;
}

esp_err_t s3v_player_open(const char *filepath) {
    s3v_player_close();

    ESP_LOGI(TAG, "Abriendo archivo S3V: %s", filepath);
    s_file = fopen(filepath, "rb");
    if (!s_file) {
        ESP_LOGE(TAG, "No se pudo abrir el archivo S3V: %s", filepath);
        return ESP_ERR_NOT_FOUND;
    }

    // Leer cabecera (32 bytes)
    size_t r = fread(&s_header, 1, sizeof(s3v_header_t), s_file);
    if (r < sizeof(s3v_header_t)) {
        ESP_LOGE(TAG, "Archivo demasiado corto para cabecera S3V");
        fclose(s_file);
        s_file = NULL;
        return ESP_ERR_INVALID_SIZE;
    }

    if (memcmp(s_header.magic, S3V_MAGIC_STR, 4) != 0) {
        ESP_LOGE(TAG, "Firma magica S3V no coincide: %.4s", s_header.magic);
        fclose(s_file);
        s_file = NULL;
        return ESP_ERR_INVALID_VERSION;
    }

    s_info.width = s_header.width;
    s_info.height = s_header.height;
    s_info.fps = s_header.fps ? s_header.fps : 30;
    s_info.us_per_frame = 1000000 / s_info.fps;
    s_info.total_frames = s_header.total_frames;
    s_info.duration_sec = s_header.duration_sec;
    s_info.current_frame = 0;
    s_info.elapsed_sec = 0;
    s_info.is_open = true;
    s_info.is_eof = false;

    // Cargar tabla de índices para O(1) Seek si existe
    if (s_header.index_offset > 0 && s_header.total_frames > 0) {
        size_t table_bytes = s_header.total_frames * sizeof(uint32_t);
        s_index_table = (uint32_t *)heap_caps_malloc(table_bytes, MALLOC_CAP_SPIRAM);
        if (s_index_table) {
            long cur_pos = ftell(s_file);
            fseek(s_file, s_header.index_offset, SEEK_SET);
            fread(s_index_table, sizeof(uint32_t), s_header.total_frames, s_file);
            fseek(s_file, cur_pos, SEEK_SET);
            ESP_LOGI(TAG, "Tabla de indices O(1) cargada (%u cuadros, %u KB)",
                     (unsigned int)s_header.total_frames, (unsigned int)(table_bytes / 1024));
        }
    }

    ESP_LOGI(TAG, "S3V Abierto: %ux%u @ %u FPS, Total: %u cuadros (%u:%02u)",
             (unsigned int)s_info.width, (unsigned int)s_info.height,
             (unsigned int)s_info.fps, (unsigned int)s_info.total_frames,
             (unsigned int)(s_info.duration_sec / 60), (unsigned int)(s_info.duration_sec % 60));

    // Limpiar canvas canónico para evitar artefactos del video previo
    if (s_canonical_frame) {
        memset(s_canonical_frame, 0, FRAME_RAW_BYTES);
    }

    return ESP_OK;
}

void s3v_player_close(void) {
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

esp_err_t s3v_player_read_next_frame(uint16_t *out_rgb565, uint8_t scale) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    s3v_frame_header_t fhdr;
    size_t r = fread(&fhdr, 1, sizeof(s3v_frame_header_t), s_file);
    if (r < sizeof(s3v_frame_header_t)) {
        s_info.is_eof = true;
        return ESP_ERR_NOT_FOUND; // EOF
    }

    if (fhdr.frame_type == 1) {
        // I-FRAME (Cuadro completo comprimido LZ4)
        if (fhdr.payload_len > COMPRESSED_BUF_SIZE) {
            ESP_LOGE(TAG, "Payload I-Frame excede buffer: %u bytes", (unsigned int)fhdr.payload_len);
            return ESP_ERR_NO_MEM;
        }

        size_t pr = fread(s_compressed_buf, 1, fhdr.payload_len, s_file);
        if (pr < fhdr.payload_len) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        }

        int decomp_bytes = LZ4_decompress_safe((const char *)s_compressed_buf,
                                               (char *)s_canonical_frame,
                                               (int)fhdr.payload_len,
                                               FRAME_RAW_BYTES);
        if (decomp_bytes < 0) {
            ESP_LOGE(TAG, "Error de descompresion LZ4 en I-Frame");
            return ESP_FAIL;
        }

    } else if (fhdr.frame_type == 2) {
        // P-FRAME (Bloques delta 16x16)
        uint8_t mask[S3V_MASK_BYTES];
        size_t mr = fread(mask, 1, S3V_MASK_BYTES, s_file);
        if (mr < S3V_MASK_BYTES) {
            s_info.is_eof = true;
            return ESP_ERR_NOT_FOUND;
        }

        if (fhdr.changed_blocks > 0 && fhdr.payload_len > 0) {
            if (fhdr.payload_len > COMPRESSED_BUF_SIZE) {
                ESP_LOGE(TAG, "Payload P-Frame excede buffer: %u bytes", (unsigned int)fhdr.payload_len);
                return ESP_ERR_NO_MEM;
            }

            size_t pr = fread(s_compressed_buf, 1, fhdr.payload_len, s_file);
            if (pr < fhdr.payload_len) {
                s_info.is_eof = true;
                return ESP_ERR_NOT_FOUND;
            }

            int expected_bytes = fhdr.changed_blocks * (S3V_BLOCK_SIZE * S3V_BLOCK_SIZE * 2);
            int decomp_bytes = LZ4_decompress_safe((const char *)s_compressed_buf,
                                                   (char *)s_block_decomp_buf,
                                                   (int)fhdr.payload_len,
                                                   expected_bytes);
            if (decomp_bytes < 0) {
                ESP_LOGE(TAG, "Error de descompresion LZ4 en P-Frame");
                return ESP_FAIL;
            }

            // Blit ultra-rapido de macrobloques modificados
            const uint16_t *src_blk = s_block_decomp_buf;
            int blk_idx = 0;
            for (int by = 0; by < S3V_BLOCK_ROWS; by++) {
                for (int bx = 0; bx < S3V_BLOCK_COLS; bx++) {
                    if (mask[blk_idx >> 3] & (1 << (blk_idx & 7))) {
                        int start_x = bx * S3V_BLOCK_SIZE;
                        int start_y = by * S3V_BLOCK_SIZE;
                        for (int row = 0; row < S3V_BLOCK_SIZE; row++) {
                            memcpy(&s_canonical_frame[(start_y + row) * 480 + start_x],
                                   &src_blk[row * S3V_BLOCK_SIZE],
                                   S3V_BLOCK_SIZE * sizeof(uint16_t));
                        }
                        src_blk += (S3V_BLOCK_SIZE * S3V_BLOCK_SIZE);
                    }
                    blk_idx++;
                }
            }
        }
    } else {
        ESP_LOGE(TAG, "Tipo de cuadro desconocido: %u", fhdr.frame_type);
        return ESP_FAIL;
    }

    s_info.current_frame++;
    s_info.elapsed_sec = s_info.current_frame / s_info.fps;

    // Renderizado al búfer de destino
    if (out_rgb565) {
        if (scale == 0) {
            // Fullscreen 480x320: copia directa
            memcpy(out_rgb565, s_canonical_frame, FRAME_RAW_BYTES);
        } else {
            // Studio 240x160: submuestreo 2:1
            for (int y = 0; y < 160; y++) {
                const uint16_t *src_line = &s_canonical_frame[(y * 2) * 480];
                uint16_t *dst_line = &out_rgb565[y * 240];
                for (int x = 0; x < 240; x++) {
                    dst_line[x] = src_line[x * 2];
                }
            }
        }
    }

    return ESP_OK;
}

void s3v_player_seek_percent(int percent) {
    if (!s_file || !s_index_table || s_info.total_frames == 0) {
        return;
    }

    if (percent < 0) percent = 0;
    if (percent > 99) percent = 99;

    uint32_t target_frame = (percent * s_info.total_frames) / 100;
    // Buscar el I-frame anterior más cercano (intervalo 60)
    uint32_t iframe_idx = (target_frame / 60) * 60;
    if (iframe_idx >= s_info.total_frames) {
        iframe_idx = (s_info.total_frames > 0) ? (s_info.total_frames - 1) : 0;
    }

    fseek(s_file, s_index_table[iframe_idx], SEEK_SET);
    s_info.current_frame = iframe_idx;

    // Replay frames hasta target_frame sin blit a pantalla
    while (s_info.current_frame <= target_frame) {
        if (s3v_player_read_next_frame(NULL, 0) != ESP_OK) {
            break;
        }
    }

    ESP_LOGI(TAG, "Seek completado a %d%% (cuadro %u/%u)",
             percent, (unsigned int)s_info.current_frame, (unsigned int)s_info.total_frames);
}

void s3v_player_restart(void) {
    if (s_file && s_index_table) {
        fseek(s_file, s_index_table[0], SEEK_SET);
        s_info.current_frame = 0;
        s_info.elapsed_sec = 0;
        s_info.is_eof = false;
    }
}

const s3v_info_t *s3v_player_get_info(void) {
    return &s_info;
}
