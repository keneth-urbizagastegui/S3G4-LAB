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
#include "esp_random.h"

#include "avi_player.h"
#include "media_library.h"
#include "settings_nvs.h"
#include "perf.h"
#include "sdcard_spi.h"
#include "lcd_bus.h"
#include "tear_diag.h"
#include "ili9488_8080.h"
#include "sdkconfig.h"

static const char *TAG = "PLAYER";

#define FULL_W 480
#define FULL_H 320
#define STUDIO_W 240
#define STUDIO_H 160

static portMUX_TYPE s_player_mux = portMUX_INITIALIZER_UNLOCKED;
static QueueHandle_t s_cmd_queue = NULL;
static player_status_t s_status;

static uint16_t *s_buf_studio[2] = {NULL, NULL};
static volatile uint8_t s_std_write_idx = 0;
static volatile uint8_t s_std_read_idx = 1;

static volatile bool s_new_frame_ready = false;
static volatile uint8_t s_current_scale = 0; // 0 = direct blit (reproductor directo)
static int64_t s_track_play_start_us = 0;
static uint32_t s_track_presented_frames = 0;

static TaskHandle_t s_player_task_handle = NULL;
static int64_t s_pts_t0_us = 0;
static bool s_pts_started = false;

static void player_open_track(int index);

static int player_find_compatible(int current, int total, int step) {
    if (total <= 0) return -1;
    for (int i = 1; i <= total; i++) {
        int idx = (current + i * step + total * total) % total;
        const media_item_t *it = media_library_get(idx);
        if (it && it->compatible) return idx;
    }
    return -1;
}

void player_get_track_title(int track_index, char *out_title, size_t max_len) {
    if (!out_title || max_len == 0) return;
    const media_item_t *item = media_library_get(track_index);
    if (item && item->title[0] != '\0') {
        snprintf(out_title, max_len, "%s", item->title);
    } else {
        snprintf(out_title, max_len, "Pista %d", track_index + 1);
    }
}

void player_get_track_subtitle(int track_index, char *out_sub, size_t max_len) {
    if (!out_sub || max_len == 0) return;
    const media_item_t *item = media_library_get(track_index);
    if (item && item->subtitle[0] != '\0') {
        snprintf(out_sub, max_len, "%s", item->subtitle);
    } else {
        out_sub[0] = '\0';
    }
}

static int s_consecutive_open_fails = 0;

static void player_handle_sd_error(void) {
    ESP_LOGE(TAG, "Detectado error critico de E/S en MicroSD. Iniciando procedimiento de recuperacion...");

    // Guardar estado actual de reproduccion para reanudar
    int saved_track = s_status.track_index;
    const avi_info_t *info = avi_player_get_info();
    uint32_t saved_frame = info ? info->current_frame : 0;
    uint32_t total_frames = info ? info->total_frames : 0;

    // Cerrar archivo y desmontar SD
    avi_player_close();
    sdcard_spi_deinit();

    portENTER_CRITICAL(&s_player_mux);
    s_status.state = PST_NO_MEDIA;
    snprintf(s_status.title, sizeof(s_status.title), "Sin microSD");
    snprintf(s_status.subtitle, sizeof(s_status.subtitle), "Inserte tarjeta MicroSD");
    portEXIT_CRITICAL(&s_player_mux);

    ESP_LOGW(TAG, "MicroSD desmontada. Reintentando montaje cada 1 s...");

    // Bucle de reintento de montaje cada 1 s
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        esp_err_t err = sdcard_spi_init();
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "¡MicroSD reconectada con exito! Reescaneando archivos...");
            media_library_scan();
            break;
        }
    }

    // Restaurar reproduccion
    if (media_library_count() > 0) {
        if (saved_track >= media_library_count()) saved_track = 0;
        player_open_track(saved_track);
        if (total_frames > 0 && saved_frame > 0) {
            int pct = (int)(((int64_t)saved_frame * 100) / total_frames);
            if (pct > 99) pct = 99;
            avi_player_seek_percent(pct);
        }
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_PLAYING;
        s_pts_started = false;
        portEXIT_CRITICAL(&s_player_mux);
        ESP_LOGI(TAG, "Reproduccion recuperada con exito en pista %d (cuadro %u)",
                 saved_track, (unsigned int)saved_frame);
    }
}

