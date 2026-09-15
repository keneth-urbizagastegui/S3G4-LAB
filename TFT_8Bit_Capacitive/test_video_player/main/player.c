#include "player.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/portmacro.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"

#include "avi_player.h"
#include "perf.h"
#include "sdcard_spi.h"

static const char *TAG = "PLAYER";

#define FULL_W 480
#define FULL_H 320
#define STUDIO_W 240
#define STUDIO_H 160

static portMUX_TYPE s_player_mux = portMUX_INITIALIZER_UNLOCKED;
static QueueHandle_t s_cmd_queue = NULL;
static player_status_t s_status;

static uint16_t *s_buf_fullscreen[2] = {NULL, NULL};
static volatile uint8_t s_fs_write_idx = 0;
static volatile uint8_t s_fs_read_idx = 1;

static uint16_t *s_buf_studio[2] = {NULL, NULL};
static volatile uint8_t s_std_write_idx = 0;
static volatile uint8_t s_std_read_idx = 1;

static volatile bool s_new_frame_ready = false;
static volatile uint8_t s_current_scale = 0; // 0 = fullscreen 480x320, 1 = studio 240x160

static void player_open_track(int index);

void player_get_track_title(int track_index, char *out_title, size_t max_len) {
    if (!out_title || max_len == 0) return;
    const char *path = media_get_avi_path(track_index);
    if (!path) {
        snprintf(out_title, max_len, "Pista %d", track_index + 1);
        return;
    }
    if (strstr(path, "harry.avi")) {
        strncpy(out_title, "Dance No More", max_len - 1);
    } else if (strstr(path, "ariana.avi")) {
        strncpy(out_title, "hate that i made you love me", max_len - 1);
    } else if (strstr(path, "lesserafim.avi")) {
        strncpy(out_title, "ICONIC BY MISTAKE", max_len - 1);
    } else if (strstr(path, "meovv.avi")) {
        strncpy(out_title, "HANDS UP", max_len - 1);
    } else {
        const char *base = strrchr(path, '/');
        base = base ? (base + 1) : path;
        strncpy(out_title, base, max_len - 1);
        char *dot = strrchr(out_title, '.');
        if (dot) *dot = '\0';
    }
    out_title[max_len - 1] = '\0';
}

void player_get_track_subtitle(int track_index, char *out_sub, size_t max_len) {
    if (!out_sub || max_len == 0) return;
    const char *path = media_get_avi_path(track_index);
    if (!path) {
        out_sub[0] = '\0';
        return;
    }
    if (strstr(path, "harry.avi")) {
        strncpy(out_sub, "Harry Styles", max_len - 1);
    } else if (strstr(path, "ariana.avi")) {
        strncpy(out_sub, "Ariana Grande", max_len - 1);
    } else if (strstr(path, "lesserafim.avi")) {
        strncpy(out_sub, "LE SSERAFIM x ILLIT", max_len - 1);
    } else if (strstr(path, "meovv.avi")) {
        strncpy(out_sub, "MEOVV", max_len - 1);
    } else {
        strncpy(out_sub, "Video", max_len - 1);
    }
    out_sub[max_len - 1] = '\0';
}

static void player_open_track(int index) {
    int total = media_get_avi_count();
    if (total <= 0) {
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_NO_MEDIA;
        s_status.track_count = 0;
        portEXIT_CRITICAL(&s_player_mux);
        return;
    }

    if (index < 0) index = 0;
    if (index >= total) index = total - 1;

    const char *path = media_get_avi_path(index);
    if (!path) return;

    ESP_LOGI(TAG, "Abriendo pista %d: %s", index, path);
    esp_err_t ret = avi_player_open(path);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al abrir pista %d (%s): ret=%d", index, path, ret);
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_ERROR;
        s_status.err_code = (uint32_t)ret;
        portEXIT_CRITICAL(&s_player_mux);
        return;
    }

    const avi_info_t *info = avi_player_get_info();
    portENTER_CRITICAL(&s_player_mux);
    s_status.track_index = index;
    s_status.track_count = total;
    s_status.width = (uint16_t)info->width;
    s_status.height = (uint16_t)info->height;
    s_status.fps_milli = (info->us_per_frame > 0) ? (uint32_t)(1000000000ULL / (uint64_t)info->us_per_frame) : 30000;
    s_status.pos_ms = 0;
    s_status.dur_ms = ((uint64_t)info->total_frames * (uint64_t)info->us_per_frame) / 1000ULL;
    s_status.state = PST_PLAYING;
    s_status.err_code = 0;

    player_get_track_title(index, s_status.title, sizeof(s_status.title));
    player_get_track_subtitle(index, s_status.subtitle, sizeof(s_status.subtitle));
    portEXIT_CRITICAL(&s_player_mux);
}

