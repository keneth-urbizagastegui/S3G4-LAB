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

static bool s_synthetic_touch_active = false;
static touch_sample_t s_synthetic_touch = {0};

void touch_inject_synthetic(uint16_t x, uint16_t y, bool pressed) {
    portENTER_CRITICAL(&s_touch_mux);
    s_synthetic_touch_active = pressed;
    s_synthetic_touch.x = x;
    s_synthetic_touch.y = y;
    s_synthetic_touch.pressed = pressed;
    s_synthetic_touch.timestamp_us = esp_timer_get_time();
    s_shared_touch = s_synthetic_touch;
    portEXIT_CRITICAL(&s_touch_mux);
}

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
        if (s_synthetic_touch_active) {
            s_shared_touch = s_synthetic_touch;
        } else if (ret == ESP_OK && touch.touched) {
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
// Peticiones asíncronas a UI (X3: SOLO gui_task llama lv_* y spotify_ui_*)
// -------------------------------------------------------------
typedef enum {
    UI_REQ_SET_VIEW,
    UI_REQ_SET_HUD,
} ui_req_type_t;

typedef struct {
    ui_req_type_t type;
    int arg;
} ui_req_t;

static QueueHandle_t s_ui_req_queue = NULL;

__attribute__((unused)) static bool ui_req_send(ui_req_type_t type, int arg) {
    if (!s_ui_req_queue) return false;
    ui_req_t req = {.type = type, .arg = arg};
    return (xQueueSend(s_ui_req_queue, &req, pdMS_TO_TICKS(50)) == pdPASS);
}

// -------------------------------------------------------------
// Estado real de UI publicado atómicamente por gui_task (X1, X4)
// -------------------------------------------------------------
typedef struct {
    char title[64];
    int track_index;
    view_mode_t view_mode;
    int hud_visible; // 0 = hidden, 1 = visible
    uint32_t version;
} ui_published_state_t;

static ui_published_state_t s_published_ui = {
    .title = "",
    .track_index = 0,
    .view_mode = VIEW_MODE_STUDIO,
    .hud_visible = 0,
    .version = 0,
};
static portMUX_TYPE s_ui_pub_mux = portMUX_INITIALIZER_UNLOCKED;

static void publish_ui_state(void) {
    char title[64] = {0};
    int trk = 0;
    view_mode_t vm = VIEW_MODE_STUDIO;
    int hud = 0;
    spotify_ui_get_published_info(title, sizeof(title), &trk, &vm, &hud);

    portENTER_CRITICAL(&s_ui_pub_mux);
    snprintf(s_published_ui.title, sizeof(s_published_ui.title), "%s", title);
    s_published_ui.track_index = trk;
    s_published_ui.view_mode = vm;
    s_published_ui.hud_visible = hud;
    s_published_ui.version++;
    portEXIT_CRITICAL(&s_ui_pub_mux);
}

void ui_get_published_state(char *title_buf, size_t max_len, int *track_idx, view_mode_t *vmode, int *hud_vis) {
    portENTER_CRITICAL(&s_ui_pub_mux);
    if (title_buf && max_len > 0) {
        snprintf(title_buf, max_len, "%s", s_published_ui.title);
    }
    if (track_idx) *track_idx = s_published_ui.track_index;
    if (vmode) *vmode = s_published_ui.view_mode;
    if (hud_vis) *hud_vis = s_published_ui.hud_visible;
    portEXIT_CRITICAL(&s_ui_pub_mux);
}

void perf_get_ui_state(char *out_view, size_t max_len, int *out_hud) {
    portENTER_CRITICAL(&s_ui_pub_mux);
    if (out_view && max_len > 0) {
        const char *vstr = (s_published_ui.view_mode == VIEW_MODE_FULLSCREEN) ? "full" : "studio";
        snprintf(out_view, max_len, "%s", vstr);
    }
    if (out_hud) {
        *out_hud = s_published_ui.hud_visible;
    }
    portEXIT_CRITICAL(&s_ui_pub_mux);
}

// -------------------------------------------------------------
// Timer periódico de LVGL (Núcleo 0, cada 100 ms)
// -------------------------------------------------------------
static void ui_refresh_timer_cb(lv_timer_t *timer) {
    player_status_t status;
    player_get_status(&status);
    spotify_ui_update_from_status(&status);
    publish_ui_state();
}

// -------------------------------------------------------------
// Tarea GUI principal (Núcleo 0, prioridad 4)
// -------------------------------------------------------------
static void gui_task(void *arg) {
    ESP_LOGI(TAG, "Iniciando gui_task en Core 0...");

    s_ui_req_queue = xQueueCreate(8, sizeof(ui_req_t));
    assert(s_ui_req_queue != NULL);

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

    // Publicar estado inicial
    publish_ui_state();

#ifndef CONFIG_APP_UI_REFRESH_MS
#define CONFIG_APP_UI_REFRESH_MS 250
#endif
    // Timer de refresco periódico desde player_get_status (Obs O1: CONFIG_APP_UI_REFRESH_MS)
    lv_timer_create(ui_refresh_timer_cb, CONFIG_APP_UI_REFRESH_MS, NULL);

    ESP_LOGI(TAG, "Bucle de eventos GUI LVGL iniciado en Core 0 (refresh: %d ms).", CONFIG_APP_UI_REFRESH_MS);
    while (1) {
        // 1. Consumir peticiones UI antes de lv_timer_handler (X3)
        ui_req_t req;
        while (xQueueReceive(s_ui_req_queue, &req, 0) == pdPASS) {
            if (req.type == UI_REQ_SET_VIEW) {
                spotify_ui_set_view_mode((view_mode_t)req.arg);
            } else if (req.type == UI_REQ_SET_HUD) {
                spotify_ui_set_hud_forced(req.arg);
            }
            publish_ui_state();
        }

        // 2. Traspaso atómico de fotograma decodificado
        uint16_t *frame_buf = NULL;
        int frame_w = 0, frame_h = 0;
        if (player_check_and_clear_new_frame(&frame_buf, &frame_w, &frame_h)) {
            if (spotify_ui_display_frame(frame_buf, frame_w, frame_h)) {
                s_present_pending = true;
            }
        }

        // 3. Ejecutar handler de LVGL
        uint32_t delay_ms = lv_timer_handler();

        // 4. Publicar estado UI actualizado
        publish_ui_state();

        // Regla F1: no dormir más de 5 ms entre lv_timer_handler
        if (delay_ms > 5) delay_ms = 5;
        vTaskDelay(pdMS_TO_TICKS(delay_ms ? delay_ms : 1));
    }
}

static TaskHandle_t s_touch_task_handle = NULL;
static TaskHandle_t s_gui_task_handle = NULL;
static TaskHandle_t s_autotest_task_handle = NULL;

static void log_stack_and_heap_diag(const char *phase_tag) {
    UBaseType_t touch_free = s_touch_task_handle ? uxTaskGetStackHighWaterMark(s_touch_task_handle) : 0;
    UBaseType_t gui_free = s_gui_task_handle ? uxTaskGetStackHighWaterMark(s_gui_task_handle) : 0;
    uint32_t player_free = player_get_task_stack_high_water_mark();
    UBaseType_t auto_free = s_autotest_task_handle ? uxTaskGetStackHighWaterMark(s_autotest_task_handle) : 0;
    uint32_t heap_int = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    uint32_t heap_psram = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_SPIRAM);

    ESP_LOGI(TAG, "DIAG_HEAP [%s]: int=%lu, psram=%lu | STACK_FREE: touch=%u, gui=%u, player=%lu, auto=%u",
             phase_tag, (unsigned long)heap_int, (unsigned long)heap_psram,
             (unsigned int)touch_free, (unsigned int)gui_free, (unsigned long)player_free, (unsigned int)auto_free);
    heap_caps_print_heap_info(MALLOC_CAP_INTERNAL);
}

