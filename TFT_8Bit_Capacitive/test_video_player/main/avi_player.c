#include "avi_player.h"
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

#define FULL_SCREEN_W 320
#define FULL_SCREEN_H 480
#define FULL_FRAME_BYTES (FULL_SCREEN_W * FULL_SCREEN_H * sizeof(uint16_t)) // 307200 B

#define NUM_FULL_FRAME_BUFS 3
static uint16_t *s_full_frame_bufs[NUM_FULL_FRAME_BUFS] = {NULL, NULL, NULL};
static uint16_t *s_clipped_buf = NULL;
static volatile int s_buf_head = 0;
static volatile int s_buf_tail = 0;
static volatile int s_buf_count = 0;
static volatile uint32_t s_frame_idx_ring[NUM_FULL_FRAME_BUFS] = {0};
static volatile bool s_prerolled = false;
static TaskHandle_t s_decoder_task_handle = NULL;
static SemaphoreHandle_t s_ring_free_sem = NULL;
static SemaphoreHandle_t s_ring_ready_sem = NULL;
static portMUX_TYPE s_ring_mux = portMUX_INITIALIZER_UNLOCKED;
static volatile bool s_direct_pipeline_enabled = false;
static esp_err_t avi_player_preroll_first_frame(void);

static char **s_scanned_avi_files = NULL;
static int s_scanned_avi_count = 0;

static void avi_decoder_task(void *arg);

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

