#include "avi_player.h"
#include "media_library.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <dirent.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "esp_memory_utils.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "esp_jpeg_dec.h"
#include "perf.h"
#include "lcd_bus.h"
#include "tear_diag.h"

static const char *TAG = "AVI_PLAYER_SIMD";

static FILE *s_file = NULL;
static char *s_file_vbuf = NULL;
static avi_info_t s_info;
static long s_movi_start_offset = 0;
static uint32_t *s_index_table = NULL;
static bool s_need_index_seek = true;

// Búfer para retener el último fotograma JPEG decodificado (re-blit en pausa)
static uint8_t *s_last_jpeg_chunk = NULL;
static size_t s_last_jpeg_len = 0;
static size_t s_last_jpeg_cap = 0;

#define JPEG_INBUF_INIT_SIZE (48 * 1024)
#define JPEG_INBUF_MAX_SIZE  (128 * 1024)

#define AVI_PREFETCH_SLOTS 3

typedef struct {
    uint8_t *buf;
    size_t capacity;
    size_t chunk_len;
    uint32_t frame_idx;
    esp_err_t err;
    bool is_eof;
} avi_slot_t;

static avi_slot_t s_slots[AVI_PREFETCH_SLOTS];
static QueueHandle_t s_q_free = NULL;
static QueueHandle_t s_q_ready = NULL;
static SemaphoreHandle_t s_file_mutex = NULL;
static TaskHandle_t s_reader_task_handle = NULL;
static volatile bool s_reader_run = false;
static uint32_t s_reader_frame_idx = 0;

static jpeg_dec_handle_t s_dec_full = NULL;
static jpeg_dec_handle_t s_dec_studio = NULL;
static jpeg_rotate_t s_current_std_rot = (jpeg_rotate_t)-1;

static esp_err_t ensure_studio_decoder(uint16_t src_w, uint16_t src_h) {
    bool is_rotated = (src_w == 320 && src_h == 480);
    uint16_t req_scale_w = is_rotated ? 160 : 240;
    uint16_t req_scale_h = is_rotated ? 240 : 160;
    jpeg_rotate_t req_rot = is_rotated ? JPEG_ROTATE_270D : JPEG_ROTATE_0D;

    if (s_dec_studio && s_current_std_rot == req_rot) {
        return ESP_OK;
    }

    if (s_dec_studio) {
        jpeg_dec_close(s_dec_studio);
        s_dec_studio = NULL;
    }

    jpeg_dec_config_t cfg_std = DEFAULT_JPEG_DEC_CONFIG();
    cfg_std.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;
    cfg_std.scale.width = req_scale_w;
    cfg_std.scale.height = req_scale_h;
    cfg_std.rotate = req_rot;
    cfg_std.block_enable = false;
    jpeg_error_t err = jpeg_dec_open(&cfg_std, &s_dec_studio);
    if (err != JPEG_ERR_OK) {
        ESP_LOGE(TAG, "Fallo al crear decoder Studio (scale=%ux%u, rot=%d): %d",
                 req_scale_w, req_scale_h, (int)req_rot, err);
        return ESP_FAIL;
    }
    s_current_std_rot = req_rot;
    ESP_LOGI(TAG, "Decoder Studio configurado: scale=%ux%u, rot=%d (salida 240x160)",
             req_scale_w, req_scale_h, (int)req_rot);
    return ESP_OK;
}

// Búferes DMA internos alineados a 16 B para decodificación por franjas (P2)
static uint16_t *s_strip_bufs[2] = {NULL, NULL};
static size_t s_strip_buf_len = 0;
static uint16_t *s_clip_strip_bufs[2] = {NULL, NULL};
static size_t s_clip_strip_buf_len = 0;

