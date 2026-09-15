#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/portmacro.h"
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
#include "player.h"
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

static volatile bool s_present_pending = false;

// Estructura compartida para el sondeo desacoplado del táctil FT6236 (T1)
typedef struct {
    uint16_t x;
    uint16_t y;
    bool pressed;
    int64_t timestamp_us;
} touch_sample_t;

static touch_sample_t s_shared_touch = {0};
static portMUX_TYPE s_touch_mux = portMUX_INITIALIZER_UNLOCKED;

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
    int last_canvas_row = (vmode == VIEW_MODE_FULLSCREEN) ? 319 : (34 + 160 - 1);
    if (s_present_pending && area->y2 >= last_canvas_row) {
        perf_mark_presented();
        s_present_pending = false;
    }

    lv_display_flush_ready(disp);
}

// Callback de lectura de LVGL: SOLO copia la estructura protegida por spinlock (sin I2C)
static void lvgl_touch_read_cb(lv_indev_t *indev, lv_indev_data_t *data) {
    portENTER_CRITICAL(&s_touch_mux);
    touch_sample_t sample = s_shared_touch;
    portEXIT_CRITICAL(&s_touch_mux);

    int64_t now = esp_timer_get_time();
    int64_t age_us = (sample.timestamp_us > 0 && now >= sample.timestamp_us) ? (now - sample.timestamp_us) : 0;
    perf_mark_touch_age((uint32_t)age_us);

    if (sample.pressed) {
        data->point.x = sample.x;
        data->point.y = sample.y;
        data->state = LV_INDEV_STATE_PRESSED;
    } else {
        data->state = LV_INDEV_STATE_RELEASED;
    }
}