static void avi_decoder_task(void *arg) {
    ESP_LOGI(TAG, "Tarea avi_decoder_task iniciada en Core 1.");
    while (1) {
        while (!s_direct_pipeline_enabled || !s_reader_run || !s_info.is_open) {
            ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(50));
        }

        // Esperar búfer libre en el anillo de cuadro completo
        if (xSemaphoreTake(s_ring_free_sem, pdMS_TO_TICKS(50)) != pdTRUE) {
            continue;
        }

        if (!s_direct_pipeline_enabled || !s_reader_run || !s_info.is_open) {
            xSemaphoreGive(s_ring_free_sem);
            continue;
        }

        // Obtener slot con JPEG comprimido desde reader task
        avi_slot_t *slot = NULL;
        int64_t t_rd_start = esp_timer_get_time();
        if (xQueueReceive(s_q_ready, &slot, pdMS_TO_TICKS(100)) != pdTRUE) {
            xSemaphoreGive(s_ring_free_sem);
            continue;
        }
        perf_mark_q_wait((uint32_t)(esp_timer_get_time() - t_rd_start));

        if (slot->err != ESP_OK || slot->is_eof) {
            if (slot->is_eof) s_info.is_eof = true;
            xQueueSend(s_q_free, &slot, 0);
            xSemaphoreGive(s_ring_free_sem);
            continue;
        }

        jpeg_dec_handle_t dec = s_dec_full;
        if (!dec) {
            xQueueSend(s_q_free, &slot, 0);
            xSemaphoreGive(s_ring_free_sem);
            continue;
        }

        jpeg_dec_io_t io = {
            .inbuf = slot->buf,
            .inbuf_len = (int)slot->chunk_len,
            .outbuf = (uint8_t *)s_full_frame_bufs[s_buf_tail],
        };
        jpeg_dec_header_info_t hdr;
        jpeg_error_t jerr = jpeg_dec_parse_header(dec, &io, &hdr);
        if (jerr == JPEG_ERR_OK) {
            int64_t t_d0 = esp_timer_get_time();
            jerr = jpeg_dec_process(dec, &io);
            uint32_t dec_us0 = (uint32_t)(esp_timer_get_time() - t_d0);
            perf_mark_decode(dec_us0);
            perf_mark_frame_decode(dec_us0);

            if (jerr == JPEG_ERR_OK) {
                s_frame_idx_ring[s_buf_tail] = slot->frame_idx;
                s_buf_tail = (s_buf_tail + 1) % NUM_FULL_FRAME_BUFS;
                portENTER_CRITICAL(&s_ring_mux);
                s_buf_count++;
                portEXIT_CRITICAL(&s_ring_mux);
                xSemaphoreGive(s_ring_ready_sem);
            } else {
                xSemaphoreGive(s_ring_free_sem);
            }
        } else {
            xSemaphoreGive(s_ring_free_sem);
        }

        xQueueSend(s_q_free, &slot, 0);
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

void avi_player_set_direct_pipeline(bool enable) {
    s_direct_pipeline_enabled = enable;
    if (enable && s_decoder_task_handle) {
        xTaskNotifyGive(s_decoder_task_handle);
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

    // 1. Decoder para Fullscreen 480x320 con rotación 90° (salida 320x480 RGB565 LE)
    if (!s_dec_full) {
        jpeg_dec_config_t cfg_full = DEFAULT_JPEG_DEC_CONFIG();
        cfg_full.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;
        cfg_full.rotate = JPEG_ROTATE_90D;
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

    // 3. Búferes PSRAM para triple búfer de cuadro completo alineados a 64 B
    for (int i = 0; i < NUM_FULL_FRAME_BUFS; i++) {
        if (!s_full_frame_bufs[i]) {
            s_full_frame_bufs[i] = (uint16_t *)heap_caps_aligned_alloc(64, FULL_FRAME_BYTES, MALLOC_CAP_SPIRAM);
            if (!s_full_frame_bufs[i]) {
                ESP_LOGE(TAG, "Fallo al reservar s_full_frame_bufs[%d] en PSRAM", i);
                return ESP_ERR_NO_MEM;
            }
            memset(s_full_frame_bufs[i], 0, FULL_FRAME_BYTES);
        }
    }
    if (!s_clipped_buf) {
        s_clipped_buf = (uint16_t *)heap_caps_aligned_alloc(64, FULL_FRAME_BYTES, MALLOC_CAP_SPIRAM);
        if (!s_clipped_buf) {
            ESP_LOGE(TAG, "Fallo al reservar s_clipped_buf en PSRAM");
            return ESP_ERR_NO_MEM;
        }
        memset(s_clipped_buf, 0, FULL_FRAME_BYTES);
    }

    // 4. Semáforos de sincronización para pipeline desacoplado en anillo de 3 búferes
    if (!s_ring_free_sem) {
        s_ring_free_sem = xSemaphoreCreateCounting(NUM_FULL_FRAME_BUFS, NUM_FULL_FRAME_BUFS);
        s_ring_ready_sem = xSemaphoreCreateCounting(NUM_FULL_FRAME_BUFS, 0);
        assert(s_ring_free_sem != NULL && s_ring_ready_sem != NULL);
    }

    // 5. Tarea de decodificación SIMD en Core 1 (prioridad 4, subordinada a player_task p5)
    if (!s_decoder_task_handle) {
        BaseType_t ret_dec = xTaskCreatePinnedToCore(
            avi_decoder_task,
            "avi_decoder",
            4096,
            NULL,
            4,
            &s_decoder_task_handle,
            1
        );
        if (ret_dec != pdPASS) {
            ESP_LOGE(TAG, "Fallo al crear avi_decoder_task en Core 1");
            return ESP_FAIL;
        }
    }

    ESP_LOGI(TAG, "Decodificadores SIMD Fullscreen (Rot 90°) y Studio inicializados con éxito.");
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
    s_prerolled = false;
    s_buf_head = 0;
    s_buf_tail = 0;
    s_buf_count = 0;
    if (s_ring_ready_sem && s_ring_free_sem) {
        while (xSemaphoreTake(s_ring_ready_sem, 0) == pdTRUE);
        while (xSemaphoreTake(s_ring_free_sem, 0) == pdTRUE);
        for (int i = 0; i < NUM_FULL_FRAME_BUFS; i++) {
            xSemaphoreGive(s_ring_free_sem);
        }
    }

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }

    if (s_reader_task_handle) {
        xTaskNotifyGive(s_reader_task_handle);
    }
    if (s_decoder_task_handle && s_direct_pipeline_enabled) {
        xTaskNotifyGive(s_decoder_task_handle);
    }

    // Preroll: precargar búferes
    for (int w = 0; w < 40; w++) {
        if (s_direct_pipeline_enabled) {
            if (s_buf_count >= 2 || s_info.is_eof) break;
        } else {
            if (uxQueueMessagesWaiting(s_q_ready) >= 3 || s_info.is_eof) break;
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    if (s_direct_pipeline_enabled) {
        s_info.current_frame = 0;
        s_info.elapsed_sec = 0;
        s_prerolled = (s_buf_count > 0);
    } else {
        avi_player_preroll_first_frame();
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
    s_prerolled = false;
    s_buf_head = 0;
    s_buf_tail = 0;
    s_buf_count = 0;
    if (s_ring_ready_sem && s_ring_free_sem) {
        while (xSemaphoreTake(s_ring_ready_sem, 0) == pdTRUE);
        while (xSemaphoreTake(s_ring_free_sem, 0) == pdTRUE);
        for (int i = 0; i < NUM_FULL_FRAME_BUFS; i++) {
            xSemaphoreGive(s_ring_free_sem);
        }
    }
    if (s_file_mutex) {
        xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    }

    if (s_q_ready && s_q_free) {
        avi_slot_t *s;
        while (xQueueReceive(s_q_ready, &s, 0) == pdTRUE) {
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

static esp_err_t avi_player_preroll_first_frame(void) {
    if (!s_file || !s_info.is_open) return ESP_ERR_INVALID_STATE;
    if (s_decoder_task_handle && s_direct_pipeline_enabled) {
        xTaskNotifyGive(s_decoder_task_handle);
    }
    for (int w = 0; w < 30; w++) {
        if (s_buf_count >= 2 || s_info.is_eof) break;
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    s_prerolled = (s_buf_count > 0);
    return (s_buf_count > 0) ? ESP_OK : ESP_ERR_TIMEOUT;
}

esp_err_t avi_player_read_and_blit_direct(void) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    if (xSemaphoreTake(s_ring_ready_sem, pdMS_TO_TICKS(100)) != pdTRUE) {
        if (s_info.is_eof && s_buf_count == 0) {
            return ESP_ERR_NOT_FOUND;
        }
        return ESP_ERR_TIMEOUT;
    }

    int buf_to_blit_idx = s_buf_head;
    const uint16_t *buf_to_blit = s_full_frame_bufs[buf_to_blit_idx];

    int16_t vx, vy, vw, vh;
    lcd_bus_get_video_rect(&vx, &vy, &vw, &vh);

    tear_diag_mode_t diag = tear_diag_get_mode();
    uint16_t x1 = 0, y1 = 0, x2 = 319, y2 = 479;
    size_t blit_bytes = FULL_FRAME_BYTES;

    if (diag == TEAR_DIAG_MODE_A) {
        y2 = 239;
        blit_bytes = 320 * 240 * sizeof(uint16_t);
    } else if (diag == TEAR_DIAG_MODE_B) {
        y1 = 80;
        y2 = 95;
        buf_to_blit += (80 * 320);
        blit_bytes = 320 * 16 * sizeof(uint16_t);
    } else if (vh > 0 && vh < 320 && s_clipped_buf) {
        int cx1 = vy;
        int cx2 = vy + vh - 1;
        int clip_w = cx2 - cx1 + 1;
        const uint16_t *src_line = buf_to_blit + cx1;
        uint16_t *dst_line = s_clipped_buf;
        for (int row = 0; row < 480; row++) {
            memcpy(dst_line, src_line, clip_w * sizeof(uint16_t));
            src_line += 320;
            dst_line += clip_w;
        }
        x1 = (uint16_t)vy;
        x2 = (uint16_t)(vy + vh - 1);
        buf_to_blit = s_clipped_buf;
        blit_bytes = (size_t)clip_w * 480 * sizeof(uint16_t);
    }

    // 1. Lanzar DMA asíncrono inmediatamente tras el pulso TE
    lcd_bus_lock();
    esp_err_t tx_err = lcd_bus_draw_strip_async(x1, y1, x2, y2, buf_to_blit, blit_bytes);
    if (tx_err != ESP_OK) {
        lcd_bus_unlock();
        xSemaphoreGive(s_ring_ready_sem);
        return tx_err;
    }

    // 2. Esperar a que concluya la transmisión DMA
    uint32_t dma_us = 0;
    lcd_bus_wait_strip_done(&dma_us);
    lcd_bus_unlock();

    // 3. Actualizar cuadro presentado y avanzar cabeza del anillo
    uint32_t pres_idx = s_frame_idx_ring[s_buf_head];
    s_info.current_frame = pres_idx + 1;
    s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
    s_buf_head = (s_buf_head + 1) % NUM_FULL_FRAME_BUFS;

    portENTER_CRITICAL(&s_ring_mux);
    s_buf_count--;
    portEXIT_CRITICAL(&s_ring_mux);

    // 4. Liberar búfer para que el decodificador prepare el siguiente fotograma
    xSemaphoreGive(s_ring_free_sem);

    perf_mark_direct_frame(1, dma_us);
    perf_mark_presented();

    return ESP_OK;
}

esp_err_t avi_player_skip_next_frame(void) {
    if (!s_file || !s_info.is_open) {
        return ESP_ERR_INVALID_STATE;
    }

    if (xSemaphoreTake(s_ring_ready_sem, 0) == pdTRUE) {
        uint32_t pres_idx = s_frame_idx_ring[s_buf_head];
        s_info.current_frame = pres_idx + 1;
        s_info.elapsed_sec = (s_info.fps > 0) ? (s_info.current_frame / s_info.fps) : 0;
        s_buf_head = (s_buf_head + 1) % NUM_FULL_FRAME_BUFS;
        portENTER_CRITICAL(&s_ring_mux);
        s_buf_count--;
        portEXIT_CRITICAL(&s_ring_mux);
        xSemaphoreGive(s_ring_free_sem);
        return ESP_OK;
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

void avi_player_seek_percent(int percent) {
    if (!s_file) return;

    if (percent < 0) percent = 0;
    if (percent > 99) percent = 99;

    s_reader_run = false;
    if (s_file_mutex) {
        xSemaphoreTake(s_file_mutex, portMAX_DELAY);
    }

    if (s_q_ready && s_q_free) {
        avi_slot_t *s;
        while (xQueueReceive(s_q_ready, &s, 0) == pdTRUE) {
            xQueueSend(s_q_free, &s, 0);
        }
    }

    int fd = fileno(s_file);
    uint32_t target_frame = (percent * s_info.total_frames) / 100;
    if (s_index_table && target_frame < s_info.total_frames) {
        lseek(fd, s_index_table[target_frame], SEEK_SET);
        s_info.current_frame = target_frame;
        s_reader_frame_idx = target_frame;
        s_info.elapsed_sec = (s_info.fps > 0) ? (target_frame / s_info.fps) : 0;
        s_need_index_seek = false;
    } else {
        off_t sz = lseek(fd, 0, SEEK_END);
        off_t target_pos = s_movi_start_offset + (off_t)(((sz - s_movi_start_offset) * (int64_t)percent) / 100);
        lseek(fd, target_pos, SEEK_SET);
        s_info.current_frame = target_frame;
        s_reader_frame_idx = target_frame;
        s_info.elapsed_sec = (s_info.fps > 0) ? (target_frame / s_info.fps) : 0;
        s_need_index_seek = false;
    }

    s_info.is_eof = false;
    s_prerolled = false;
    s_buf_head = 0;
    s_buf_tail = 0;
    s_buf_count = 0;
    if (s_ring_ready_sem && s_ring_free_sem) {
        while (xSemaphoreTake(s_ring_ready_sem, 0) == pdTRUE);
        while (xSemaphoreTake(s_ring_free_sem, 0) == pdTRUE);
        for (int i = 0; i < NUM_FULL_FRAME_BUFS; i++) {
            xSemaphoreGive(s_ring_free_sem);
        }
    }
    s_reader_run = true;

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }

    if (s_reader_task_handle) {
        xTaskNotifyGive(s_reader_task_handle);
    }
    if (s_decoder_task_handle && s_direct_pipeline_enabled) {
        xTaskNotifyGive(s_decoder_task_handle);
    }

    for (int w = 0; w < 30; w++) {
        if (s_direct_pipeline_enabled) {
            if (s_buf_count >= 1 || s_info.is_eof) break;
        } else {
            if (uxQueueMessagesWaiting(s_q_ready) >= 1 || s_info.is_eof) break;
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    avi_player_preroll_first_frame();

    ESP_LOGI(TAG, "Seek completado a %d%% (cuadro %u/%u)",
             percent, (unsigned int)s_info.current_frame, (unsigned int)s_info.total_frames);
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
            xQueueSend(s_q_free, &s, 0);
        }
    }

    lseek(fileno(s_file), s_movi_start_offset, SEEK_SET);
    s_info.current_frame = 0;
    s_reader_frame_idx = 0;
    s_info.elapsed_sec = 0;
    s_info.is_eof = false;
    s_need_index_seek = false;
    s_prerolled = false;
    s_buf_head = 0;
    s_buf_tail = 0;
    s_buf_count = 0;
    if (s_ring_ready_sem && s_ring_free_sem) {
        while (xSemaphoreTake(s_ring_ready_sem, 0) == pdTRUE);
        while (xSemaphoreTake(s_ring_free_sem, 0) == pdTRUE);
        for (int i = 0; i < NUM_FULL_FRAME_BUFS; i++) {
            xSemaphoreGive(s_ring_free_sem);
        }
    }
    s_reader_run = true;

    if (s_file_mutex) {
        xSemaphoreGive(s_file_mutex);
    }

    if (s_reader_task_handle) {
        xTaskNotifyGive(s_reader_task_handle);
    }
    if (s_decoder_task_handle && s_direct_pipeline_enabled) {
        xTaskNotifyGive(s_decoder_task_handle);
    }

    for (int w = 0; w < 30; w++) {
        if (s_direct_pipeline_enabled) {
            if (s_buf_count >= 1 || s_info.is_eof) break;
        } else {
            if (uxQueueMessagesWaiting(s_q_ready) >= 1 || s_info.is_eof) break;
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    avi_player_preroll_first_frame();
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
