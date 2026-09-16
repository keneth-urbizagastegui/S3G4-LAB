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

esp_err_t lcd_bus_set_frame_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2) {
    esp_lcd_panel_io_handle_t io = ili9488_8080_get_panel_io();
    if (!io) return ESP_ERR_INVALID_STATE;
    ili9488_8080_set_window(x1, y1, x2, y2);
    return ESP_OK;
}

esp_err_t lcd_bus_draw_strip_continue_async(const uint16_t *data, size_t len_bytes, bool is_first) {
    esp_lcd_panel_io_handle_t io = ili9488_8080_get_panel_io();
    SemaphoreHandle_t sem = ili9488_8080_get_trans_sem();
    if (!io || !sem) return ESP_ERR_INVALID_STATE;

    // Purgar token previo si existiera
    xSemaphoreTake(sem, 0);

    s_strip_start_us = esp_timer_get_time();
    s_strip_in_flight = true;
    return esp_lcd_panel_io_tx_color(io, is_first ? 0x2C : -1, data, len_bytes);
}

esp_err_t lcd_bus_draw_strip_async(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, const uint16_t *data, size_t len_bytes) {
    esp_err_t ret = lcd_bus_set_frame_window(x1, y1, x2, y2);
    if (ret != ESP_OK) return ret;
    return lcd_bus_draw_strip_continue_async(data, len_bytes, true);
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

// -----------------------------------------------------------------------------
// Sincronización y monitoreo del pin TE (Tearing Effect)
// -----------------------------------------------------------------------------
#include <math.h>
#include "driver/gpio.h"

#define TE_SAMPLES_MAX 128

static portMUX_TYPE s_te_mux = portMUX_INITIALIZER_UNLOCKED;
static SemaphoreHandle_t s_te_sem = NULL;
static volatile uint32_t s_te_pulse_count = 0;
static volatile int64_t s_te_prev_edge_us = 0;
static volatile int64_t s_te_last_edge_us = 0;

static uint32_t s_te_periods[TE_SAMPLES_MAX];
static uint32_t s_te_periods_cnt = 0;
static uint64_t s_te_period_sum_us = 0;
static uint32_t s_te_period_count_total = 0;

static bool s_te_present = false;
static float s_te_last_hz = 0.0f;
static float s_te_last_jitter_ms = 0.0f;
static int64_t s_te_last_sample_us = 0;

static void IRAM_ATTR te_gpio_isr_handler(void *arg) {
    int64_t now_us = esp_timer_get_time();
    s_te_pulse_count++;
    if (s_te_prev_edge_us > 0) {
        uint32_t dt = (uint32_t)(now_us - s_te_prev_edge_us);
        s_te_period_sum_us += dt;
        s_te_period_count_total++;
        if (s_te_periods_cnt < TE_SAMPLES_MAX) {
            s_te_periods[s_te_periods_cnt++] = dt;
        }
    }
    s_te_prev_edge_us = now_us;
    s_te_last_edge_us = now_us;

    BaseType_t high_task_awoken = pdFALSE;
    if (s_te_sem) {
        xSemaphoreGiveFromISR(s_te_sem, &high_task_awoken);
    }
    if (high_task_awoken == pdTRUE) {
        portYIELD_FROM_ISR();
    }
}

esp_err_t lcd_bus_te_init(gpio_num_t pin) {
    ESP_LOGI(TAG, "Configurando pin TE en GPIO %d (sin pull, flanco subida)...", pin);
    if (!s_te_sem) {
        s_te_sem = xSemaphoreCreateBinary();
        assert(s_te_sem != NULL);
    }

    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << pin),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_POSEDGE,
    };
    esp_err_t err = gpio_config(&io_conf);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al configurar GPIO %d: %s", pin, esp_err_to_name(err));
        return err;
    }

    err = gpio_install_isr_service(0);
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "Fallo al instalar servicio ISR GPIO: %s", esp_err_to_name(err));
        return err;
    }

    err = gpio_isr_handler_add(pin, te_gpio_isr_handler, (void *)(intptr_t)pin);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al registrar handler ISR para GPIO %d: %s", pin, esp_err_to_name(err));
        return err;
    }

    // Probar presencia de señal durante hasta 1000 ms
    int64_t probe_start = esp_timer_get_time();
    while ((esp_timer_get_time() - probe_start) < 1000000LL) {
        if (s_te_pulse_count >= 10) break;
        vTaskDelay(pdMS_TO_TICKS(50));
    }

    int64_t probe_dur_us = esp_timer_get_time() - probe_start;
    if (s_te_pulse_count > 0 && probe_dur_us > 0) {
        s_te_present = true;
        float hz = (float)s_te_pulse_count * 1000000.0f / (float)probe_dur_us;
        s_te_last_hz = hz;
        ESP_LOGI(TAG, "TE,present=1,hz=%.1f (pulsos=%lu en %lld ms)",
                 hz, (unsigned long)s_te_pulse_count, (long long)(probe_dur_us / 1000));
        printf("TE,present=1,hz=%.1f\n", hz);
        fflush(stdout);
    } else {
        s_te_present = false;
        ESP_LOGW(TAG, "TE,absent=1 (sin pulsos tras %lld ms)", (long long)(probe_dur_us / 1000));
        printf("TE,absent=1\n");
        fflush(stdout);
    }

    s_te_last_sample_us = esp_timer_get_time();
    return ESP_OK;
}

