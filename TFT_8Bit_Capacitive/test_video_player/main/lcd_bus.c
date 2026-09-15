#include "lcd_bus.h"
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_lcd_panel_io.h"
#include "ili9488_8080.h"

static const char *TAG = "LCD_BUS";

static SemaphoreHandle_t s_bus_mutex = NULL;
static portMUX_TYPE s_rect_mux = portMUX_INITIALIZER_UNLOCKED;
static lcd_video_rect_t s_video_rect = {0, 0, 480, 320};

static int64_t s_strip_start_us = 0;
static bool s_strip_in_flight = false;

void lcd_bus_init(void) {
    if (!s_bus_mutex) {
        s_bus_mutex = xSemaphoreCreateRecursiveMutex();
        assert(s_bus_mutex != NULL);
    }
    ESP_LOGI(TAG, "lcd_bus inicializado con mutex recursivo.");
}

void lcd_bus_lock(void) {
    if (s_bus_mutex) {
        xSemaphoreTakeRecursive(s_bus_mutex, portMAX_DELAY);
    }
}

void lcd_bus_unlock(void) {
    if (s_bus_mutex) {
        xSemaphoreGiveRecursive(s_bus_mutex);
    }
}

void lcd_bus_set_video_rect(int16_t x, int16_t y, int16_t w, int16_t h) {
    portENTER_CRITICAL(&s_rect_mux);
    s_video_rect.x = x;
    s_video_rect.y = y;
    s_video_rect.w = w;
    s_video_rect.h = h;
    portEXIT_CRITICAL(&s_rect_mux);
}

void lcd_bus_get_video_rect(int16_t *x, int16_t *y, int16_t *w, int16_t *h) {
    portENTER_CRITICAL(&s_rect_mux);
    if (x) *x = s_video_rect.x;
    if (y) *y = s_video_rect.y;
    if (w) *w = s_video_rect.w;
    if (h) *h = s_video_rect.h;
    portEXIT_CRITICAL(&s_rect_mux);
}

esp_err_t lcd_bus_draw_strip_async(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, const uint16_t *data, size_t len_bytes) {
    esp_lcd_panel_io_handle_t io = ili9488_8080_get_panel_io();
    SemaphoreHandle_t sem = ili9488_8080_get_trans_sem();
    if (!io || !sem) return ESP_ERR_INVALID_STATE;

    // Purgar token previo si existiera
    xSemaphoreTake(sem, 0);

    ili9488_8080_set_window(x1, y1, x2, y2);
    s_strip_start_us = esp_timer_get_time();
    s_strip_in_flight = true;
    return esp_lcd_panel_io_tx_color(io, 0x2C, data, len_bytes);
}

esp_err_t lcd_bus_wait_strip_done(uint32_t *out_dma_us) {
    if (!s_strip_in_flight) {
        if (out_dma_us) *out_dma_us = 0;
        return ESP_OK;
    }
    SemaphoreHandle_t sem = ili9488_8080_get_trans_sem();
    if (!sem) return ESP_ERR_INVALID_STATE;

    xSemaphoreTake(sem, portMAX_DELAY);
    s_strip_in_flight = false;
    if (out_dma_us) {
        int64_t elapsed = esp_timer_get_time() - s_strip_start_us;
        *out_dma_us = (uint32_t)(elapsed > 0 ? elapsed : 0);
    }
    return ESP_OK;
}
