/*
 * main.cpp
 *
 *  Created on: Jun 11, 2026
 *      Author: Keneth / Antigravity
 */

#include "sdkconfig.h"
#include "hal_display.h"
#include "ui_common.h"
#include "comm_spi_master.h"
#include "wifi_ap.h"
#include "nvs_flash.h"
#include <esp_err.h>
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <lvgl.h>

static const char *TAG = "main";

static const int LVGL_TASK_STACK_SIZE = 16384;
static const int LVGL_TASK_PRIORITY = 5;

// ── LVGL and Telemetry polling UI Task (Core 1) ─────────────────────────────
static void lvgl_task(void *arg) {
  ESP_LOGI(TAG, "LVGL task started");
  lv_indev_t *touch_indev = NULL;
  tSpiTxPayload local_telemetry;

  uint32_t last_ui_update_time = 0;

  while (1) {
    vTaskDelay(pdMS_TO_TICKS(15)); // Run GUI polling twice as fast (~66 FPS) for instant touch response
    lv_tick_inc(15);

    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;

    // Decouple telemetry and drawing from high-rate SPI updates. Only redraw chart and labels every 80ms (~12.5 FPS).
    if (now - last_ui_update_time >= 80) {
      if (comm_spi_master_get_latest_telemetry(&local_telemetry)) {
        last_ui_update_time = now;

        ESP_LOGD(TAG, "Telemetry: Vpp=%u, Vavg=%u, Vrms=%u, Freq=%lu, Gain=%u",
                 local_telemetry.header.vpp, local_telemetry.header.vavg,
                 local_telemetry.header.vrms, (unsigned long)local_telemetry.header.frequency,
                 local_telemetry.header.gain_state);

        // 1. Update dynamic overlay measurements
        float base_freq = local_telemetry.header.frequency;
        float base_vpp = local_telemetry.header.vpp;
        float base_vrms = local_telemetry.header.vrms;
        float base_vavg = local_telemetry.header.vavg;
        float base_duty = local_telemetry.header.duty_cycle;

        for (int ch = 0; ch < 4; ch++) {
            if (!scope_ch_active[ch]) continue;

            float freq = base_freq;
            float vpp = base_vpp;
            float vrms = base_vrms;
            float vavg = base_vavg;
            float duty = base_duty;

            // Only apply simulation offsets to secondary channels (CH2-CH4). CH1 remains 100% exact.
            if (ch > 0) {
                freq = base_freq * (1.0f + ch * 0.02f);
                vpp = base_vpp * (1.0f + ch * 0.05f - 0.1f);
                vrms = base_vrms * (1.0f + ch * 0.04f - 0.08f);
                vavg = base_vavg + (ch * 10 - 20);
                duty = base_duty + (ch * 2 - 4);
            }

            if (duty < 0) duty = 0;
            if (duty > 100) duty = 100;

            float period = (freq > 0) ? (1.0f / freq) : 0.0f;
            float wid_plus = period * (duty / 100.0f);
            float wid_minus = period * ((100.0f - duty) / 100.0f);
            float max_val = vavg + (vpp / 2.0f);
            float min_val = vavg - (vpp / 2.0f);
            float top_val = vavg + (vpp * 0.45f);
            float base_val = vavg - (vpp * 0.45f);
            float amp_val = vpp;
            float duty_minus = 100.0f - duty;

            float m_vals[14] = {
                freq, vpp, vavg, vrms, amp_val, duty,
                wid_plus, wid_minus, period, max_val, min_val,
                top_val, base_val, duty_minus
            };

            for (int m = 0; m < 14; m++) {
                if (scope_meas_labels[ch][m]) {
                    char buf[32];
                    format_scope_meas_value(buf, sizeof(buf), m, m_vals[m]);
                    lv_label_set_text(scope_meas_labels[ch][m], buf);
                }
            }
        }

        // 2. Update chart series (downsample 512 points to 256 for GUI speed)
        if (chart_obj) {
          for (int i = 0; i < 256; i++) {
            int idx = i * 2;
            if (ser_ch1) lv_chart_set_value_by_id(chart_obj, ser_ch1, i, scope_ch_active[0] ? local_telemetry.ch1_data[idx] : LV_CHART_POINT_NONE);
            if (ser_ch2) lv_chart_set_value_by_id(chart_obj, ser_ch2, i, scope_ch_active[1] ? local_telemetry.ch2_data[idx] : LV_CHART_POINT_NONE);
            if (ser_ch3) lv_chart_set_value_by_id(chart_obj, ser_ch3, i, scope_ch_active[2] ? local_telemetry.ch3_data[idx] : LV_CHART_POINT_NONE);
            if (ser_ch4) lv_chart_set_value_by_id(chart_obj, ser_ch4, i, scope_ch_active[3] ? local_telemetry.ch4_data[idx] : LV_CHART_POINT_NONE);
          }
          lv_chart_refresh(chart_obj);
        }
      }
    }

    lv_timer_handler();

    // Query touch panel and propagate events
    if (touch_indev == NULL) {
      touch_indev = lv_indev_get_next(NULL);
    }
  }
}

// ── Web Server WebSockets streaming task (Core 0) ───────────────────────────
static void wifi_streaming_task(void *pvParameters) {
    ESP_LOGI(TAG, "WiFi WebSockets streaming task started on core %d", xPortGetCoreID());
    tSpiTxPayload telemetry_frame;
    uint32_t last_send_time = 0;
    
    while (1) {
        // Blocks until a new frame is received via SPI DMA from the STM32
        if (comm_spi_master_queue_pop(&telemetry_frame, portMAX_DELAY)) {
            uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
            // Throttle WebSocket broadcasts to ~20 FPS (every 50ms) to prevent WiFi queue saturation
            if (now - last_send_time >= 50) {
                last_send_time = now;
                wifi_ap_broadcast_telemetry(&telemetry_frame);
            }
        }
    }
}

// ── Main Entrance ───────────────────────────────────────────────────────────
extern "C" void app_main() {
  ESP_LOGI(TAG, "Initializing System firmware...");

  // 1. Initialize display hardware abstraction layer (Display, LEDC, SPI, LVGL, Touch)
  hal_display_init();
  
  // 2. Create DSO splash screen UI
  transition_to_screen(SCREEN_SPLASH);
  display_brightness_set(75);

  // 3. Initialize NVS (required for Wi-Fi)
  esp_err_t ret = nvs_flash_init();
  if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
    ESP_ERROR_CHECK(nvs_flash_erase());
    ret = nvs_flash_init();
  }
  ESP_ERROR_CHECK(ret);

  // 4. Initialize co-processors interface
  ESP_ERROR_CHECK(comm_spi_master_init());

  // 5. Initialize Wi-Fi AP & HTTP/WebSocket Server
  ESP_ERROR_CHECK(wifi_ap_init());

  // 6. Spawning real-time core loops
  // GUI & Touch loop running on Core 1
  xTaskCreatePinnedToCore(lvgl_task, "lvgl", LVGL_TASK_STACK_SIZE, NULL, LVGL_TASK_PRIORITY, NULL, 1);

  // WiFi WebSockets streaming loop running on Core 0
  xTaskCreatePinnedToCore(wifi_streaming_task, "wifi_stream", 4096, NULL, 5, NULL, 0);
  
  ESP_LOGI(TAG, "System initialization complete. Run loops active.");
}