// -------------------------------------------------------------
// Tarea táctil desacoplada (Núcleo 0, prioridad 6 > gui_task, cada 10 ms)
// -------------------------------------------------------------
static void touch_task(void *arg) {
    ESP_LOGI(TAG, "Tarea touch_task iniciada en Core 0 (prioridad 6, intervalo 10 ms).");
    ft6236_touch_data_t touch;

    while (1) {
        int64_t t0 = esp_timer_get_time();
        esp_err_t ret = ft6236_i2c_read(&touch);
        int64_t t1 = esp_timer_get_time();
        uint32_t rd_us = (uint32_t)(t1 - t0);
        perf_mark_touch_read(rd_us);

        portENTER_CRITICAL(&s_touch_mux);
        if (ret == ESP_OK && touch.touched) {
            s_shared_touch.x = touch.x1;
            s_shared_touch.y = touch.y1;
            s_shared_touch.pressed = true;
        } else {
            s_shared_touch.pressed = false;
        }
        s_shared_touch.timestamp_us = t1;
        portEXIT_CRITICAL(&s_touch_mux);

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// -------------------------------------------------------------
// Timer periódico de LVGL (Núcleo 0, cada 200 ms)
// -------------------------------------------------------------
static void ui_refresh_timer_cb(lv_timer_t *timer) {
    player_status_t status;
    player_get_status(&status);
    spotify_ui_update_from_status(&status);
}

// -------------------------------------------------------------
// Tarea GUI principal (Núcleo 0, prioridad 4)
// -------------------------------------------------------------
static void gui_task(void *arg) {
    ESP_LOGI(TAG, "Iniciando gui_task en Core 0...");

    lv_init();
    lv_tick_set_cb((lv_tick_get_cb_t)my_tick_get_cb);

    lv_display_t *disp = lv_display_create(LCD_WIDTH, LCD_HEIGHT);
    lv_display_set_color_format(disp, LV_COLOR_FORMAT_RGB565);
    lv_display_set_buffers(disp, s_disp_buf1, s_disp_buf2, sizeof(s_disp_buf1), LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(disp, lvgl_disp_flush_cb);

    lv_indev_t *indev = lv_indev_create();
    lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);
    lv_indev_set_read_cb(indev, lvgl_touch_read_cb);

    // Callbacks dummy para spotify_ui_init (la UI envía los comandos internamente)
    spotify_ui_init(NULL, NULL, NULL);

    // Timer de refresco periódico desde player_get_status (200 ms)
    lv_timer_create(ui_refresh_timer_cb, 200, NULL);

    ESP_LOGI(TAG, "Bucle de eventos GUI LVGL iniciado en Core 0.");
    while (1) {
        // Traspaso atómico de fotograma decodificado
        uint16_t *frame_buf = NULL;
        int frame_w = 0, frame_h = 0;
        if (player_check_and_clear_new_frame(&frame_buf, &frame_w, &frame_h)) {
            s_present_pending = true;
            spotify_ui_display_frame(frame_buf, frame_w, frame_h);
        }

        uint32_t delay_ms = lv_timer_handler();
        // Regla F1: no dormir más de 5 ms entre lv_timer_handler
        if (delay_ms > 5) delay_ms = 5;
        vTaskDelay(pdMS_TO_TICKS(delay_ms ? delay_ms : 1));
    }
}

// -------------------------------------------------------------
// Autotest F1 (si CONFIG_APP_PERF_AUTOTEST=1)
// -------------------------------------------------------------
#if CONFIG_APP_PERF_AUTOTEST

static void autotest_task(void *arg) {
    ESP_LOGI(TAG, "Tarea de autotest F1 iniciada (usa cola de comandos player_cmd_send).");

    vTaskDelay(pdMS_TO_TICKS(1000));

    int total_tracks = media_get_avi_count();
    int sec_per_track = CONFIG_APP_PERF_SECONDS_PER_TRACK;
    if (sec_per_track < 3) sec_per_track = 3;
    int sec_per_scenario = sec_per_track / 3;

    const char *scenarios[3] = {"hidden", "osd", "seek"};

    for (int track_idx = 0; track_idx < total_tracks; track_idx++) {
        ESP_LOGI(TAG, "Autotest: Abriendo Track %d via PCMD_OPEN", track_idx);
        player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = track_idx};
        player_cmd_send(&cmd_open);

        vTaskDelay(pdMS_TO_TICKS(500));

        for (int s = 0; s < 3; s++) {
            const char *scn_name = scenarios[s];
            perf_set_scenario(track_idx, scn_name);
            ESP_LOGI(TAG, "Track %d -> Escenario '%s' (%d s)", track_idx, scn_name, sec_per_scenario);

            // Configurar HUD: hidden=1, osd=2, seek=1
            spotify_ui_set_hud_forced((s == 1) ? 2 : 1);

            int64_t scn_start_time = esp_timer_get_time();
            int64_t scenario_duration_us = (int64_t)sec_per_scenario * 1000000LL;
            int64_t seek_interval_us = scenario_duration_us / 10;
            int64_t last_seek_time = scn_start_time;
            int seek_count = 0;

            while (esp_timer_get_time() - scn_start_time < scenario_duration_us) {
                perf_report_if_due();

                // Escenario seek: 10 saltos aleatorios
                if (s == 2 && seek_count < 10) {
                    int64_t now_t = esp_timer_get_time();
                    if (now_t - last_seek_time >= seek_interval_us) {
                        last_seek_time = now_t;
                        player_status_t st;
                        player_get_status(&st);
                        int64_t dur = (int64_t)st.dur_ms;
                        if (dur <= 0) dur = 100000;
                        int pct = (int)(esp_random() % 95);
                        int32_t seek_ms = (int32_t)((dur * pct) / 100);
                        player_cmd_t cmd_seek = {.type = PCMD_SEEK_MS, .arg = seek_ms};
                        player_cmd_send(&cmd_seek);
                        seek_count++;
                    }
                }

                vTaskDelay(pdMS_TO_TICKS(100));
            }
        }
    }

    // Escenario STRESS final: 20 cambios de pista y 50 saltos SEEK simulando arrastre
    ESP_LOGI(TAG, "Iniciando escenario final de STRESS...");
    perf_set_scenario(0, "stress");

    int changes_count = 0;
    int seeks_count = 0;
    int title_mismatch_count = 0;

    // 20 cambios de pista (PCMD_NEXT/PREV alternados cada 500 ms)
    for (int i = 0; i < 20; i++) {
        player_cmd_type_t ctype = (i % 2 == 0) ? PCMD_NEXT : PCMD_PREV;
        player_cmd_t cmd = {.type = ctype};
        player_cmd_send(&cmd);
        changes_count++;

        vTaskDelay(pdMS_TO_TICKS(500));
        perf_report_if_due();

        player_status_t st;
        player_get_status(&st);
        char expected_title[64] = {0};
        player_get_track_title(st.track_index, expected_title, sizeof(expected_title));

        if (strcmp(st.title, expected_title) != 0) {
            title_mismatch_count++;
            ESP_LOGW(TAG, "Mismatch en cambio %d: pista=%d, esperado='%s', obtenido='%s'",
                     i, (int)st.track_index, expected_title, st.title);
        }
    }

    // 50 PCMD_SEEK_MS cada 100 ms (simulando arrastre continuo)
    for (int i = 0; i < 50; i++) {
        player_status_t st;
        player_get_status(&st);
        int64_t dur = (int64_t)st.dur_ms;
        if (dur <= 0) dur = 100000;
        int pct = ((i * 3) % 90) + 5;
        int32_t seek_ms = (int32_t)((dur * pct) / 100);

        player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = seek_ms};
        player_cmd_send(&cmd);
        seeks_count++;

        vTaskDelay(pdMS_TO_TICKS(100));
        perf_report_if_due();

        player_get_status(&st);
        char expected_title[64] = {0};
        player_get_track_title(st.track_index, expected_title, sizeof(expected_title));

        if (strcmp(st.title, expected_title) != 0) {
            title_mismatch_count++;
            ESP_LOGW(TAG, "Mismatch en seek %d: pista=%d, esperado='%s', obtenido='%s'",
                     i, (int)st.track_index, expected_title, st.title);
        }
    }

    printf("STRESS,changes=%d,seeks=%d,title_mismatch=%d\n", changes_count, seeks_count, title_mismatch_count);
    fflush(stdout);

    printf("AUTOTEST_DONE,tracks=%d\n", total_tracks);
    fflush(stdout);

    while (1) {
        perf_report_if_due();
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

#endif

// -------------------------------------------------------------
// Función Principal app_main (Solo inicializa y lanza tareas)
// -------------------------------------------------------------
void app_main(void) {
    board_turn_off_rgb_led();

    ESP_LOGI(TAG, "==========================================================");
    ESP_LOGI(TAG, "   S3G4 LAB — REPRODUCTOR DE VIDEO FASE 1 (CONCURRENCIA)");
    ESP_LOGI(TAG, "   Display: ILI9488 (8080 8-bit @ 16.0 MHz)");
    ESP_LOGI(TAG, "   Touch:   FT6236 Capacitivo (Desacoplado, sondeo 10 ms)");
    ESP_LOGI(TAG, "   Storage: MicroSD SPI @ 20 MHz (32 KB Buffer)");
    ESP_LOGI(TAG, "   Core 1:  player_task (Motor video + cola comandos)");
    ESP_LOGI(TAG, "   Core 0:  gui_task (LVGL) + touch_task");
    ESP_LOGI(TAG, "==========================================================");

    perf_init();

    // 1. Inicializar Hardware
    ESP_ERROR_CHECK(ili9488_8080_init_clock(16 * 1000 * 1000));
    ESP_ERROR_CHECK(ft6236_i2c_init());

    // 2. Inicializar MicroSD y escanear medios
    esp_err_t sd_err = sdcard_spi_init();
    if (sd_err != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al inicializar MicroSD.");
    } else {
        media_scan_sdcard();
    }

    // 3. Inicializar decodificador de video
    ESP_ERROR_CHECK(avi_player_init());

    // 4. Lanzar motor de reproducción en Core 1
    ESP_ERROR_CHECK(player_start());

    // 5. Lanzar tarea táctil en Core 0 (prioridad 6)
    BaseType_t t_touch = xTaskCreatePinnedToCore(touch_task, "touch_task", 4096, NULL, 6, NULL, 0);
    assert(t_touch == pdPASS);

    // 6. Lanzar tarea GUI en Core 0 (prioridad 4)
    BaseType_t t_gui = xTaskCreatePinnedToCore(gui_task, "gui_task", 8192, NULL, 4, NULL, 0);
    assert(t_gui == pdPASS);

#if CONFIG_APP_PERF_AUTOTEST
    // 7. Lanzar tarea de autotest (prioridad 3)
    BaseType_t t_auto = xTaskCreatePinnedToCore(autotest_task, "autotest_task", 6144, NULL, 3, NULL, 0);
    assert(t_auto == pdPASS);
#endif

    ESP_LOGI(TAG, "app_main inicializacion completada.");
}
