#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "esp_random.h"
#include "sdkconfig.h"

#include "lvgl.h"
#include "ili9488_8080.h"
#include "ft6236_i2c.h"
#include "sdcard_spi.h"
#include "avi_player.h"
#include "spotify_ui.h"
#include "perf.h"

static const char *TAG = "MAIN_APP";

#ifndef CONFIG_APP_PERF_AUTOTEST
#define CONFIG_APP_PERF_AUTOTEST 0
#endif

#ifndef CONFIG_APP_PERF_SECONDS_PER_TRACK
#define CONFIG_APP_PERF_SECONDS_PER_TRACK 60
#endif

#define DRAW_BUF_LINES 40
static uint16_t s_disp_buf1[LCD_WIDTH * DRAW_BUF_LINES];
static uint16_t s_disp_buf2[LCD_WIDTH * DRAW_BUF_LINES];

static SemaphoreHandle_t s_lvgl_mutex = NULL;
static volatile bool s_video_frame_ready = false;
static int s_active_track_idx = 0;
static bool s_need_track_switch = false;
static int s_pending_track_idx = 0;
static bool s_need_seek = false;
static int s_pending_seek_percent = 0;

static volatile bool s_req_set_view_mode = false;
static volatile view_mode_t s_target_view_mode = VIEW_MODE_FULLSCREEN;

static volatile float s_latest_fps = 30.0f;

static uint32_t my_tick_get_cb(void) {
    return (uint32_t)(esp_timer_get_time() / 1000);
}

static void lvgl_disp_flush_cb(lv_display_t *disp, const lv_area_t *area, uint8_t *px_map) {
    uint16_t *pixels = (uint16_t *)px_map;

    int64_t t0 = esp_timer_get_time();
    ili9488_8080_draw_bitmap(area->x1, area->y1, area->x2, area->y2, pixels);
    int64_t blit_us = esp_timer_get_time() - t0;
    perf_mark_blit((uint32_t)blit_us);

    view_mode_t vmode = spotify_ui_get_view_mode();
    if (vmode == VIEW_MODE_FULLSCREEN) {
        if (area->y2 >= 319) {
            perf_mark_presented();
        }
    } else {
        if (area->y2 >= (34 + 160 - 1) && area->y1 <= (34 + 160 - 1)) {
            perf_mark_presented();
        }
    }

    lv_display_flush_ready(disp);
}

static void lvgl_touch_read_cb(lv_indev_t *indev, lv_indev_data_t *data) {
    ft6236_touch_data_t touch;
    if (ft6236_i2c_read(&touch) == ESP_OK && touch.touched) {
        data->point.x = touch.x1;
        data->point.y = touch.y1;
        data->state = LV_INDEV_STATE_PRESSED;
    } else {
        data->state = LV_INDEV_STATE_RELEASED;
    }
}

// Callbacks desde la interfaz Spotify
static void on_track_changed_cb(int new_index) {
    s_pending_track_idx = new_index;
    s_need_track_switch = true;
}

static void on_playback_changed_cb(playback_state_t state) {
    if (state == PLAYBACK_STATE_STOPPED) {
        avi_player_restart();
    }
}

static void on_seek_requested_cb(int percent) {
    s_pending_seek_percent = percent;
    s_need_seek = true;
}

// -------------------------------------------------------------
// Tarea de Reproducción de Video (CPU Core 1)
// -------------------------------------------------------------
#if CONFIG_APP_PERF_AUTOTEST