static void player_handle_cmd(const player_cmd_t *cmd) {
    if (!cmd) return;

    switch (cmd->type) {
        case PCMD_OPEN: {
            if (cmd->path[0] != '\0') {
                int total = media_get_avi_count();
                int matched_idx = -1;
                for (int i = 0; i < total; i++) {
                    const char *p = media_get_avi_path(i);
                    if (p && strcmp(p, cmd->path) == 0) {
                        matched_idx = i;
                        break;
                    }
                }
                if (matched_idx >= 0) {
                    player_open_track(matched_idx);
                } else {
                    ESP_LOGI(TAG, "Abriendo archivo personalizado: %s", cmd->path);
                    esp_err_t ret = avi_player_open(cmd->path);
                    if (ret == ESP_OK) {
                        const avi_info_t *info = avi_player_get_info();
                        portENTER_CRITICAL(&s_player_mux);
                        s_status.state = PST_PLAYING;
                        s_status.width = (uint16_t)info->width;
                        s_status.height = (uint16_t)info->height;
                        s_status.pos_ms = 0;
                        s_status.dur_ms = ((uint64_t)info->total_frames * (uint64_t)info->us_per_frame) / 1000ULL;
                        strncpy(s_status.title, cmd->path, sizeof(s_status.title) - 1);
                        s_status.title[sizeof(s_status.title) - 1] = '\0';
                        portEXIT_CRITICAL(&s_player_mux);
                    }
                }
            } else {
                player_open_track(cmd->arg);
            }
            break;
        }

        case PCMD_PLAY: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_PLAYING;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_PAUSE: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_PAUSED;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_TOGGLE: {
            portENTER_CRITICAL(&s_player_mux);
            if (s_status.state == PST_PLAYING) {
                s_status.state = PST_PAUSED;
            } else {
                s_status.state = PST_PLAYING;
            }
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_STOP: {
            avi_player_restart();
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_IDLE;
            s_status.pos_ms = 0;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_SEEK_MS: {
            // Este caso se procesa en el bucle principal con vaciado/coalescencia de cola
            int64_t dur_ms = (int64_t)s_status.dur_ms;
            int pct = (dur_ms > 0) ? (int)(((int64_t)cmd->arg * 100) / dur_ms) : 0;
            if (pct < 0) pct = 0;
            if (pct > 99) pct = 99;
            avi_player_seek_percent(pct);
            portENTER_CRITICAL(&s_player_mux);
            s_status.pos_ms = (uint64_t)cmd->arg;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_SEEK_REL_MS: {
            int64_t target_ms = (int64_t)s_status.pos_ms + cmd->arg;
            int64_t dur_ms = (int64_t)s_status.dur_ms;
            if (target_ms < 0) target_ms = 0;
            if (target_ms > dur_ms) target_ms = dur_ms;
            int pct = (dur_ms > 0) ? (int)((target_ms * 100) / dur_ms) : 0;
            avi_player_seek_percent(pct);
            portENTER_CRITICAL(&s_player_mux);
            s_status.pos_ms = (uint64_t)target_ms;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_NEXT: {
            int total = s_status.track_count;
            if (total > 0) {
                int next = (s_status.track_index + 1) % total;
                player_open_track(next);
            }
            break;
        }

        case PCMD_PREV: {
            int total = s_status.track_count;
            if (total > 0) {
                int prev = (s_status.track_index - 1 + total) % total;
                player_open_track(prev);
            }
            break;
        }

        case PCMD_SET_REPEAT: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.repeat = (repeat_mode_t)cmd->arg;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_SET_SHUFFLE: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.shuffle = (bool)cmd->arg;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_SET_VIDEO_RECT: {
            portENTER_CRITICAL(&s_player_mux);
            if (cmd->rect.w <= STUDIO_W && cmd->rect.h <= STUDIO_H && cmd->rect.w > 0) {
                s_current_scale = 1;
            } else {
                s_current_scale = 0;
            }
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        default:
            break;
    }
}

static void player_task(void *arg) {
    ESP_LOGI(TAG, "Tarea player_task ejecutandose en CPU 1.");

    // Abrir pista inicial
    player_open_track(0);

    while (1) {
        perf_report_if_due();

        // 1. Procesar cola de comandos con coalescencia de SEEK
        player_cmd_t cmd;
        while (xQueueReceive(s_cmd_queue, &cmd, 0) == pdPASS) {
            if (cmd.type == PCMD_SEEK_MS) {
                // Vaciado de SEEKs consecutivos: quedarse solo con el ultimo
                player_cmd_t peek_cmd;
                while (xQueuePeek(s_cmd_queue, &peek_cmd, 0) == pdPASS) {
                    if (peek_cmd.type == PCMD_SEEK_MS) {
                        xQueueReceive(s_cmd_queue, &cmd, 0);
                    } else {
                        break;
                    }
                }
            }
            player_handle_cmd(&cmd);
        }

        // 2. Decodificacion si esta en reproduccion activa
        player_state_t cur_state;
        portENTER_CRITICAL(&s_player_mux);
        cur_state = s_status.state;
        uint8_t scale = s_current_scale;
        portEXIT_CRITICAL(&s_player_mux);

        if (cur_state == PST_PLAYING) {
            const avi_info_t *cur_info = avi_player_get_info();
            if (!cur_info->is_open) {
                vTaskDelay(pdMS_TO_TICKS(20));
                continue;
            }

            uint16_t *target_buf = (scale == 1) ? s_buf_studio[s_std_write_idx] : s_buf_fullscreen[s_fs_write_idx];
            int64_t t_start = esp_timer_get_time();
            esp_err_t ret = avi_player_read_next_frame(target_buf, scale);

            if (ret == ESP_OK) {
                perf_mark_decoded();

                // Traspaso atomico de frame
                portENTER_CRITICAL(&s_player_mux);
                if (scale == 1) {
                    s_std_read_idx = s_std_write_idx;
                    s_std_write_idx = (s_std_write_idx + 1) % 2;
                } else {
                    s_fs_read_idx = s_fs_write_idx;
                    s_fs_write_idx = (s_fs_write_idx + 1) % 2;
                }
                s_new_frame_ready = true;

                const avi_info_t *info = avi_player_get_info();
                s_status.pos_ms = ((uint64_t)info->current_frame * (uint64_t)info->us_per_frame) / 1000ULL;
                s_status.dur_ms = ((uint64_t)info->total_frames * (uint64_t)info->us_per_frame) / 1000ULL;
                perf_get_fps(&s_status.dec_fps, &s_status.pres_fps);
                portEXIT_CRITICAL(&s_player_mux);

                // Cadencia de reproduccion
                int64_t elapsed_us = esp_timer_get_time() - t_start;
                int32_t delay_us = (int32_t)info->us_per_frame - (int32_t)elapsed_us;
                if (delay_us > 1000) {
                    vTaskDelay(pdMS_TO_TICKS(delay_us / 1000));
                } else {
                    vTaskDelay(1);
                }
            } else if (ret == ESP_ERR_NOT_FOUND) {
                // Fin de video (EOF)
                ESP_LOGI(TAG, "Fin de video alcanzado. Aplicando politica de repeticion.");
                if (s_status.repeat == REPEAT_ONE) {
                    avi_player_restart();
                } else {
                    int next = (s_status.track_index + 1) % s_status.track_count;
                    if (s_status.repeat == REPEAT_OFF && next == 0) {
                        portENTER_CRITICAL(&s_player_mux);
                        s_status.state = PST_ENDED;
                        portEXIT_CRITICAL(&s_player_mux);
                        avi_player_restart();
                    } else {
                        player_open_track(next);
                    }
                }
            } else {
                vTaskDelay(pdMS_TO_TICKS(10));
            }
        } else {
            vTaskDelay(pdMS_TO_TICKS(20));
        }
    }
}

esp_err_t player_start(void) {
    ESP_LOGI(TAG, "Iniciando subsistema player...");

    portENTER_CRITICAL(&s_player_mux);
    memset(&s_status, 0, sizeof(s_status));
    s_status.state = PST_IDLE;
    s_status.repeat = REPEAT_ALL;
    s_status.shuffle = false;
    portEXIT_CRITICAL(&s_player_mux);

    if (!s_cmd_queue) {
        s_cmd_queue = xQueueCreate(8, sizeof(player_cmd_t));
        if (!s_cmd_queue) {
            ESP_LOGE(TAG, "Fallo al crear cola de comandos");
            return ESP_ERR_NO_MEM;
        }
    }

    // Reservar doble búfer Fullscreen en PSRAM (480x320 RGB565)
    for (int i = 0; i < 2; i++) {
        if (!s_buf_fullscreen[i]) {
            s_buf_fullscreen[i] = (uint16_t *)heap_caps_aligned_alloc(64, FULL_W * FULL_H * 2, MALLOC_CAP_SPIRAM);
            if (!s_buf_fullscreen[i]) {
                ESP_LOGE(TAG, "Fallo al reservar s_buf_fullscreen[%d] en PSRAM", i);
                return ESP_ERR_NO_MEM;
            }
            memset(s_buf_fullscreen[i], 0, FULL_W * FULL_H * 2);
        }
    }

    // Reservar doble búfer Studio en PSRAM (240x160 RGB565)
    for (int i = 0; i < 2; i++) {
        if (!s_buf_studio[i]) {
            s_buf_studio[i] = (uint16_t *)heap_caps_aligned_alloc(64, STUDIO_W * STUDIO_H * 2, MALLOC_CAP_SPIRAM);
            if (!s_buf_studio[i]) {
                ESP_LOGE(TAG, "Fallo al reservar s_buf_studio[%d] en PSRAM", i);
                return ESP_ERR_NO_MEM;
            }
            memset(s_buf_studio[i], 0, STUDIO_W * STUDIO_H * 2);
        }
    }

    BaseType_t ret = xTaskCreatePinnedToCore(player_task, "player_task", 16 * 1024, NULL, 5, NULL, 1);
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "Fallo al crear player_task en CPU 1");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "player_task iniciada con exito en CPU 1.");
    return ESP_OK;
}

bool player_cmd_send(const player_cmd_t *c) {
    if (!s_cmd_queue || !c) return false;
    return (xQueueSend(s_cmd_queue, c, 0) == pdPASS);
}

void player_get_status(player_status_t *out) {
    if (!out) return;
    portENTER_CRITICAL(&s_player_mux);
    memcpy(out, &s_status, sizeof(player_status_t));
    portEXIT_CRITICAL(&s_player_mux);
}

bool player_check_and_clear_new_frame(uint16_t **out_frame_buf, int *out_w, int *out_h) {
    bool has_new = false;
    portENTER_CRITICAL(&s_player_mux);
    if (s_new_frame_ready) {
        s_new_frame_ready = false;
        has_new = true;
        if (s_current_scale == 1) {
            if (out_frame_buf) *out_frame_buf = s_buf_studio[s_std_read_idx];
            if (out_w) *out_w = STUDIO_W;
            if (out_h) *out_h = STUDIO_H;
        } else {
            if (out_frame_buf) *out_frame_buf = s_buf_fullscreen[s_fs_read_idx];
            if (out_w) *out_w = FULL_W;
            if (out_h) *out_h = FULL_H;
        }
    }
    portEXIT_CRITICAL(&s_player_mux);
    return has_new;
}