static void ensure_clip_strip_bufs(size_t required_bytes) {
    if (!s_clip_strip_bufs[0] || s_clip_strip_buf_len < required_bytes) {
        for (int i = 0; i < 2; i++) {
            if (s_clip_strip_bufs[i]) {
                free(s_clip_strip_bufs[i]);
                s_clip_strip_bufs[i] = NULL;
            }
            s_clip_strip_bufs[i] = (uint16_t *)heap_caps_aligned_alloc(
                16, required_bytes, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
            assert(s_clip_strip_bufs[i] != NULL);
        }
        s_clip_strip_buf_len = required_bytes;
    }
}

static void avi_reader_task(void *arg) {
    ESP_LOGI(TAG, "Tarea avi_reader_task iniciada en Core 0.");
    while (1) {
        while (!s_reader_run) {
            ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(100));
        }

        avi_slot_t *slot = NULL;
        if (xQueueReceive(s_q_free, &slot, pdMS_TO_TICKS(50)) != pdTRUE) {
            continue;
        }

        if (!s_reader_run) {
            xQueueSend(s_q_free, &slot, 0);
            continue;
        }

        xSemaphoreTake(s_file_mutex, portMAX_DELAY);

        if (!s_file || !s_info.is_open || s_info.is_eof) {
            xSemaphoreGive(s_file_mutex);
            xQueueSend(s_q_free, &slot, 0);
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }

        if (s_info.total_frames > 0 && s_reader_frame_idx >= s_info.total_frames) {
            slot->is_eof = true;
            slot->err = ESP_ERR_NOT_FOUND;
            s_info.is_eof = true;
            xSemaphoreGive(s_file_mutex);
            xQueueSend(s_q_ready, &slot, portMAX_DELAY);
            continue;
        }

        int fd = fileno(s_file);

        if (s_need_index_seek && s_index_table && s_reader_frame_idx < s_info.total_frames) {
            lseek(fd, s_index_table[s_reader_frame_idx], SEEK_SET);
            s_need_index_seek = false;
        }

        uint8_t chunk_hdr[8];
        bool got_frame = false;

        while (!got_frame && s_reader_run) {
            ssize_t r = read(fd, chunk_hdr, 8);
            if (r < 8) {
                if (r < 0) {
                    ESP_LOGE(TAG, "Error de E/S leyendo cabecera en reader task: %d", errno);
                    slot->err = ESP_ERR_INVALID_RESPONSE;
                } else {
                    slot->is_eof = true;
                    slot->err = ESP_ERR_NOT_FOUND;
                    s_info.is_eof = true;
                }
                got_frame = true;
                break;
            }

            uint32_t chunk_len = *(uint32_t *)(chunk_hdr + 4);

            if (memcmp(chunk_hdr, "00dc", 4) == 0 || memcmp(chunk_hdr, "00db", 4) == 0) {
                if (chunk_len > JPEG_INBUF_MAX_SIZE) {
                    ESP_LOGE(TAG, "Chunk JPEG excede 128 KB (%u B)", (unsigned int)chunk_len);
                    lseek(fd, chunk_len + (chunk_len & 1), SEEK_CUR);
                    perf_mark_oversize();
                    continue;
                }

                if (chunk_len > slot->capacity) {
                    size_t new_cap = (chunk_len + 4095) & ~4095;
                    if (new_cap > JPEG_INBUF_MAX_SIZE) new_cap = JPEG_INBUF_MAX_SIZE;
                    uint8_t *nb = (uint8_t *)heap_caps_realloc(slot->buf, new_cap, MALLOC_CAP_SPIRAM);
                    if (!nb) {
                        ESP_LOGE(TAG, "Fallo realloc buffer prefetch a %u B", (unsigned int)new_cap);
                        lseek(fd, chunk_len + (chunk_len & 1), SEEK_CUR);
                        perf_mark_oversize();
                        continue;
                    }
                    slot->buf = nb;
                    slot->capacity = new_cap;
                }

                int64_t t_real_rd_start = esp_timer_get_time();
                ssize_t jr = read(fd, slot->buf, chunk_len);
                if (chunk_len & 1) {
                    uint8_t pad;
                    read(fd, &pad, 1);
                }
                int64_t t_real_rd_end = esp_timer_get_time();
                perf_mark_reader_read((uint32_t)(t_real_rd_end - t_real_rd_start));

                if (jr < (ssize_t)chunk_len) {
                    if (jr < 0) {
                        ESP_LOGE(TAG, "Error de E/S leyendo JPEG en reader task: %d", errno);
                        slot->err = ESP_ERR_INVALID_RESPONSE;
                    } else {
                        slot->is_eof = true;
                        slot->err = ESP_ERR_NOT_FOUND;
                        s_info.is_eof = true;
                    }
                    got_frame = true;
                    break;
                }

                slot->chunk_len = chunk_len;
                slot->frame_idx = s_reader_frame_idx++;
                slot->err = ESP_OK;
                slot->is_eof = false;
                got_frame = true;
            } else if (memcmp(chunk_hdr, "idx1", 4) == 0) {
                slot->is_eof = true;
                slot->err = ESP_ERR_NOT_FOUND;
                s_info.is_eof = true;
                got_frame = true;
            } else {
                lseek(fd, chunk_len + (chunk_len & 1), SEEK_CUR);
            }
        }

        if (got_frame && s_reader_run) {
            xQueueSend(s_q_ready, &slot, portMAX_DELAY);
            perf_mark_slots_ready((uint32_t)uxQueueMessagesWaiting(s_q_ready));
        } else {
            xQueueSend(s_q_free, &slot, 0);
        }

        xSemaphoreGive(s_file_mutex);
    }
}