bool lcd_bus_te_is_present(void) {
    return s_te_present;
}

float lcd_bus_te_get_hz(void) {
    portENTER_CRITICAL(&s_te_mux);
    float hz = s_te_last_hz;
    portEXIT_CRITICAL(&s_te_mux);
    return hz;
}

float lcd_bus_te_get_jitter_ms(void) {
    portENTER_CRITICAL(&s_te_mux);
    float j = s_te_last_jitter_ms;
    portEXIT_CRITICAL(&s_te_mux);
    return j;
}

uint32_t lcd_bus_te_get_period_us(void) {
    portENTER_CRITICAL(&s_te_mux);
    float hz = s_te_last_hz;
    uint32_t total = s_te_period_count_total;
    uint64_t sum = s_te_period_sum_us;
    portEXIT_CRITICAL(&s_te_mux);

    if (hz > 10.0f) {
        return (uint32_t)(1000000.0f / hz);
    }
    if (total > 0 && sum > 0) {
        return (uint32_t)(sum / total);
    }
    return 16666; // Periodo nominal a 60 Hz si todavia no hay medicion
}

esp_err_t lcd_bus_wait_te(uint32_t timeout_us, uint32_t *out_wait_us) {
    if (!s_te_sem || !s_te_present) {
        if (out_wait_us) *out_wait_us = 0;
        return ESP_OK;
    }

    // Purgar TODOS los tokens previos acumulados para asegurar que esperamos el SIGUIENTE flanco real
    while (xSemaphoreTake(s_te_sem, 0) == pdTRUE);

    int64_t t0 = esp_timer_get_time();
    TickType_t ticks = pdMS_TO_TICKS((timeout_us + 999) / 1000);
    if (ticks == 0) ticks = 1;

    BaseType_t ok = xSemaphoreTake(s_te_sem, ticks);
    int64_t elapsed = esp_timer_get_time() - t0;
    if (out_wait_us) {
        *out_wait_us = (uint32_t)(elapsed > 0 ? elapsed : 0);
    }
    return (ok == pdTRUE) ? ESP_OK : ESP_ERR_TIMEOUT;
}

void lcd_bus_te_perf_sample(uint32_t *out_pulses, float *out_hz, float *out_jitter_ms, bool *out_present) {
    int64_t now_us = esp_timer_get_time();
    int64_t window_us = now_us - s_te_last_sample_us;
    s_te_last_sample_us = now_us;

    portENTER_CRITICAL(&s_te_mux);
    uint32_t pulses = s_te_pulse_count;
    s_te_pulse_count = 0;

    uint32_t cnt = s_te_periods_cnt;
    uint32_t periods_copy[TE_SAMPLES_MAX];
    if (cnt > 0) {
        memcpy(periods_copy, s_te_periods, cnt * sizeof(uint32_t));
    }
    s_te_periods_cnt = 0;
    portEXIT_CRITICAL(&s_te_mux);

    float hz = (window_us > 0) ? ((float)pulses * 1000000.0f / (float)window_us) : 0.0f;
    float jitter_ms = 0.0f;

    if (cnt > 1) {
        uint64_t sum = 0;
        for (uint32_t i = 0; i < cnt; i++) {
            sum += periods_copy[i];
        }
        double avg_dt = (double)sum / (double)cnt;
        double dev_sum = 0.0;
        for (uint32_t i = 0; i < cnt; i++) {
            dev_sum += fabs((double)periods_copy[i] - avg_dt);
        }
        jitter_ms = (float)((dev_sum / (double)cnt) / 1000.0);
    }

    bool pres = (pulses > 0);
    if (pres) {
        s_te_present = true;
    }

    portENTER_CRITICAL(&s_te_mux);
    s_te_last_hz = hz;
    s_te_last_jitter_ms = jitter_ms;
    portEXIT_CRITICAL(&s_te_mux);

    if (out_pulses) *out_pulses = pulses;
    if (out_hz) *out_hz = hz;
    if (out_jitter_ms) *out_jitter_ms = jitter_ms;
    if (out_present) *out_present = s_te_present;
}