static void video_engine_task(void *arg) {
    ESP_LOGI(TAG, "Tarea de autotest de rendimiento iniciada en CPU 1.");

    vTaskDelay(pdMS_TO_TICKS(500));

    int total_tracks = media_get_avi_count();
    int sec_per_track = CONFIG_APP_PERF_SECONDS_PER_TRACK;
    if (sec_per_track < 3) sec_per_track = 3;
    int sec_per_scenario = sec_per_track / 3;
    int64_t scenario_duration_us = (int64_t)sec_per_scenario * 1000000LL;

    const char *scenarios[3] = {"hidden", "osd", "seek"};

    for (int track_idx = 0; track_idx < total_tracks; track_idx++) {
        const char *avi_path = media_get_avi_path(track_idx);
        if (!avi_path) continue;

        ESP_LOGI(TAG, "Autotest: Abriendo Track %d: %s", track_idx, avi_path);
        if (avi_player_open(avi_path) != ESP_OK) {
            ESP_LOGE(TAG, "Fallo al abrir %s en autotest", avi_path);
            continue;
        }

        for (int s = 0; s < 3; s++) {
            const char *scn_name = scenarios[s];
            perf_set_scenario(track_idx, scn_name);
            ESP_LOGI(TAG, "Track %d -> Escenario '%s' (%d s)", track_idx, scn_name, sec_per_scenario);

            // Solicitar fullscreen al bucle GUI
            s_target_view_mode = VIEW_MODE_FULLSCREEN;
            s_req_set_view_mode = true;

            int64_t scn_start_time = esp_timer_get_time();
            int64_t last_seek_time = scn_start_time;
            int seek_count = 0;
            int64_t seek_interval_us = scenario_duration_us / 10;

            while (esp_timer_get_time() - scn_start_time < scenario_duration_us) {
                perf_report_if_due();

                // Escenario seek: 10 seeks aleatorios
                if (s == 2 && seek_count < 10) {
                    int64_t now_t = esp_timer_get_time();
                    if (now_t - last_seek_time >= seek_interval_us) {
                        last_seek_time = now_t;
                        int pct = (int)(esp_random() % 95);
                        avi_player_seek_percent(pct);
                        seek_count++;
                    }
                }

                uint16_t *target_buf = spotify_ui_get_fullscreen_buffer();
                int64_t t_start = esp_timer_get_time();
                esp_err_t ret = avi_player_read_next_frame(target_buf, 0);

                if (ret == ESP_OK) {
                    perf_mark_decoded();
                    spotify_ui_commit_frame();
                    s_video_frame_ready = true;

                    int64_t elapsed_us = esp_timer_get_time() - t_start;
                    const avi_info_t *info = avi_player_get_info();

                    int32_t delay_us = (int32_t)info->us_per_frame - (int32_t)elapsed_us;
                    if (delay_us > 1000) {
                        vTaskDelay(pdMS_TO_TICKS(delay_us / 1000));
                    } else {
                        vTaskDelay(1);
                    }
                } else if (ret == ESP_ERR_NOT_FOUND) {
                    // Reiniciar video para completar el tiempo del escenario
                    avi_player_restart();
                } else {
                    vTaskDelay(pdMS_TO_TICKS(5));
                }
            }
        }

        avi_player_close();
    }

    printf("AUTOTEST_DONE,tracks=%d\n", total_tracks);
    fflush(stdout);

    // Quedar en reposo
    while (1) {
        perf_report_if_due();
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

#else

static void video_engine_task(void *arg) {
    ESP_LOGI(TAG, "Tarea de motor de video SIMD (esp_new_jpeg) iniciada en CPU 1.");

    // Abrir primer video
    avi_player_open(g_playlist[s_active_track_idx].filepath);
    perf_set_scenario(s_active_track_idx, "normal");

    int frame_counter = 0;
    int64_t fps_window_start = esp_timer_get_time();

    while (1) {
        perf_report_if_due();

        // 1. Cambio de canción solicitado
        if (s_need_track_switch) {
            s_need_track_switch = false;
            s_active_track_idx = s_pending_track_idx;
            ESP_LOGI(TAG, "Cambiando a pista %d: %s", s_active_track_idx, g_playlist[s_active_track_idx].filepath);
            avi_player_open(g_playlist[s_active_track_idx].filepath);
            perf_set_scenario(s_active_track_idx, "normal");
            spotify_ui_set_play_state(PLAYBACK_STATE_PLAYING);
            frame_counter = 0;
            fps_window_start = esp_timer_get_time();
        }

        // 2. Búsqueda/Seek solicitada
        if (s_need_seek) {
            s_need_seek = false;
            avi_player_seek_percent(s_pending_seek_percent);
        }

        // 3. Decodificación de cuadros si está en estado PLAYING
        playback_state_t st = spotify_ui_get_play_state();
        if (st == PLAYBACK_STATE_PLAYING) {
            const avi_info_t *cur_info = avi_player_get_info();
            if (!cur_info->is_open) {
                static int64_t last_open_retry = 0;
                if (esp_timer_get_time() - last_open_retry > 1000000) {
                    last_open_retry = esp_timer_get_time();
                    if (sdcard_is_mounted()) {
                        avi_player_open(g_playlist[s_active_track_idx].filepath);
                        perf_set_scenario(s_active_track_idx, "normal");
                    } else {
                        sdcard_spi_init();
                    }
                }
                vTaskDelay(pdMS_TO_TICKS(50));
                continue;
            }

            view_mode_t vmode = spotify_ui_get_view_mode();
            uint8_t scale = (vmode == VIEW_MODE_STUDIO) ? 1 : 0;
            uint16_t *target_buf = (vmode == VIEW_MODE_STUDIO) ?
                                   spotify_ui_get_studio_buffer() :
                                   spotify_ui_get_fullscreen_buffer();

            int64_t t_start = esp_timer_get_time();
            esp_err_t ret = avi_player_read_next_frame(target_buf, scale);

            if (ret == ESP_OK) {
                perf_mark_decoded();
                spotify_ui_commit_frame();
                s_video_frame_ready = true;

                int64_t elapsed_us = esp_timer_get_time() - t_start;
                const avi_info_t *info = avi_player_get_info();

                frame_counter++;
                if (frame_counter >= 30) {
                    int64_t now = esp_timer_get_time();
                    int64_t window_us = now - fps_window_start;
                    if (window_us > 0) {
                        s_latest_fps = (frame_counter * 1000000.0f) / window_us;
                        ESP_LOGI(TAG, "[PERF] 30 Cuadros en %lld ms -> FPS REAL: %.1f | Ultimo decode: %lld ms",
                                 window_us / 1000, s_latest_fps, elapsed_us / 1000);
                    }
                    frame_counter = 0;
                    fps_window_start = now;
                }

                // Mantener cadencia de 30 FPS (33.3 ms por cuadro)
                int32_t delay_us = (int32_t)info->us_per_frame - (int32_t)elapsed_us;
                if (delay_us > 1000) {
                    vTaskDelay(pdMS_TO_TICKS(delay_us / 1000));
                } else {
                    vTaskDelay(1);
                }
            } else if (ret == ESP_ERR_NOT_FOUND) {
                ESP_LOGI(TAG, "Video finalizado. Avanzando a siguiente pista...");
                s_active_track_idx = (s_active_track_idx + 1) % PLAYLIST_SIZE;
                avi_player_open(g_playlist[s_active_track_idx].filepath);
                perf_set_scenario(s_active_track_idx, "normal");
                if (xSemaphoreTake(s_lvgl_mutex, pdMS_TO_TICKS(20)) == pdTRUE) {
                    spotify_ui_set_track(s_active_track_idx);
                    xSemaphoreGive(s_lvgl_mutex);
                }
            } else {
                vTaskDelay(pdMS_TO_TICKS(10));
            }
        } else {
            vTaskDelay(pdMS_TO_TICKS(50));
        }
    }
}

#endif

// -------------------------------------------------------------
// Función Principal app_main
// -------------------------------------------------------------
void app_main(void) {
    board_turn_off_rgb_led();

    ESP_LOGI(TAG, "==========================================================");
    ESP_LOGI(TAG, "   S3G4 LAB — REPRODUCTOR SPOTIFY VIDEO (30 FPS SIMD)");
    ESP_LOGI(TAG, "   Display: ILI9488 (8080 8-bit @ 16.0 MHz Overclock)");
    ESP_LOGI(TAG, "   Touch:   FT6236 Capacitivo (400 kHz Fast-Mode)");
    ESP_LOGI(TAG, "   Storage: MicroSD SPI @ 25 MHz (32 KB DMA Buffer)");
    ESP_LOGI(TAG, "   Codec:   esp_new_jpeg (Aceleración Vectorial SIMD ESP32-S3)");
    ESP_LOGI(TAG, "   GUI:     LVGL v9.5.0 (Spotify Dark Premium Aesthetic)");
    ESP_LOGI(TAG, "==========================================================");

    s_lvgl_mutex = xSemaphoreCreateMutex();

    // 1. Inicializar Hardware
    ESP_ERROR_CHECK(ili9488_8080_init_clock(16 * 1000 * 1000));
    ESP_ERROR_CHECK(ft6236_i2c_init());

    // 2. Inicializar MicroSD
    esp_err_t sd_err = sdcard_spi_init();
    if (sd_err != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al inicializar MicroSD. Verifique tarjeta y cableado.");
    } else {
        media_scan_sdcard();
    }

    // 3. Inicializar Decodificador AVI con esp_new_jpeg
    ESP_LOGI(TAG, "Iniciando decodificador SIMD esp_new_jpeg...");
    ESP_ERROR_CHECK(avi_player_init());

    // 4. Inicializar LVGL 9.5.0
    ESP_LOGI(TAG, "Inicializando LVGL 9.5.0...");
    lv_init();
    lv_tick_set_cb((lv_tick_get_cb_t)my_tick_get_cb);

    lv_display_t *disp = lv_display_create(LCD_WIDTH, LCD_HEIGHT);
    lv_display_set_color_format(disp, LV_COLOR_FORMAT_RGB565);
    lv_display_set_buffers(disp, s_disp_buf1, s_disp_buf2, sizeof(s_disp_buf1), LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(disp, lvgl_disp_flush_cb);

    lv_indev_t *indev = lv_indev_create();
    lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);
    lv_indev_set_read_cb(indev, lvgl_touch_read_cb);

    // 5. Inicializar Interfaz Spotify
    ESP_LOGI(TAG, "Iniciando interfaz Spotify...");
    spotify_ui_init(on_track_changed_cb, on_playback_changed_cb, on_seek_requested_cb);

    // 6. Lanzar Tarea de Video en Core 1 (Stack 16 KB)
    ESP_LOGI(TAG, "Creando tarea de video en Core 1...");
    BaseType_t t_res = xTaskCreatePinnedToCore(video_engine_task, "video_task", 16 * 1024, NULL, 5, NULL, 1);
    assert(t_res == pdPASS);

    // 7. Bucle Principal de la GUI (Core 0)
    ESP_LOGI(TAG, "Iniciando bucle de interfaz GUI...");
    int64_t last_progress_update = 0;
    int64_t last_eq_tick = 0;
    int64_t last_fps_ui_update = 0;

    while (1) {
        if (xSemaphoreTake(s_lvgl_mutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            if (s_req_set_view_mode) {
                s_req_set_view_mode = false;
                spotify_ui_set_view_mode(s_target_view_mode);
            }

            if (s_video_frame_ready) {
                s_video_frame_ready = false;
                spotify_ui_invalidate_video();
            }

            uint32_t delay_ms = lv_timer_handler();
            int64_t now = esp_timer_get_time();

            // Animación de ecualizador cada 80 ms
            if (now - last_eq_tick >= 80000) {
                last_eq_tick = now;
                spotify_ui_tick();
            }

            // Actualizar progreso cada 250 ms
            if (now - last_progress_update >= 250000) {
                last_progress_update = now;
                const avi_info_t *info = avi_player_get_info();
                if (info->is_open && info->total_frames > 0) {
                    int pct = (int)((info->current_frame * 100) / info->total_frames);
                    spotify_ui_update_progress(info->elapsed_sec, info->duration_sec, pct);
                }
            }

            // Actualizar badge de FPS en UI cada 500 ms
            if (now - last_fps_ui_update >= 500000) {
                last_fps_ui_update = now;
                spotify_ui_update_fps(s_latest_fps);
            }

            xSemaphoreGive(s_lvgl_mutex);
            if (delay_ms > 10) delay_ms = 10;
            vTaskDelay(pdMS_TO_TICKS(delay_ms ? delay_ms : 5));
        } else {
            vTaskDelay(pdMS_TO_TICKS(5));
        }
    }
}