static void player_open_track(int index) {
    int total = media_library_count();
    if (total <= 0) {
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_NO_MEDIA;
        s_status.track_count = 0;
        portEXIT_CRITICAL(&s_player_mux);
        return;
    }

    if (index < 0) index = 0;
    if (index >= total) index = total - 1;

    const media_item_t *item = media_library_get(index);
    if (!item) return;

    if (!item->compatible) {
        ESP_LOGW(TAG, "Pista %d (%s) no es compatible: %s", index, item->path, item->incompat);
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_ERROR;
        snprintf(s_status.title, sizeof(s_status.title), "%s", item->title);
        snprintf(s_status.subtitle, sizeof(s_status.subtitle), "%s", item->incompat);
        s_status.err_code = 0x434F4D50; // 'COMP'
        portEXIT_CRITICAL(&s_player_mux);
        return;
    }

    // Guardar posicion del video previo si cambiamos de pista
    if (s_status.track_index >= 0 && s_status.track_index < total) {
        const media_item_t *prev = media_library_get(s_status.track_index);
        if (prev && prev->compatible && s_status.pos_ms >= 5000) {
            settings_nvs_set_pos(prev->path, (uint32_t)s_status.pos_ms);
        }
    }

    ESP_LOGI(TAG, "Abriendo pista %d: %s", index, item->path);
    esp_err_t ret = avi_player_open(item->path);
    if (ret != ESP_OK) {
        s_consecutive_open_fails++;
        if (s_consecutive_open_fails >= 2) {
            s_consecutive_open_fails = 0;
            player_handle_sd_error();
            return;
        }
        ESP_LOGE(TAG, "Fallo al abrir pista %d (%s): ret=%d", index, item->path, ret);
        media_library_mark_failed(index);
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_ENDED;
        s_status.err_code = (uint32_t)ret;
        portEXIT_CRITICAL(&s_player_mux);
        return;
    }
    s_consecutive_open_fails = 0;

    const avi_info_t *info = avi_player_get_info();
#ifndef CONFIG_APP_LCD_MADCTL_NATIVE
#define CONFIG_APP_LCD_MADCTL_NATIVE 0x48
#endif
    // Siempre mantener la orientación nativa del panel (0x48)
    ili9488_8080_set_madctl((uint8_t)CONFIG_APP_LCD_MADCTL_NATIVE);

    portENTER_CRITICAL(&s_player_mux);
    s_status.track_index = index;
    s_status.track_count = total;
    s_status.width = (uint16_t)info->width;
    s_status.height = (uint16_t)info->height;
    s_status.fps_milli = (info->us_per_frame > 0) ? (uint32_t)(1000000000ULL / (uint64_t)info->us_per_frame) : 30000;
    s_status.pos_ms = 0;
    s_status.dur_ms = item->dur_ms;
    s_status.state = PST_PLAYING;
    s_status.err_code = 0;

    player_get_track_title(index, s_status.title, sizeof(s_status.title));
    player_get_track_subtitle(index, s_status.subtitle, sizeof(s_status.subtitle));
    if (info->width == 480 && info->height == 320) {
        snprintf(s_status.subtitle, sizeof(s_status.subtitle), "Sin girar");
    }
    s_pts_started = false;
    s_pts_t0_us = 0;
    s_track_play_start_us = esp_timer_get_time();
    s_track_presented_frames = 0;
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
                        snprintf(s_status.title, sizeof(s_status.title), "%.*s", (int)(sizeof(s_status.title) - 1), cmd->path);
                        s_track_play_start_us = esp_timer_get_time();
                        s_track_presented_frames = 0;
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
            s_pts_started = false;
            break;
        }

        case PCMD_PAUSE: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_PAUSED;
            portEXIT_CRITICAL(&s_player_mux);
            s_pts_started = false;
            const media_item_t *cur = media_library_get(s_status.track_index);
            if (cur && cur->compatible && s_status.pos_ms >= 5000) {
                settings_nvs_set_pos(cur->path, (uint32_t)s_status.pos_ms);
            }
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
            s_pts_started = false;
            if (s_status.state == PST_PAUSED) {
                const media_item_t *cur = media_library_get(s_status.track_index);
                if (cur && cur->compatible && s_status.pos_ms >= 5000) {
                    settings_nvs_set_pos(cur->path, (uint32_t)s_status.pos_ms);
                }
            }
            break;
        }

        case PCMD_STOP: {
            const media_item_t *cur = media_library_get(s_status.track_index);
            if (cur && cur->compatible && s_status.pos_ms >= 5000) {
                settings_nvs_set_pos(cur->path, (uint32_t)s_status.pos_ms);
            }
            avi_player_restart();
            s_pts_started = false;
            s_pts_t0_us = 0;
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_IDLE;
            s_status.pos_ms = 0;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_SEEK_MS: {
            // Este caso se procesa en el bucle principal con vaciado/coalescencia de cola
            uint32_t target_ms = (uint32_t)cmd->arg;
            avi_player_seek_ms(target_ms);
            const avi_info_t *info = avi_player_get_info();
            s_pts_started = false;
            s_pts_t0_us = 0;
            portENTER_CRITICAL(&s_player_mux);
            s_status.pos_ms = ((uint64_t)info->current_frame * (uint64_t)info->us_per_frame) / 1000ULL;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_SEEK_REL_MS: {
            int64_t target_ms = (int64_t)s_status.pos_ms + cmd->arg;
            int64_t dur_ms = (int64_t)s_status.dur_ms;
            if (target_ms < 0) target_ms = 0;
            if (target_ms > dur_ms) target_ms = dur_ms;
            avi_player_seek_ms((uint32_t)target_ms);
            const avi_info_t *info = avi_player_get_info();
            s_pts_started = false;
            s_pts_t0_us = 0;
            portENTER_CRITICAL(&s_player_mux);
            s_status.pos_ms = ((uint64_t)info->current_frame * (uint64_t)info->us_per_frame) / 1000ULL;
            portEXIT_CRITICAL(&s_player_mux);
            break;
        }

        case PCMD_NEXT: {
            int total = s_status.track_count;
            if (total > 0) {
                int next = player_find_compatible(s_status.track_index, total, 1);
                if (next >= 0) {
                    player_open_track(next);
                }
            }
            break;
        }

        case PCMD_PREV: {
            int total = s_status.track_count;
            if (total > 0) {
                int prev = player_find_compatible(s_status.track_index, total, -1);
                if (prev >= 0) {
                    player_open_track(prev);
                }
            }
            break;
        }

        case PCMD_SET_REPEAT: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.repeat = (repeat_mode_t)cmd->arg;
            portEXIT_CRITICAL(&s_player_mux);
            settings_nvs_set_u8("repeat", (uint8_t)cmd->arg);
            break;
        }

        case PCMD_SET_SHUFFLE: {
            portENTER_CRITICAL(&s_player_mux);
            s_status.shuffle = (bool)cmd->arg;
            portEXIT_CRITICAL(&s_player_mux);
            settings_nvs_set_u8("shuffle", (uint8_t)(cmd->arg ? 1 : 0));
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

static void player_handle_eof(void) {
    ESP_LOGI(TAG, "Fin de video alcanzado. Aplicando politica de repeticion.");
    const media_item_t *cur = media_library_get(s_status.track_index);
    if (cur) {
        settings_nvs_set_pos(cur->path, 0);
        media_library_set_resume(s_status.track_index, 0);
    }

    if (s_status.repeat == REPEAT_ONE) {
        const char *next_path = cur ? cur->path : "desconocido";
        ESP_LOGI(TAG, "EOF,track=%d,repeat=%d,next_frame_from=%s",
                 s_status.track_index, (int)s_status.repeat, next_path);
        avi_player_restart();
        s_pts_started = false;
        s_pts_t0_us = 0;
        s_track_presented_frames = 0;
        s_track_play_start_us = esp_timer_get_time();
    } else {
        int total = s_status.track_count;
        int next = -1;
        if (s_status.shuffle && total > 1) {
            int rand_start = (int)(esp_random() % total);
            next = player_find_compatible(rand_start - 1, total, 1);
        } else {
            next = player_find_compatible(s_status.track_index, total, 1);
        }

        if (next < 0) {
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_ENDED;
            portEXIT_CRITICAL(&s_player_mux);
            avi_player_restart();
            s_pts_started = false;
            s_pts_t0_us = 0;
            s_track_presented_frames = 0;
            s_track_play_start_us = esp_timer_get_time();
            return;
        }

        if (s_status.repeat == REPEAT_OFF) {
            ESP_LOGI(TAG, "EOF,track=%d,repeat=%d,next_frame_from=none",
                     s_status.track_index, (int)s_status.repeat);
            portENTER_CRITICAL(&s_player_mux);
            s_status.state = PST_ENDED;
            portEXIT_CRITICAL(&s_player_mux);
            avi_player_close();
            s_pts_started = false;
            s_pts_t0_us = 0;
            s_track_play_start_us = 0;
            return;
        } else {
            const media_item_t *next_it = media_library_get(next);
            const char *next_path = next_it ? next_it->path : "desconocido";
            ESP_LOGI(TAG, "EOF,track=%d,repeat=%d,next_frame_from=%s",
                     s_status.track_index, (int)s_status.repeat, next_path);
            player_open_track(next);
        }
    }
}

static void player_task(void *arg) {
    ESP_LOGI(TAG, "Tarea player_task ejecutandose en CPU 1.");

    // Cargar configuracion persistente de NVS
    app_settings_t nvs_cfg;
    settings_nvs_load(&nvs_cfg);

    portENTER_CRITICAL(&s_player_mux);
    s_status.repeat = (repeat_mode_t)nvs_cfg.repeat;
    s_status.shuffle = (nvs_cfg.shuffle != 0);
    portEXIT_CRITICAL(&s_player_mux);

    int initial_track = -1;
    if (nvs_cfg.last_path[0] != '\0') {
        int idx = media_library_index_of(nvs_cfg.last_path);
        const media_item_t *it = (idx >= 0) ? media_library_get(idx) : NULL;
        if (it && it->compatible && !it->failed_playback) {
            initial_track = idx;
        } else {
            ESP_LOGW(TAG, "last_path '%s' invalido o incompatible, ignorando y abriendo biblioteca", nvs_cfg.last_path);
            settings_nvs_set_last_path("");
            initial_track = -1;
        }
    }

    if (initial_track >= 0) {
        player_open_track(initial_track);
        const media_item_t *it = media_library_get(initial_track);
        if (nvs_cfg.resume && it && it->resume_ms >= 5000) {
            ESP_LOGI(TAG, "Reanudando '%s' en %u ms (NVS resume=1)", it->path, (unsigned int)it->resume_ms);
            avi_player_seek_ms(it->resume_ms);
            const avi_info_t *info = avi_player_get_info();
            portENTER_CRITICAL(&s_player_mux);
            s_status.pos_ms = ((uint64_t)info->current_frame * (uint64_t)info->us_per_frame) / 1000ULL;
            portEXIT_CRITICAL(&s_player_mux);
        }
    } else {
        portENTER_CRITICAL(&s_player_mux);
        s_status.state = PST_IDLE;
        s_status.track_count = media_library_count();
        portEXIT_CRITICAL(&s_player_mux);
    }

    int64_t last_nvs_pos_save_us = esp_timer_get_time();

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
            tear_diag_mode_t diag = tear_diag_get_mode();
            if (diag == TEAR_DIAG_MODE_C) {
                // Modo C: patron de prueba sin video (alternar pantalla completa rojo/azul sincronizado con TE)
                static bool s_diag_c_toggle = false;
                s_diag_c_toggle = !s_diag_c_toggle;
                uint16_t color = s_diag_c_toggle ? 0xF800 : 0x001F; // Rojo o Azul RGB565

                static uint16_t *s_diag_c_buf = NULL;
                if (!s_diag_c_buf) {
                    s_diag_c_buf = (uint16_t *)heap_caps_aligned_alloc(16, 480 * 16 * sizeof(uint16_t), MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
                }
                if (s_diag_c_buf) {
                    uint8_t cur_madctl = ili9488_8080_get_madctl();
                    bool is_native = (cur_madctl == (uint8_t)CONFIG_APP_LCD_MADCTL_NATIVE);
                    int strip_w = is_native ? 320 : 480;
                    int num_strips = is_native ? 30 : 20;

                    // 1. Preparar datos del buffer ANTES de esperar TE
                    for (int p = 0; p < strip_w * 16; p++) {
                        s_diag_c_buf[p] = color;
                    }

                    lcd_bus_lock();

                    // 2. Esperar flanco TE para sincronizar el inicio exacto del blit con el V-blank
#if CONFIG_APP_TE_SYNC
                    if (lcd_bus_te_is_present()) {
                        uint32_t te_period = lcd_bus_te_get_period_us();
                        uint32_t te_timeout = (te_period * 3) / 2;
                        uint32_t te_wait_us = 0;
                        esp_err_t te_res = lcd_bus_wait_te(te_timeout, &te_wait_us);
                        if (te_res == ESP_OK) {
                            perf_mark_te_wait(te_wait_us);
                        } else {
                            perf_mark_te_timeout();
                        }
                    }
#endif

                    // 3. Inmediatamente tras el flanco TE, emitir franjas
                    for (int b = 0; b < num_strips; b++) {
                        uint16_t y1 = b * 16;
                        uint16_t y2 = y1 + 15;
                        lcd_bus_draw_strip_async(0, y1, strip_w - 1, y2, s_diag_c_buf, strip_w * 16 * sizeof(uint16_t));
                        lcd_bus_wait_strip_done(NULL);
                    }
                    lcd_bus_unlock();
                }

                perf_mark_presented();
                vTaskDelay(pdMS_TO_TICKS(15));
                continue;
            }

            const avi_info_t *cur_info = avi_player_get_info();
            if (!cur_info->is_open) {
                vTaskDelay(pdMS_TO_TICKS(20));
                continue;
            }

            // Watchdog D5: Si transcurren >3 s en PST_PLAYING sin presentar ningun frame, abortar reproduccion
            int64_t elapsed_play_us = esp_timer_get_time() - s_track_play_start_us;
            if (s_track_play_start_us > 0 && elapsed_play_us > 3000000LL && s_track_presented_frames == 0) {
                ESP_LOGE(TAG, "Watchdog D5: >3s sin presentar cuadros en pista %d (%s). Abortando reproduccion.",
                         s_status.track_index, s_status.title);
                if (s_status.track_index >= 0) {
                    media_library_mark_failed(s_status.track_index);
                }
                avi_player_close();
                settings_nvs_set_last_path("");

                if (s_status.repeat != REPEAT_OFF) {
                    int total = s_status.track_count;
                    int next = player_find_compatible(s_status.track_index, total, 1);
                    if (next >= 0 && next != s_status.track_index) {
                        player_open_track(next);
                        continue;
                    }
                }
                portENTER_CRITICAL(&s_player_mux);
                s_status.state = PST_ENDED;
                s_status.err_code = ESP_ERR_TIMEOUT;
                portEXIT_CRITICAL(&s_player_mux);
                continue;
            }

            // Inicializar reloj PTS (t0 = now - pos_us)
            if (!s_pts_started) {
                int64_t pos_us = (int64_t)cur_info->current_frame * (int64_t)cur_info->us_per_frame;
                s_pts_t0_us = esp_timer_get_time() - pos_us;
                s_pts_started = true;
            }

            int64_t now_us = esp_timer_get_time();
            int64_t due_us = s_pts_t0_us + (int64_t)cur_info->current_frame * (int64_t)cur_info->us_per_frame;
            int64_t late = now_us - due_us;

            // Deteccion de desincronia PTS / saltos temporales bruscos (SEEK frecuente o cambio de flujo)
            if (late < -50000 || late > 100000) {
                int64_t pos_us = (int64_t)cur_info->current_frame * (int64_t)cur_info->us_per_frame;
                s_pts_t0_us = now_us - pos_us;
                due_us = s_pts_t0_us + pos_us;
                late = 0;
            }

            if (late > 0) {
                perf_mark_late((uint32_t)late);
            }

            // Si late > us_per_frame + margen de fase TE: saltar el chunk SIN decodificar
#if CONFIG_APP_TE_SYNC
            int64_t drop_threshold = (int64_t)cur_info->us_per_frame * 2 - 2000;
#else
            int64_t drop_threshold = (int64_t)cur_info->us_per_frame + 8000;
#endif
            if (late > drop_threshold) {
                esp_err_t ret_skip = avi_player_skip_next_frame();
                if (ret_skip == ESP_OK) {
                    perf_mark_dropped();
                    portENTER_CRITICAL(&s_player_mux);
                    s_status.dropped++;
                    s_status.pos_ms = ((uint64_t)cur_info->current_frame * (uint64_t)cur_info->us_per_frame) / 1000ULL;
                    s_status.dur_ms = ((uint64_t)cur_info->total_frames * (uint64_t)cur_info->us_per_frame) / 1000ULL;
                    perf_get_fps(&s_status.dec_fps, &s_status.pres_fps);
                    portEXIT_CRITICAL(&s_player_mux);

                    // drift_ms = pos_ms del reproductor - tiempo de pared transcurrido desde t0 (con signo)
                    int64_t wall_ms = (esp_timer_get_time() - s_pts_t0_us) / 1000;
                    int32_t drift_ms = (int32_t)((int64_t)s_status.pos_ms - wall_ms);
                    perf_mark_drift(drift_ms);
                    continue;
                } else if (ret_skip == ESP_ERR_NOT_FOUND) {
                    player_handle_eof();
                    continue;
                }
            }

#if CONFIG_APP_TE_SYNC
            int64_t te_lead_us = 0;
            if (scale != 1 && lcd_bus_te_is_present()) {
                uint32_t te_p = lcd_bus_te_get_period_us();
                te_lead_us = (int64_t)(te_p / 2);
            }
            int64_t wait_target_us = due_us - te_lead_us;
#else
            int64_t wait_target_us = due_us;
#endif

            // Si llega adelantado: esperar con precisión
            int64_t diff = now_us - wait_target_us;
            if (diff < -2000) {
                int64_t wait = -diff;
                if (wait > 3000) {
                    vTaskDelay(pdMS_TO_TICKS((wait - 2000) / 1000));
                }
                while (esp_timer_get_time() < wait_target_us) {
                    taskYIELD();
                }
            } else if (diff < 0) {
                while (esp_timer_get_time() < wait_target_us) {
                    taskYIELD();
                }
            }

            esp_err_t ret;
            if (scale == 1) {
                uint16_t *target_buf = s_buf_studio[s_std_write_idx];
                ret = avi_player_read_next_frame(target_buf, 1);
                if (ret == ESP_OK) {
                    perf_mark_decoded();

                    // Traspaso atomico de frame a LVGL (solo modo Studio)
                    portENTER_CRITICAL(&s_player_mux);
                    s_std_read_idx = s_std_write_idx;
                    s_std_write_idx = (s_std_write_idx + 1) % 2;
                    s_new_frame_ready = true;

                    const avi_info_t *info = avi_player_get_info();
                    s_status.pos_ms = ((uint64_t)info->current_frame * (uint64_t)info->us_per_frame) / 1000ULL;
                    s_status.dur_ms = ((uint64_t)info->total_frames * (uint64_t)info->us_per_frame) / 1000ULL;
                    perf_get_fps(&s_status.dec_fps, &s_status.pres_fps);
                    portEXIT_CRITICAL(&s_player_mux);

                    int64_t wall_ms = (esp_timer_get_time() - s_pts_t0_us) / 1000;
                    int32_t drift_ms = (int32_t)((int64_t)s_status.pos_ms - wall_ms);
                    perf_mark_drift(drift_ms);
                } else if (ret == ESP_ERR_NOT_FOUND) {
                    player_handle_eof();
                    continue;
                } else if (ret == ESP_ERR_INVALID_RESPONSE || ret == ESP_FAIL) {
                    player_handle_sd_error();
                } else {
                    vTaskDelay(pdMS_TO_TICKS(10));
                }
            } else {
                // Modo Direct Fullscreen por franjas DMA (P2)
#if CONFIG_APP_TE_SYNC
                if (lcd_bus_te_is_present()) {
                    uint32_t te_period = lcd_bus_te_get_period_us();
                    uint32_t te_timeout = (te_period * 3) / 2; // tope 1,5 x periodo medido
                    uint32_t te_wait_us = 0;
                    esp_err_t te_res = lcd_bus_wait_te(te_timeout, &te_wait_us);
                    if (te_res == ESP_OK) {
                        perf_mark_te_wait(te_wait_us);
                    } else {
                        perf_mark_te_timeout();
                    }
                }
#endif
                ret = avi_player_read_and_blit_direct();
                if (ret == ESP_OK) {
                    perf_mark_decoded();

                    portENTER_CRITICAL(&s_player_mux);
                    const avi_info_t *info = avi_player_get_info();
                    s_status.pos_ms = ((uint64_t)info->current_frame * (uint64_t)info->us_per_frame) / 1000ULL;
                    s_status.dur_ms = ((uint64_t)info->total_frames * (uint64_t)info->us_per_frame) / 1000ULL;
                    perf_get_fps(&s_status.dec_fps, &s_status.pres_fps);
                    portEXIT_CRITICAL(&s_player_mux);

                    int64_t wall_ms = (esp_timer_get_time() - s_pts_t0_us) / 1000;
                    int32_t drift_ms = (int32_t)((int64_t)s_status.pos_ms - wall_ms);
                    perf_mark_drift(drift_ms);
                } else if (ret == ESP_ERR_NOT_FOUND) {
                    player_handle_eof();
                    continue;
                } else if (ret == ESP_ERR_INVALID_RESPONSE || ret == ESP_FAIL) {
                    player_handle_sd_error();
                } else {
                    vTaskDelay(pdMS_TO_TICKS(10));
                }
            }

            if (ret == ESP_OK) {
                s_track_presented_frames++;
                int64_t now_us = esp_timer_get_time();
                if (now_us - last_nvs_pos_save_us >= 5000000) {
                    last_nvs_pos_save_us = now_us;
                    const media_item_t *cur_it = media_library_get(s_status.track_index);
                    if (cur_it && cur_it->compatible && !cur_it->failed_playback && s_status.pos_ms >= 5000) {
                        float dec_fps = 0, pres_fps = 0;
                        perf_get_fps(&dec_fps, &pres_fps);
                        if (pres_fps > 0.0f || s_track_presented_frames >= 30) {
                            settings_nvs_set_last_path(cur_it->path);
                            settings_nvs_set_pos(cur_it->path, (uint32_t)s_status.pos_ms);
                        }
                    }
                }
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
    s_current_scale = 0; // 0 = direct blit a pantalla completa
    portEXIT_CRITICAL(&s_player_mux);

    if (!s_cmd_queue) {
        s_cmd_queue = xQueueCreate(8, sizeof(player_cmd_t));
        if (!s_cmd_queue) {
            ESP_LOGE(TAG, "Fallo al crear cola de comandos");
            return ESP_ERR_NO_MEM;
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

    // Stack ajustado de 16 KB a 8 KB tras medir HighWaterMark (Obs O2: max uso 4620 B, margen >= 3.5 KB)
    BaseType_t ret = xTaskCreatePinnedToCore(player_task, "player_task", 8 * 1024, NULL, 5, &s_player_task_handle, 1);
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
        }
    }
    portEXIT_CRITICAL(&s_player_mux);
    return has_new;
}

uint32_t player_get_task_stack_high_water_mark(void) {
    if (!s_player_task_handle) return 0;
    return (uint32_t)uxTaskGetStackHighWaterMark(s_player_task_handle);
}