// -------------------------------------------------------------
// Autotest F2 (si CONFIG_APP_PERF_AUTOTEST=1)
// -------------------------------------------------------------
#if CONFIG_APP_PERF_AUTOTEST

static void autotest_task(void *arg) {
    ESP_LOGI(TAG, "Tarea de autotest F2 iniciada (usa cola de comandos y peticiones UI).");

    vTaskDelay(pdMS_TO_TICKS(1000));
    log_stack_and_heap_diag("AUTOTEST_START");

    int total_tracks = media_get_avi_count();
    int sec_per_track = CONFIG_APP_PERF_SECONDS_PER_TRACK;
    if (sec_per_track < 3) sec_per_track = 3;
    int sec_per_scenario = sec_per_track / 3;

    const char *scenarios[3] = {"hidden", "osd", "seek"};

    for (int track_idx = 0; track_idx < total_tracks; track_idx++) {
        ESP_LOGI(TAG, "Autotest: Abriendo Track %d via PCMD_OPEN", track_idx);
        player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = track_idx};
        player_cmd_send(&cmd_open);

        // X1: Al empezar cada track pedir a gui_task VIEW_MODE_FULLSCREEN + PCMD_SET_VIDEO_RECT {0,0,480,320}
        ui_req_send(UI_REQ_SET_VIEW, VIEW_MODE_FULLSCREEN);
        player_cmd_t cmd_rect = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
        player_cmd_send(&cmd_rect);

        // Esperar confirmación de que la UI pasó a FULLSCREEN
        for (int w = 0; w < 50; w++) {
            view_mode_t vm = VIEW_MODE_STUDIO;
            ui_get_published_state(NULL, 0, NULL, &vm, NULL);
            if (vm == VIEW_MODE_FULLSCREEN) break;
            vTaskDelay(pdMS_TO_TICKS(10));
        }

        vTaskDelay(pdMS_TO_TICKS(400));

        for (int s = 0; s < 3; s++) {
            const char *scn_name = scenarios[s];

            // X1 & X3: hidden = HUD forzado oculto (1); osd = HUD forzado visible (2); seek = oculto (1)
            int hud_req = (s == 1) ? 2 : 1;
            ui_req_send(UI_REQ_SET_HUD, hud_req);

            int expected_hud = (s == 1) ? 1 : 0;
            for (int w = 0; w < 50; w++) {
                view_mode_t vm = VIEW_MODE_STUDIO;
                int hud_vis = -1;
                ui_get_published_state(NULL, 0, NULL, &vm, &hud_vis);
                if (vm == VIEW_MODE_FULLSCREEN && hud_vis == expected_hud) break;
                vTaskDelay(pdMS_TO_TICKS(10));
            }

            perf_set_scenario(track_idx, scn_name);
            ESP_LOGI(TAG, "Track %d -> Escenario '%s' (%d s, view=full, hud=%d)",
                     track_idx, scn_name, sec_per_scenario, expected_hud);

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

    // Escenario TAP de verificacion Bug T2
    ESP_LOGI(TAG, "Iniciando escenario TAP (Bug T2)...");
    perf_set_scenario(0, "tap");
    ui_req_send(UI_REQ_SET_VIEW, VIEW_MODE_FULLSCREEN);
    ui_req_send(UI_REQ_SET_HUD, 1); // forzar oculto
    vTaskDelay(pdMS_TO_TICKS(300));

    // Cambiar HUD a modo AUTO (0)
    ui_req_send(UI_REQ_SET_HUD, 0);
    vTaskDelay(pdMS_TO_TICKS(150));

    int hud_before = -1;
    ui_get_published_state(NULL, 0, NULL, NULL, &hud_before);

    // Inyectar toque sintético en el centro (240, 160) durante 80 ms
    touch_inject_synthetic(240, 160, true);
    vTaskDelay(pdMS_TO_TICKS(80));
    touch_inject_synthetic(240, 160, false);

    // Esperar a que gui_task procese el toque y actualice hud a 1 (hasta 600 ms)
    int hud_after = -1;
    int64_t tap_t0 = esp_timer_get_time();
    while (esp_timer_get_time() - tap_t0 < 600000LL) {
        vTaskDelay(pdMS_TO_TICKS(20));
        ui_get_published_state(NULL, 0, NULL, NULL, &hud_after);
        if (hud_after == 1) break;
    }

    printf("TAP,hud_before=%d,hud_after=%d\n", hud_before, hud_after);
    fflush(stdout);

    // Escenario STRESS final: 20 cambios de pista y 50 saltos SEEK simulando arrastre
    ESP_LOGI(TAG, "Iniciando escenario final de STRESS...");
    perf_set_scenario(0, "stress");

    int changes_count = 0;
    int seeks_count = 0;
    int title_mismatch_count = 0;
    int64_t title_wait_ms_max = 0;

    // 20 cambios de pista (PCMD_NEXT/PREV alternados cada 500 ms)
    for (int i = 0; i < 20; i++) {
        player_cmd_type_t ctype = (i % 2 == 0) ? PCMD_NEXT : PCMD_PREV;
        player_cmd_t cmd = {.type = ctype};
        player_cmd_send(&cmd);
        changes_count++;

        vTaskDelay(pdMS_TO_TICKS(500));
        perf_report_if_due();

        // X4: Esperar hasta 600 ms a que el titulo publicado por la UI coincida con player_get_track_title(status.track_index)
        int64_t t0 = esp_timer_get_time();
        bool matched = false;
        char expected_title[64] = {0};
        char ui_title[64] = {0};

        while ((esp_timer_get_time() - t0) < 600000LL) {
            player_status_t st;
            player_get_status(&st);
            player_get_track_title(st.track_index, expected_title, sizeof(expected_title));

            ui_get_published_state(ui_title, sizeof(ui_title), NULL, NULL, NULL);

            if (strlen(ui_title) > 0 && strcmp(ui_title, expected_title) == 0) {
                matched = true;
                break;
            }
            vTaskDelay(pdMS_TO_TICKS(10));
        }

        int64_t wait_ms = (esp_timer_get_time() - t0) / 1000;
        if (wait_ms > title_wait_ms_max) {
            title_wait_ms_max = wait_ms;
        }

        if (!matched) {
            title_mismatch_count++;
            ESP_LOGW(TAG, "Mismatch en cambio %d tras %lld ms: esperado='%s', UI='%s'",
                     i, (long long)wait_ms, expected_title, ui_title);
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

        // X4: Esperar hasta 600 ms comprobando consistencia con UI publicada
        int64_t t0 = esp_timer_get_time();
        bool matched = false;
        char expected_title[64] = {0};
        char ui_title[64] = {0};

        while ((esp_timer_get_time() - t0) < 600000LL) {
            player_get_status(&st);
            player_get_track_title(st.track_index, expected_title, sizeof(expected_title));

            ui_get_published_state(ui_title, sizeof(ui_title), NULL, NULL, NULL);

            if (strlen(ui_title) > 0 && strcmp(ui_title, expected_title) == 0) {
                matched = true;
                break;
            }
            vTaskDelay(pdMS_TO_TICKS(10));
        }

        int64_t wait_ms = (esp_timer_get_time() - t0) / 1000;
        if (wait_ms > title_wait_ms_max) {
            title_wait_ms_max = wait_ms;
        }

        if (!matched) {
            title_mismatch_count++;
            ESP_LOGW(TAG, "Mismatch en seek %d tras %lld ms: esperado='%s', UI='%s'",
                     i, (long long)wait_ms, expected_title, ui_title);
        }
    }

    printf("STRESS,changes=%d,seeks=%d,title_mismatch=%d,title_wait_ms_max=%lld\n",
           changes_count, seeks_count, title_mismatch_count, (long long)title_wait_ms_max);
    fflush(stdout);

    log_stack_and_heap_diag("AUTOTEST_END");

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
    ESP_LOGI(TAG, "   S3G4 LAB — REPRODUCTOR DE VIDEO FASE 2 (PTS / CADENCIA)");
    ESP_LOGI(TAG, "   Display: ILI9488 (8080 8-bit @ 16.0 MHz)");
    ESP_LOGI(TAG, "   Touch:   FT6236 Capacitivo (Desacoplado, sondeo 10 ms)");
    ESP_LOGI(TAG, "   Storage: MicroSD SPI @ 20 MHz (32 KB Buffer)");
    ESP_LOGI(TAG, "   Core 1:  player_task (Motor video + cola comandos + PTS)");
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

    // 5. Lanzar tarea táctil en Core 0 (prioridad 6, ajustada a 3584 tras medir uso de 1288 B)
    BaseType_t t_touch = xTaskCreatePinnedToCore(touch_task, "touch_task", 3584, NULL, 6, &s_touch_task_handle, 0);
    assert(t_touch == pdPASS);

    // 6. Lanzar tarea GUI en Core 0 (prioridad 4)
    BaseType_t t_gui = xTaskCreatePinnedToCore(gui_task, "gui_task", 8192, NULL, 4, &s_gui_task_handle, 0);
    assert(t_gui == pdPASS);

#if CONFIG_APP_PERF_AUTOTEST
    // 7. Lanzar tarea de autotest (prioridad 3, ajustada a 4608 tras medir uso de 2400 B)
    BaseType_t t_auto = xTaskCreatePinnedToCore(autotest_task, "autotest_task", 4608, NULL, 3, &s_autotest_task_handle, 0);
    assert(t_auto == pdPASS);
#endif

    log_stack_and_heap_diag("POST_INIT");
    ESP_LOGI(TAG, "app_main inicializacion completada.");
}