esp_err_t avi_player_init(void) {
    ESP_LOGI(TAG, "Inicializando motor de video SIMD (esp_new_jpeg) con prefetch task...");

    memset(&s_info, 0, sizeof(s_info));

    if (!s_file_mutex) {
        s_file_mutex = xSemaphoreCreateMutex();
        assert(s_file_mutex != NULL);
    }

    if (!s_q_free) {
        s_q_free = xQueueCreate(AVI_PREFETCH_SLOTS, sizeof(avi_slot_t *));
        s_q_ready = xQueueCreate(AVI_PREFETCH_SLOTS, sizeof(avi_slot_t *));
        assert(s_q_free != NULL && s_q_ready != NULL);

        for (int i = 0; i < AVI_PREFETCH_SLOTS; i++) {
            s_slots[i].capacity = JPEG_INBUF_INIT_SIZE;
            s_slots[i].buf = (uint8_t *)heap_caps_malloc(s_slots[i].capacity, MALLOC_CAP_SPIRAM);
            if (!s_slots[i].buf) {
                s_slots[i].buf = (uint8_t *)malloc(s_slots[i].capacity);
            }
            assert(s_slots[i].buf != NULL);
            s_slots[i].chunk_len = 0;
            s_slots[i].frame_idx = 0;
            s_slots[i].err = ESP_OK;
            s_slots[i].is_eof = false;

            avi_slot_t *p_slot = &s_slots[i];
            xQueueSend(s_q_free, &p_slot, 0);
        }
    }

    if (!s_reader_task_handle) {
        BaseType_t ret_t = xTaskCreatePinnedToCore(
            avi_reader_task,
            "avi_reader",
            4096,
            NULL,
            5,
            &s_reader_task_handle,
            0
        );
        if (ret_t != pdPASS) {
            ESP_LOGE(TAG, "Fallo al crear avi_reader_task en Core 0");
            return ESP_FAIL;
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

    // 2. Decoder para Studio 240x160 con hardware downsampling SIMD (D1: rotación según fichero)
    s_current_std_rot = (jpeg_rotate_t)-1;
    if (ensure_studio_decoder(480, 320) != ESP_OK) {
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Decodificadores SIMD Fullscreen y Studio inicializados con éxito.");
    return ESP_OK;
}

esp_err_t avi_player_open(const char *filepath) {
    avi_player_close();

    if (s_file_mutex) {
        xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    }

    ESP_LOGI(TAG, "Abriendo archivo AVI MJPEG: %s", filepath);
    s_file = fopen(filepath, "rb");
    if (!s_file) {
        ESP_LOGE(TAG, "No se pudo abrir el archivo %s", filepath);
        if (s_file_mutex) xSemaphoreGive(s_file_mutex);
        return ESP_FAIL;
    }

    fseek(s_file, 0, SEEK_END);
    long file_size = ftell(s_file);
    fseek(s_file, 0, SEEK_SET);

    size_t hdr_cap = 16384;
    uint8_t *hdr = (uint8_t *)malloc(hdr_cap);
    if (!hdr) {
        fclose(s_file);
        s_file = NULL;
        if (s_file_mutex) xSemaphoreGive(s_file_mutex);
        return ESP_ERR_NO_MEM;
    }

    size_t r = fread(hdr, 1, hdr_cap, s_file);
    if (r < 128 || memcmp(hdr, "RIFF", 4) != 0 || memcmp(hdr + 8, "AVI ", 4) != 0) {
        ESP_LOGE(TAG, "Encabezado RIFF AVI no válido");
        free(hdr);
        fclose(s_file);
        s_file = NULL;
        if (s_file_mutex) xSemaphoreGive(s_file_mutex);
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

    ensure_studio_decoder(s_info.width, s_info.height);

    int movi_pos = -1;
    int movi_chunk_start = -1;
    uint32_t movi_len = 0;
    for (size_t i = 0; i < r - 12; i++) {
        if (memcmp(hdr + i, "LIST", 4) == 0 && memcmp(hdr + i + 8, "movi", 4) == 0) {
            movi_chunk_start = (int)i;
            movi_len = *(uint32_t *)(hdr + i + 4);
            movi_pos = (int)i + 12;
            break;
        }
    }

    free(hdr);

    if (movi_pos >= 0) {
        s_movi_start_offset = movi_pos;
    } else {
        s_movi_start_offset = 2048;
    }

    // T5: Cargar tabla de índices idx1 en O(1) calculando la posición tras LIST movi
    if (file_size > 1024 && s_info.total_frames > 0) {
        bool idx_found = false;
        long idx1_file_pos = -1;
        uint32_t idx_size = 0;

        if (movi_chunk_start >= 0 && movi_len > 0) {
            long candidate_pos = movi_chunk_start + 8 + movi_len + (movi_len & 1);
            if (candidate_pos + 8 <= file_size) {
                fseek(s_file, candidate_pos, SEEK_SET);
                uint8_t c_hdr[8];
                if (fread(c_hdr, 1, 8, s_file) == 8 && memcmp(c_hdr, "idx1", 4) == 0) {
                    idx_size = *(uint32_t *)(c_hdr + 4);
                    idx1_file_pos = candidate_pos + 8;
                    idx_found = true;
                    ESP_LOGI(TAG, "idx1 hallado en O(1) tras LIST movi en offset %ld (tam: %u B)",
                             candidate_pos, (unsigned int)idx_size);
                }
            }
        }

        if (!idx_found) {
            long scan_bytes = (file_size > 64 * 1024) ? 64 * 1024 : file_size;
            fseek(s_file, file_size - scan_bytes, SEEK_SET);
            uint8_t *tail = (uint8_t *)malloc(scan_bytes);
            if (tail) {
                size_t tr = fread(tail, 1, scan_bytes, s_file);
                for (long i = 0; i + 8 <= (long)tr; i++) {
                    if (memcmp(tail + i, "idx1", 4) == 0) {
                        idx_size = *(uint32_t *)(tail + i + 4);
                        idx1_file_pos = (file_size - scan_bytes) + i + 8;
                        idx_found = true;
                        ESP_LOGI(TAG, "idx1 hallado por fallback en cola en offset %ld (tam: %u B)",
                                 idx1_file_pos - 8, (unsigned int)idx_size);
                        break;
                    }
                }
                free(tail);
            }
        }

        if (idx_found && idx_size > 0 && idx1_file_pos >= 0) {
            uint32_t num_entries = idx_size / 16;
            if (num_entries > 0 && num_entries <= s_info.total_frames + 500) {
                s_index_table = (uint32_t *)heap_caps_malloc(num_entries * sizeof(uint32_t), MALLOC_CAP_SPIRAM);
                if (s_index_table) {
                    fseek(s_file, idx1_file_pos, SEEK_SET);
                    uint32_t valid_cnt = 0;
                    uint8_t ent_buf[4096];
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
        }
    }

    lseek(fileno(s_file), s_movi_start_offset, SEEK_SET);
    s_need_index_seek = false;
    s_info.current_frame = 0;
    s_reader_frame_idx = 0;
    s_info.is_eof = false;
    s_reader_run = true;

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }

    if (s_reader_task_handle) {
        xTaskNotifyGive(s_reader_task_handle);
    }

    // Preroll: precargar hasta 2 cuadros
    for (int w = 0; w < 40; w++) {
        if (uxQueueMessagesWaiting(s_q_ready) >= 2 || s_info.is_eof) break;
        vTaskDelay(pdMS_TO_TICKS(5));
    }

    ESP_LOGI(TAG, "AVI Abierto: %ux%u @ %u FPS, %u cuadros (%u:%02u), preroll listo (%d frames)",
             (unsigned int)s_info.width, (unsigned int)s_info.height,
             (unsigned int)s_info.fps, (unsigned int)s_info.total_frames,
             (unsigned int)(s_info.duration_sec / 60), (unsigned int)(s_info.duration_sec % 60),
             (int)uxQueueMessagesWaiting(s_q_ready));

    return ESP_OK;
}

void avi_player_close(void) {
    s_reader_run = false;
    if (s_file_mutex) {
        xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    }

    if (s_q_ready && s_q_free) {
        avi_slot_t *s;
        while (xQueueReceive(s_q_ready, &s, 0) == pdTRUE) {
            s->chunk_len = 0;
            s->frame_idx = 0;
            s->err = ESP_OK;
            s->is_eof = false;
            xQueueSend(s_q_free, &s, 0);
        }
    }

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
    if (s_last_jpeg_chunk) {
        free(s_last_jpeg_chunk);
        s_last_jpeg_chunk = NULL;
        s_last_jpeg_cap = 0;
        s_last_jpeg_len = 0;
    }
    s_info.is_open = false;
    s_info.is_eof = true;
    s_need_index_seek = true;

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }
}

esp_err_t avi_player_read_next_frame(uint16_t *out_rgb565, uint8_t scale) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    int64_t t_rd_start = esp_timer_get_time();
    avi_slot_t *slot = NULL;
    if (xQueueReceive(s_q_ready, &slot, pdMS_TO_TICKS(150)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    int64_t t_rd_end = esp_timer_get_time();
    perf_mark_q_wait((uint32_t)(t_rd_end - t_rd_start));

    if (slot->err != ESP_OK) {
        esp_err_t err = slot->err;
        xQueueSend(s_q_free, &slot, 0);
        return err;
    }

    jpeg_dec_handle_t dec = (scale == 1) ? s_dec_studio : s_dec_full;
    if (!dec) dec = s_dec_full;

    jpeg_dec_io_t io = {
        .inbuf = slot->buf,
        .inbuf_len = (int)slot->chunk_len,
        .outbuf = (uint8_t *)out_rgb565,
    };

    int64_t t_dec_start = esp_timer_get_time();
    jpeg_dec_header_info_t hdr_info;
    jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr_info);
    if (jerr != JPEG_ERR_OK) {
        ESP_LOGW(TAG, "Fallo al parsear cabecera JPEG: %d", jerr);
        xQueueSend(s_q_free, &slot, 0);
        return ESP_FAIL;
    }

    jerr = jpeg_dec_process(dec, &io);
    int64_t t_dec_end = esp_timer_get_time();
    uint32_t dec_us = (uint32_t)(t_dec_end - t_dec_start);
    perf_mark_decode(dec_us);
    perf_mark_frame_decode(dec_us);

    s_info.current_frame = slot->frame_idx + 1;
    s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;

    xQueueSend(s_q_free, &slot, 0);

    if (jerr != JPEG_ERR_OK) {
        ESP_LOGW(TAG, "Fallo al decodificar JPEG SIMD: %d", jerr);
        return ESP_FAIL;
    }

    return ESP_OK;
}

esp_err_t avi_player_read_and_blit_direct(void) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    int64_t t_rd_start = esp_timer_get_time();
    avi_slot_t *slot = NULL;
    if (xQueueReceive(s_q_ready, &slot, pdMS_TO_TICKS(150)) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    int64_t t_rd_end = esp_timer_get_time();
    perf_mark_q_wait((uint32_t)(t_rd_end - t_rd_start));

    if (slot->err != ESP_OK) {
        esp_err_t err = slot->err;
        xQueueSend(s_q_free, &slot, 0);
        return err;
    }

    if (slot->chunk_len > 0) {
        if (slot->chunk_len > s_last_jpeg_cap) {
            if (s_last_jpeg_chunk) free(s_last_jpeg_chunk);
            s_last_jpeg_chunk = (uint8_t *)heap_caps_malloc(slot->chunk_len + 4096, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
            s_last_jpeg_cap = s_last_jpeg_chunk ? (slot->chunk_len + 4096) : 0;
        }
        if (s_last_jpeg_chunk) {
            memcpy(s_last_jpeg_chunk, slot->buf, slot->chunk_len);
            s_last_jpeg_len = slot->chunk_len;
        }
    }

    jpeg_dec_handle_t dec = s_dec_full;
    if (!dec) {
        xQueueSend(s_q_free, &slot, 0);
        return ESP_FAIL;
    }

    jpeg_dec_io_t io = {
        .inbuf = slot->buf,
        .inbuf_len = (int)slot->chunk_len,
    };

    jpeg_dec_header_info_t hdr_info;
    jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr_info);
    if (jerr != JPEG_ERR_OK) {
        ESP_LOGW(TAG, "Fallo al parsear cabecera JPEG en direct: %d", jerr);
        xQueueSend(s_q_free, &slot, 0);
        return ESP_FAIL;
    }

    int outbuf_len = 0;
    jpeg_dec_get_outbuf_len(dec, &outbuf_len);
    int process_count = 0;
    jpeg_dec_get_process_count(dec, &process_count);
    if (process_count <= 0 || outbuf_len <= 0) {
        ESP_LOGW(TAG, "process_count=%d outbuf_len=%d invalido", process_count, outbuf_len);
        xQueueSend(s_q_free, &slot, 0);
        return ESP_FAIL;
    }

    // Asegurar que los búferes DMA internos de franja estén asignados
    if (!s_strip_bufs[0] || s_strip_buf_len < (size_t)outbuf_len) {
        for (int i = 0; i < 2; i++) {
            if (s_strip_bufs[i]) free(s_strip_bufs[i]);
            s_strip_bufs[i] = (uint16_t *)heap_caps_aligned_alloc(16, outbuf_len, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
            if (!s_strip_bufs[i]) {
                ESP_LOGE(TAG, "Fallo al reservar strip_buf[%d] (%d bytes DMA)", i, outbuf_len);
                xQueueSend(s_q_free, &slot, 0);
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
    uint32_t total_frame_dec_us = 0;
    uint32_t windows_count = 0;

    int x_start = 0;
    int x_end = 319;
    int clip_w = 320;
    if (hdr_info.width == 320 && hdr_info.height == 480) {
        if (vh < 320) {
            x_start = 319 - (vy + vh - 1);
            x_end = 319 - vy;
            if (x_start < 0) x_start = 0;
            if (x_end > 319) x_end = 319;
            clip_w = x_end - x_start + 1;
        }
    }

    lcd_overlay_rect_t active_overlays[LCD_OVERLAY_MAX_RECTS];
    int num_overlays = lcd_bus_get_active_overlays(active_overlays);
    const uint16_t *overlay_buf = (num_overlays > 0) ? lcd_bus_get_overlay_buffer() : NULL;

    lcd_bus_lock();

    tear_diag_mode_t diag = tear_diag_get_mode();

    // Programar la ventana de visualización UNA ÚNICA VEZ por fotograma
    if (vw > 0 && vh > 0) {
        if (diag == TEAR_DIAG_MODE_B) {
            // Modo B de diagnóstico: franja única fija (líneas 80..95)
            lcd_bus_set_frame_window(0, 80, 319, 95);
            windows_count++;
        } else if (hdr_info.width == 320 && hdr_info.height == 480) {
            if (clip_w > 0) {
                // Video rotado: ventana completa (0..319, 0..479) o recortada en X (x_start..x_end, 0..479)
                lcd_bus_set_frame_window((uint16_t)x_start, 0, (uint16_t)x_end, 479);
                windows_count++;
            }
        } else {
            // Video clásico 480x320 en panel nativo 320x480
            uint16_t x1_win = (uint16_t)x_start;
            uint16_t x2_win = (uint16_t)x_end;
            uint16_t y2_win = (hdr_info.height > 0 && hdr_info.height <= 480) ? (hdr_info.height - 1) : 319;
            lcd_bus_set_frame_window(x1_win, 0, x2_win, y2_win);
            windows_count++;
        }
    }

    for (int b = 0; b < process_count; b++) {
        io.outbuf = (uint8_t *)s_strip_bufs[b & 1];

        int64_t t_dec_start = esp_timer_get_time();
        jerr = jpeg_dec_process(dec, &io);
        int64_t t_dec_end = esp_timer_get_time();
        uint32_t s_dec_us = (uint32_t)(t_dec_end - t_dec_start);
        perf_mark_decode(s_dec_us);
        total_frame_dec_us += s_dec_us;

        if (jerr != JPEG_ERR_OK) {
            ESP_LOGW(TAG, "Fallo en jpeg_dec_process bloque %d/%d: %d", b, process_count, jerr);
            if (dma_in_flight) {
                lcd_bus_wait_strip_done(NULL);
            }
            lcd_bus_unlock();
            xQueueSend(s_q_free, &slot, 0);
            return ESP_FAIL;
        }

        int cur_lines = (hdr_info.width > 0) ? (io.out_size / (hdr_info.width * 2)) : 0;
        line_y += cur_lines;

        // Composición de capas opacas sobre el búfer nativo de la franja (Sección 0 F6b)
        // Se ejecuta en CPU de forma concurrente mientras el DMA de la franja anterior sigue en vuelo
        if (num_overlays > 0 && overlay_buf != NULL && cur_lines > 0) {
            int strip_y_start = line_y - cur_lines;
            for (int r = 0; r < cur_lines; r++) {
                int phys_y = strip_y_start + r;
                for (int ov = 0; ov < num_overlays; ov++) {
                    if (phys_y >= active_overlays[ov].nat_y_min && phys_y <= active_overlays[ov].nat_y_max) {
                        int x_min = active_overlays[ov].nat_x_min;
                        int x_max = active_overlays[ov].nat_x_max;
                        if (x_min < 0) x_min = 0;
                        if (x_max > 319) x_max = 319;
                        if (x_max >= x_min) {
                            uint16_t *dst = s_strip_bufs[b & 1] + r * 320 + x_min;
                            const uint16_t *src = overlay_buf + phys_y * 320 + x_min;
                            memcpy(dst, src, (x_max - x_min + 1) * sizeof(uint16_t));
                        }
                    }
                }
            }
        }

        // Si habia un DMA previo en vuelo, esperar a que termine antes de lanzar el siguiente
        if (dma_in_flight) {
            lcd_bus_wait_strip_done(&strip_dma_us);
            dma_in_flight = false;
            total_frame_blit_us += strip_dma_us;
            perf_mark_strip(strip_dma_us);
        }

        // Diagnostico de tearing (T2)
        bool skip_strip = false;
        if (diag == TEAR_DIAG_MODE_A && b >= (process_count / 2)) {
            // Modo A: solo mitad superior (10 franjas = 160 lineas, ~10.1 ms)
            skip_strip = true;
        } else if (diag == TEAR_DIAG_MODE_B && b != 5) {
            // Modo B: franja unica fija (franja 5 = lineas 80..95, ~1.0 ms)
            skip_strip = true;
        }

        // Enviar franja dentro de la ventana fijada previamente
        if (!skip_strip && vw > 0 && vh > 0) {
            if (hdr_info.width == 320 && hdr_info.height == 480) {
                // Video rotado 320x480 en panel nativo (MADCTL sin MV)
                if (vh >= 320) {
                    // Fullscreen completo sin HUD (hidden / seek): transferir franja completa (320 px)
                    size_t strip_bytes = (size_t)cur_lines * 320 * sizeof(uint16_t);
                    bool is_first = (strips_sent_count == 0);
                    lcd_bus_draw_strip_continue_async(s_strip_bufs[b & 1], strip_bytes, is_first);
                    dma_in_flight = true;
                    strips_sent_count++;
                } else {
                    // Fullscreen con OSD: recortar columnas a lo largo del alto lógico vh
                    if (clip_w > 0) {
                        ensure_clip_strip_bufs(320 * 16 * sizeof(uint16_t));
                        uint16_t *dst_strip = s_clip_strip_bufs[b & 1];
                        const uint16_t *src_strip = s_strip_bufs[b & 1];
                        for (int r = 0; r < cur_lines; r++) {
                            memcpy(dst_strip + r * clip_w, src_strip + r * 320 + x_start, clip_w * sizeof(uint16_t));
                        }

                        size_t clip_bytes = (size_t)cur_lines * clip_w * sizeof(uint16_t);
                        bool is_first = (strips_sent_count == 0);
                        lcd_bus_draw_strip_continue_async(dst_strip, clip_bytes, is_first);
                        dma_in_flight = true;
                        strips_sent_count++;
                    }
                }
            } else {
                // Video clasico 480x320 ("sin girar"): transferir clip_w columnas nativas
                int clip_cols = clip_w;
                if (clip_cols > 320) clip_cols = 320;
                if (clip_cols > 0 && cur_lines > 0) {
                    ensure_clip_strip_bufs(320 * 16 * sizeof(uint16_t));
                    uint16_t *dst_strip = s_clip_strip_bufs[b & 1];
                    const uint16_t *src_strip = s_strip_bufs[b & 1];
                    for (int r = 0; r < cur_lines; r++) {
                        memcpy(dst_strip + r * clip_cols, src_strip + r * hdr_info.width + x_start, clip_cols * sizeof(uint16_t));
                    }
                    size_t clip_bytes = (size_t)cur_lines * clip_cols * sizeof(uint16_t);
                    bool is_first = (strips_sent_count == 0);
                    lcd_bus_draw_strip_continue_async(dst_strip, clip_bytes, is_first);
                    dma_in_flight = true;
                    strips_sent_count++;
                }
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

    s_info.current_frame = slot->frame_idx + 1;
    s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;

    xQueueSend(s_q_free, &slot, 0);

    perf_mark_frame_decode(total_frame_dec_us);
    perf_mark_direct_frame(strips_sent_count, total_frame_blit_us, windows_count);
    perf_mark_presented();

    return ESP_OK;
}

esp_err_t avi_player_reblit_current_frame(void) {
    if (!s_last_jpeg_chunk || s_last_jpeg_len == 0) {
        return ESP_ERR_INVALID_STATE;
    }
    jpeg_dec_handle_t dec = s_dec_full;
    if (!dec) return ESP_FAIL;

    jpeg_dec_io_t io = {
        .inbuf = s_last_jpeg_chunk,
        .inbuf_len = (int)s_last_jpeg_len,
    };

    jpeg_dec_header_info_t hdr_info;
    jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr_info);
    if (jerr != JPEG_ERR_OK) return ESP_FAIL;

    int outbuf_len = 0;
    jpeg_dec_get_outbuf_len(dec, &outbuf_len);
    int process_count = 0;
    jpeg_dec_get_process_count(dec, &process_count);
    if (process_count <= 0 || outbuf_len <= 0) return ESP_FAIL;

    if (!s_strip_bufs[0] || s_strip_buf_len < (size_t)outbuf_len) return ESP_ERR_INVALID_STATE;

    int16_t vx, vy, vw, vh;
    lcd_bus_get_video_rect(&vx, &vy, &vw, &vh);
    if (vw <= 0 || vh <= 0) return ESP_OK;

    int line_y = 0;
    bool dma_in_flight = false;
    int x_start = 0;
    int x_end = 319;
    int clip_w = 320;
    if (hdr_info.width == 320 && hdr_info.height == 480) {
        if (vh < 320) {
            x_start = 319 - (vy + vh - 1);
            x_end = 319 - vy;
            if (x_start < 0) x_start = 0;
            if (x_end > 319) x_end = 319;
            clip_w = x_end - x_start + 1;
        }
    }

    lcd_overlay_rect_t active_overlays[LCD_OVERLAY_MAX_RECTS];
    int num_overlays = lcd_bus_get_active_overlays(active_overlays);
    const uint16_t *overlay_buf = (num_overlays > 0) ? lcd_bus_get_overlay_buffer() : NULL;

    lcd_bus_lock();

    if (hdr_info.width == 320 && hdr_info.height == 480) {
        if (clip_w > 0) {
            lcd_bus_set_frame_window((uint16_t)x_start, 0, (uint16_t)x_end, 479);
        }
    } else {
        uint16_t x1_win = (uint16_t)x_start;
        uint16_t x2_win = (uint16_t)x_end;
        uint16_t y2_win = (hdr_info.height > 0 && hdr_info.height <= 480) ? (hdr_info.height - 1) : 319;
        lcd_bus_set_frame_window(x1_win, 0, x2_win, y2_win);
    }

    uint32_t strips_sent_count = 0;
    for (int b = 0; b < process_count; b++) {
        io.outbuf = (uint8_t *)s_strip_bufs[b & 1];
        jerr = jpeg_dec_process(dec, &io);
        if (jerr != JPEG_ERR_OK) {
            if (dma_in_flight) lcd_bus_wait_strip_done(NULL);
            lcd_bus_unlock();
            return ESP_FAIL;
        }

        int cur_lines = (hdr_info.width > 0) ? (io.out_size / (hdr_info.width * 2)) : 0;
        line_y += cur_lines;

        if (num_overlays > 0 && overlay_buf != NULL && cur_lines > 0) {
            int strip_y_start = line_y - cur_lines;
            for (int r = 0; r < cur_lines; r++) {
                int phys_y = strip_y_start + r;
                for (int ov = 0; ov < num_overlays; ov++) {
                    if (phys_y >= active_overlays[ov].nat_y_min && phys_y <= active_overlays[ov].nat_y_max) {
                        int x_min = active_overlays[ov].nat_x_min;
                        int x_max = active_overlays[ov].nat_x_max;
                        if (x_min < 0) x_min = 0;
                        if (x_max > 319) x_max = 319;
                        if (x_max >= x_min) {
                            uint16_t *dst = s_strip_bufs[b & 1] + r * 320 + x_min;
                            const uint16_t *src = overlay_buf + phys_y * 320 + x_min;
                            memcpy(dst, src, (x_max - x_min + 1) * sizeof(uint16_t));
                        }
                    }
                }
            }
        }

        if (dma_in_flight) {
            lcd_bus_wait_strip_done(NULL);
            dma_in_flight = false;
        }

        if (hdr_info.width == 320 && hdr_info.height == 480) {
            if (vh >= 320) {
                size_t strip_bytes = (size_t)cur_lines * 320 * sizeof(uint16_t);
                bool is_first = (strips_sent_count == 0);
                lcd_bus_draw_strip_continue_async(s_strip_bufs[b & 1], strip_bytes, is_first);
                dma_in_flight = true;
                strips_sent_count++;
            } else if (clip_w > 0) {
                ensure_clip_strip_bufs(320 * 16 * sizeof(uint16_t));
                uint16_t *dst_strip = s_clip_strip_bufs[b & 1];
                const uint16_t *src_strip = s_strip_bufs[b & 1];
                for (int r = 0; r < cur_lines; r++) {
                    memcpy(dst_strip + r * clip_w, src_strip + r * 320 + x_start, clip_w * sizeof(uint16_t));
                }
                size_t clip_bytes = (size_t)cur_lines * clip_w * sizeof(uint16_t);
                bool is_first = (strips_sent_count == 0);
                lcd_bus_draw_strip_continue_async(dst_strip, clip_bytes, is_first);
                dma_in_flight = true;
                strips_sent_count++;
            }
        }
    }

    if (dma_in_flight) {
        lcd_bus_wait_strip_done(NULL);
    }
    lcd_bus_unlock();
    return ESP_OK;
}

esp_err_t avi_player_skip_next_frame(void) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    avi_slot_t *slot = NULL;
    if (xQueueReceive(s_q_ready, &slot, 0) == pdTRUE) {
        if (slot->err != ESP_OK) {
            esp_err_t err = slot->err;
            xQueueSend(s_q_free, &slot, 0);
            return err;
        }
        s_info.current_frame = slot->frame_idx + 1;
        s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
        xQueueSend(s_q_free, &slot, 0);
        return ESP_OK;
    }

    xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    if (!s_file || !s_info.is_open || s_info.is_eof) {
        xSemaphoreGive(s_file_mutex);
        return ESP_ERR_NOT_FOUND;
    }

    int fd = fileno(s_file);
    uint8_t chunk_hdr[8];
    while (1) {
        ssize_t r = read(fd, chunk_hdr, 8);
        if (r < 8) {
            s_info.is_eof = true;
            xSemaphoreGive(s_file_mutex);
            return ESP_ERR_NOT_FOUND;
        }

        uint32_t chunk_len = *(uint32_t *)(chunk_hdr + 4);

        if (memcmp(chunk_hdr, "00dc", 4) == 0 || memcmp(chunk_hdr, "00db", 4) == 0) {
            lseek(fd, chunk_len + (chunk_len & 1), SEEK_CUR);
            s_info.current_frame = s_reader_frame_idx + 1;
            s_reader_frame_idx++;
            s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
            xSemaphoreGive(s_file_mutex);
            return ESP_OK;
        } else if (memcmp(chunk_hdr, "idx1", 4) == 0) {
            s_info.is_eof = true;
            xSemaphoreGive(s_file_mutex);
            return ESP_ERR_NOT_FOUND;
        } else {
            lseek(fd, chunk_len + (chunk_len & 1), SEEK_CUR);
        }
    }
}

void avi_player_seek_frame(uint32_t target_frame) {
    if (!s_file) return;

    if (s_info.total_frames > 0 && target_frame >= s_info.total_frames) {
        target_frame = s_info.total_frames - 1;
    }

    s_reader_run = false;
    if (s_file_mutex) {
        xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    }

    if (s_q_ready && s_q_free) {
        avi_slot_t *s;
        while (xQueueReceive(s_q_ready, &s, 0) == pdTRUE) {
            s->chunk_len = 0;
            s->frame_idx = 0;
            s->err = ESP_OK;
            s->is_eof = false;
            xQueueSend(s_q_free, &s, 0);
        }
    }

    int fd = fileno(s_file);
    if (s_index_table && target_frame < s_info.total_frames) {
        lseek(fd, s_index_table[target_frame], SEEK_SET);
        s_info.current_frame = target_frame;
        s_reader_frame_idx = target_frame;
        s_info.elapsed_sec = (s_info.fps > 0) ? (target_frame / s_info.fps) : 0;
        s_need_index_seek = false;
    } else {
        off_t sz = lseek(fd, 0, SEEK_END);
        off_t target_pos = s_movi_start_offset;
        if (s_info.total_frames > 0) {
            target_pos += (off_t)(((sz - s_movi_start_offset) * (int64_t)target_frame) / s_info.total_frames);
        }
        lseek(fd, target_pos, SEEK_SET);
        s_info.current_frame = target_frame;
        s_reader_frame_idx = target_frame;
        s_info.elapsed_sec = (s_info.fps > 0) ? (target_frame / s_info.fps) : 0;
        s_need_index_seek = false;
    }

    s_info.is_eof = false;
    s_reader_run = true;

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }

    if (s_reader_task_handle) {
        xTaskNotifyGive(s_reader_task_handle);
    }

    for (int w = 0; w < 30; w++) {
        if (uxQueueMessagesWaiting(s_q_ready) >= 1 || s_info.is_eof) break;
        vTaskDelay(pdMS_TO_TICKS(5));
    }

    ESP_LOGI(TAG, "Seek completado a cuadro %u/%u",
             (unsigned int)s_info.current_frame, (unsigned int)s_info.total_frames);
}

void avi_player_seek_ms(uint32_t ms) {
    if (s_info.us_per_frame > 0) {
        uint32_t target_frame = (uint32_t)(((uint64_t)ms * 1000ULL) / s_info.us_per_frame);
        avi_player_seek_frame(target_frame);
    } else {
        avi_player_seek_percent(0);
    }
}

void avi_player_seek_percent(int percent) {
    if (percent < 0) percent = 0;
    if (percent > 99) percent = 99;
    uint32_t target_frame = (percent * s_info.total_frames) / 100;
    avi_player_seek_frame(target_frame);
}

void avi_player_restart(void) {
    if (!s_file) return;

    s_reader_run = false;
    if (s_file_mutex) {
        xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    }

    if (s_q_ready && s_q_free) {
        avi_slot_t *s;
        while (xQueueReceive(s_q_ready, &s, 0) == pdTRUE) {
            s->chunk_len = 0;
            s->frame_idx = 0;
            s->err = ESP_OK;
            s->is_eof = false;
            xQueueSend(s_q_free, &s, 0);
        }
    }

    lseek(fileno(s_file), s_movi_start_offset, SEEK_SET);
    s_info.current_frame = 0;
    s_reader_frame_idx = 0;
    s_info.elapsed_sec = 0;
    s_info.is_eof = false;
    s_need_index_seek = false;
    s_reader_run = true;

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }

    if (s_reader_task_handle) {
        xTaskNotifyGive(s_reader_task_handle);
    }

    for (int w = 0; w < 30; w++) {
        if (uxQueueMessagesWaiting(s_q_ready) >= 1 || s_info.is_eof) break;
        vTaskDelay(pdMS_TO_TICKS(5));
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

    size_t hdr_cap = 16384;
    uint8_t *hdr = (uint8_t *)malloc(hdr_cap);
    if (!hdr) {
        fclose(f);
        return;
    }
    size_t r = fread(hdr, 1, hdr_cap, f);
    if (r < 128 || memcmp(hdr, "RIFF", 4) != 0 || memcmp(hdr + 8, "AVI ", 4) != 0) {
        ESP_LOGE(TAG, "Cabecera AVI no valida en %s", filepath);
        free(hdr);
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
    long movi_chunk_start = -1;
    uint32_t movi_len = 0;
    for (size_t i = 0; i + 12 <= r; i++) {
        if (memcmp(hdr + i, "LIST", 4) == 0 && memcmp(hdr + i + 8, "movi", 4) == 0) {
            movi_chunk_start = (long)i;
            movi_len = *(uint32_t *)(hdr + i + 4);
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
        long idx1_file_pos = -1;
        uint32_t idx_size = 0;

        if (movi_chunk_start >= 0 && movi_len > 0) {
            long cand = movi_chunk_start + 8 + movi_len + (movi_len & 1);
            if (cand + 8 <= file_size) {
                fseek(f, cand, SEEK_SET);
                uint8_t chk[8];
                if (fread(chk, 1, 8, f) == 8 && memcmp(chk, "idx1", 4) == 0) {
                    idx1_file_pos = cand;
                    idx_size = *(uint32_t *)(chk + 4);
                    has_idx1 = 1;
                }
            }
        }

        if (!has_idx1) {
            long scan_bytes = (file_size > 64 * 1024) ? 64 * 1024 : file_size;
            fseek(f, file_size - scan_bytes, SEEK_SET);
            uint8_t *tail = (uint8_t *)malloc(scan_bytes);
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

    free(hdr);
    fclose(f);

    printf("MEDIA,file=%s,size=%ld,w=%u,h=%u,us_per_frame=%u,fps_milli=%llu,frames=%u,idx1=%d,chunk_avg=%u,chunk_max=%u,subsampling=%s\n",
           filepath, file_size, (unsigned int)w, (unsigned int)h,
           (unsigned int)us_per_frame, (unsigned long long)fps_milli,
           (unsigned int)frames, has_idx1,
           (unsigned int)chunk_avg, (unsigned int)chunk_max,
           subsampling);
    fflush(stdout);
}

int media_scan_sdcard(void) {
    media_library_scan();
    return media_library_count();
}

int media_get_avi_count(void) {
    return media_library_count();
}

const char *media_get_avi_path(int index) {
    const media_item_t *item = media_library_get(index);
    return item ? item->path : NULL;
}
