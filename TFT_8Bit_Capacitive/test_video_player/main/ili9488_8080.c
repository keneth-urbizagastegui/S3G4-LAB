
#include "ili9488_8080.h"
#include "lcd_bus.h"
#include <string.h>
#include <stdlib.h>
#include "font5x7.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_io_i80.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_heap_caps.h"
#include "sdkconfig.h"

static const char *TAG = "ili9488_8080";

// Asignación de pines optimizada para WeAct Studio ESP32-S3 (Sin conflictos con LED RGB ni strapping)
// Header Izquierdo WeAct:
#define TFT_CS          GPIO_NUM_8    // Serigrafiado "8"  (Evita GPIO 3 que es STRAP JTAG)
#define TFT_DC          GPIO_NUM_9    // Serigrafiado "9"
#define TFT_WR          GPIO_NUM_14   // Serigrafiado "14"
#define TFT_RESET       GPIO_NUM_16   // Serigrafiado "16"
#define TFT_BACKLIGHT   GPIO_NUM_12   // Serigrafiado "12"

// Bus de datos 8-bit:
#define TFT_D0          GPIO_NUM_4    // Header Izquierdo "4"  (Evita GPIO 38/48 que es RGB_LED)
#define TFT_D1          GPIO_NUM_39   // Header Derecho "39"
#define TFT_D2          GPIO_NUM_40   // Header Derecho "40"
#define TFT_D3          GPIO_NUM_41   // Header Derecho "41"
#define TFT_D4          GPIO_NUM_42   // Header Derecho "42"
#define TFT_D5          GPIO_NUM_2    // Header Derecho "2"
#define TFT_D6          GPIO_NUM_1    // Header Derecho "1"
#define TFT_D7          GPIO_NUM_10   // Header Izquierdo "10"

#define CHUNK_PIXELS        (LCD_WIDTH * 20) // 6400 píxeles por bloque DMA (12.8 KB)

static uint32_t s_bus_freq_hz = 16 * 1000 * 1000; // 16 MHz Overclock por defecto
static esp_lcd_i80_bus_handle_t s_i80_bus = NULL;
static esp_lcd_panel_io_handle_t s_panel_io = NULL;
static SemaphoreHandle_t s_trans_done_sem = NULL;

// Loop Engineering: Doble Búfer DMA Ping-Pong para solapar CPU y hardware DMA
static uint16_t *s_dma_chunk_bufs[2] = {NULL, NULL};
static uint8_t s_buf_toggle = 0;

static bool on_color_trans_done(esp_lcd_panel_io_handle_t panel_io,
                                esp_lcd_panel_io_event_data_t *edata,
                                void *user_ctx) {
    BaseType_t high_task_awoken = pdFALSE;
    if (s_trans_done_sem) {
        xSemaphoreGiveFromISR(s_trans_done_sem, &high_task_awoken);
    }
    return high_task_awoken == pdTRUE;
}

void board_turn_off_rgb_led(void) {
    // La placa WeAct Studio integra un LED RGB WS2812 en GPIO 48 (o GPIO 38 según revisión).
    // Si quedan flotantes, el LED capta ruido y se enciende solo.
    // Forzamos ambos pines a nivel BAJO (0V) como salida para apagarlo:
    gpio_reset_pin(GPIO_NUM_48);
    gpio_set_direction(GPIO_NUM_48, GPIO_MODE_OUTPUT);
    gpio_set_level(GPIO_NUM_48, 0);

    gpio_reset_pin(GPIO_NUM_38);
    gpio_set_direction(GPIO_NUM_38, GPIO_MODE_OUTPUT);
    gpio_set_level(GPIO_NUM_38, 0);
}

#include "driver/ledc.h"

static void init_backlight(void) {
    ledc_timer_config_t ledc_timer = {
        .speed_mode       = LEDC_LOW_SPEED_MODE,
        .timer_num        = LEDC_TIMER_0,
        .duty_resolution  = LEDC_TIMER_8_BIT,
        .freq_hz          = 5000,
        .clk_cfg          = LEDC_AUTO_CLK
    };
    ledc_timer_config(&ledc_timer);

    ledc_channel_config_t ledc_channel = {
        .speed_mode     = LEDC_LOW_SPEED_MODE,
        .channel        = LEDC_CHANNEL_0,
        .timer_sel      = LEDC_TIMER_0,
        .intr_type      = LEDC_INTR_DISABLE,
        .gpio_num       = TFT_BACKLIGHT,
        .duty           = 255,
        .hpoint         = 0
    };
    ledc_channel_config(&ledc_channel);
}

void ili9488_8080_set_backlight(uint8_t brightness_pct) {
    if (brightness_pct > 100) brightness_pct = 100;
    uint32_t duty = (brightness_pct * 255) / 100;
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

static void hardware_reset(void) {
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << TFT_RESET),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&io_conf);

    gpio_set_level(TFT_RESET, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(TFT_RESET, 0);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(TFT_RESET, 1);
    vTaskDelay(pdMS_TO_TICKS(120));
}

esp_err_t ili9488_8080_init(void) {
    board_turn_off_rgb_led();
    ESP_LOGI(TAG, "Iniciando hardware reset...");
    hardware_reset();

    if (s_trans_done_sem == NULL) {
        s_trans_done_sem = xSemaphoreCreateBinary();
    }
    for (int b = 0; b < 2; b++) {
        if (s_dma_chunk_bufs[b] == NULL) {
            s_dma_chunk_bufs[b] = (uint16_t *)heap_caps_malloc(CHUNK_PIXELS * sizeof(uint16_t), MALLOC_CAP_DMA);
            assert(s_dma_chunk_bufs[b] != NULL);
        }
    }

    ESP_LOGI(TAG, "Configurando bus LCD 8080 de 8 bits a %lu MHz...", (unsigned long)(s_bus_freq_hz / 1000000));
    esp_lcd_i80_bus_config_t bus_config = {
        .dc_gpio_num = TFT_DC,
        .wr_gpio_num = TFT_WR,
        .clk_src = LCD_CLK_SRC_DEFAULT,
        .data_gpio_nums = {
            TFT_D0, TFT_D1, TFT_D2, TFT_D3,
            TFT_D4, TFT_D5, TFT_D6, TFT_D7
        },
        .bus_width = 8,
        .max_transfer_bytes = LCD_WIDTH * LCD_HEIGHT * sizeof(uint16_t),
        .dma_burst_size = 64,
    };
    ESP_ERROR_CHECK(esp_lcd_new_i80_bus(&bus_config, &s_i80_bus));

    esp_lcd_panel_io_i80_config_t io_config = {
        .cs_gpio_num = TFT_CS,
        .pclk_hz = s_bus_freq_hz,
        .trans_queue_depth = 10,
        .on_color_trans_done = on_color_trans_done,
        .user_ctx = NULL,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
        .dc_levels = {
            .dc_idle_level = 0,
            .dc_cmd_level = 0,
            .dc_dummy_level = 0,
            .dc_data_level = 1,
        },
        .flags = {
            .swap_color_bytes = 1,
        },
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_i80(s_i80_bus, &io_config, &s_panel_io));

    ESP_LOGI(TAG, "Enviando registros de inicialización ILI9488 IPS...");

    // Secuencia recomendada por BuyDisplay para panel IPS
    const uint8_t f7_data[] = {0xA9, 0x51, 0x2C, 0x82};
    esp_lcd_panel_io_tx_param(s_panel_io, 0xF7, f7_data, sizeof(f7_data));

#ifndef CONFIG_APP_LCD_MADCTL
#define CONFIG_APP_LCD_MADCTL 0x48
#endif
    const uint8_t madctl = (uint8_t)CONFIG_APP_LCD_MADCTL; // BGR orden, orientación nativa sin MV (0x28 previo)
    esp_lcd_panel_io_tx_param(s_panel_io, 0x36, &madctl, 1);

    const uint8_t colmod = 0x55; // 16-bit/pixel RGB565 en modo paralelo
    esp_lcd_panel_io_tx_param(s_panel_io, 0x3A, &colmod, 1);

    const uint8_t b0_data = 0x00;
    esp_lcd_panel_io_tx_param(s_panel_io, 0xB0, &b0_data, 1);

    const uint8_t b4_data = 0x02; // Inversion 2-dot
    esp_lcd_panel_io_tx_param(s_panel_io, 0xB4, &b4_data, 1);

#ifndef CONFIG_APP_LCD_B1_P1
#define CONFIG_APP_LCD_B1_P1 0x80
#endif

#ifndef CONFIG_APP_LCD_B1_P2
#define CONFIG_APP_LCD_B1_P2 0x12
#endif

    // Registro FRMCTR1 (0xB1): Valor original 60 Hz = {0xA0, 0x11}. Ajuste autorizado Keneth (15/09/2026) = {CONFIG_APP_LCD_B1_P1, CONFIG_APP_LCD_B1_P2}
    const uint8_t b1_data[] = {(uint8_t)CONFIG_APP_LCD_B1_P1, (uint8_t)CONFIG_APP_LCD_B1_P2};
    esp_lcd_panel_io_tx_param(s_panel_io, 0xB1, b1_data, sizeof(b1_data));

    const uint8_t c0_data[] = {0x0F, 0x0F};
    esp_lcd_panel_io_tx_param(s_panel_io, 0xC0, c0_data, sizeof(c0_data));

    const uint8_t c1_data = 0x41;
    esp_lcd_panel_io_tx_param(s_panel_io, 0xC1, &c1_data, 1);

    const uint8_t c2_data = 0x22;
    esp_lcd_panel_io_tx_param(s_panel_io, 0xC2, &c2_data, 1);

    const uint8_t b7_data = 0xC6;
    esp_lcd_panel_io_tx_param(s_panel_io, 0xB7, &b7_data, 1);

    const uint8_t c5_data[] = {0x00, 0x53, 0x80};
    esp_lcd_panel_io_tx_param(s_panel_io, 0xC5, c5_data, sizeof(c5_data));

    const uint8_t e0_gamma[] = {
        0x00, 0x08, 0x0C, 0x02, 0x0E, 0x04, 0x30, 0x45,
        0x47, 0x04, 0x0C, 0x0A, 0x2E, 0x34, 0x0F
    };
    esp_lcd_panel_io_tx_param(s_panel_io, 0xE0, e0_gamma, sizeof(e0_gamma));

    const uint8_t e1_gamma[] = {
        0x00, 0x11, 0x0D, 0x01, 0x0F, 0x05, 0x39, 0x36,
        0x51, 0x06, 0x0F, 0x0D, 0x33, 0x37, 0x0F
    };
    esp_lcd_panel_io_tx_param(s_panel_io, 0xE1, e1_gamma, sizeof(e1_gamma));

    // Display Inversion On para panel IPS
    esp_lcd_panel_io_tx_param(s_panel_io, 0x21, NULL, 0);

    // Sleep Out
    esp_lcd_panel_io_tx_param(s_panel_io, 0x11, NULL, 0);
    vTaskDelay(pdMS_TO_TICKS(120));

    // Display ON
    esp_lcd_panel_io_tx_param(s_panel_io, 0x29, NULL, 0);
    vTaskDelay(pdMS_TO_TICKS(20));

    // Activar senal TE (Tearing Effect) - Solo V-blanking (0x00)
    const uint8_t teon_param = 0x00;
    esp_lcd_panel_io_tx_param(s_panel_io, 0x35, &teon_param, 1);

    // Inicializar backlight al 100%
    init_backlight();

    ESP_LOGI(TAG, "Inicialización completada.");
    return ESP_OK;
}

esp_err_t ili9488_8080_init_clock(uint32_t freq_hz) {
    s_bus_freq_hz = freq_hz;
    return ili9488_8080_init();
}

static void set_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2) {
    uint8_t caset[4] = {
        (uint8_t)(x1 >> 8), (uint8_t)(x1 & 0xFF),
        (uint8_t)(x2 >> 8), (uint8_t)(x2 & 0xFF)
    };
    esp_lcd_panel_io_tx_param(s_panel_io, 0x2A, caset, sizeof(caset));

    uint8_t paset[4] = {
        (uint8_t)(y1 >> 8), (uint8_t)(y1 & 0xFF),
        (uint8_t)(y2 >> 8), (uint8_t)(y2 & 0xFF)
    };
    esp_lcd_panel_io_tx_param(s_panel_io, 0x2B, paset, sizeof(paset));
}

esp_lcd_panel_io_handle_t ili9488_8080_get_panel_io(void) {
    return s_panel_io;
}

SemaphoreHandle_t ili9488_8080_get_trans_sem(void) {
    return s_trans_done_sem;
}

void ili9488_8080_set_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2) {
    set_window(x1, y1, x2, y2);
}

esp_err_t ili9488_8080_draw_bitmap(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, const uint16_t *data) {
    if (s_panel_io == NULL) return ESP_ERR_INVALID_STATE;
    lcd_bus_lock();
    if (s_trans_done_sem) xSemaphoreTake(s_trans_done_sem, 0);
    set_window(x1, y1, x2, y2);
    size_t pixel_count = (size_t)(x2 - x1 + 1) * (y2 - y1 + 1);
    esp_err_t ret = esp_lcd_panel_io_tx_color(s_panel_io, 0x2C, data, pixel_count * sizeof(uint16_t));
    xSemaphoreTake(s_trans_done_sem, portMAX_DELAY);
    lcd_bus_unlock();
    return ret;
}

esp_err_t ili9488_8080_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color) {
    if (s_panel_io == NULL || s_dma_chunk_bufs[0] == NULL) return ESP_ERR_INVALID_STATE;
    if (x >= LCD_WIDTH || y >= LCD_HEIGHT) return ESP_OK;
    if ((x + w) > LCD_WIDTH)  w = LCD_WIDTH - x;
    if ((y + h) > LCD_HEIGHT) h = LCD_HEIGHT - y;

    size_t total_pixels = (size_t)w * h;
    size_t fill_count = (total_pixels > CHUNK_PIXELS) ? CHUNK_PIXELS : total_pixels;
    for (size_t i = 0; i < fill_count; i++) {
        s_dma_chunk_bufs[0][i] = color;
        s_dma_chunk_bufs[1][i] = color;
    }

    set_window(x, y, x + w - 1, y + h - 1);

    bool first_chunk = true;
    while (total_pixels > 0) {
        size_t current_chunk = (total_pixels > CHUNK_PIXELS) ? CHUNK_PIXELS : total_pixels;
        uint16_t *buf = s_dma_chunk_bufs[s_buf_toggle];
        s_buf_toggle ^= 1;

        // El primer bloque envía el comando 0x2C (RAMWR). Los bloques siguientes envían -1 para continuar sin reiniciar puntero.
        esp_lcd_panel_io_tx_color(s_panel_io, first_chunk ? 0x2C : -1, buf, current_chunk * sizeof(uint16_t));
        xSemaphoreTake(s_trans_done_sem, portMAX_DELAY);
        first_chunk = false;
        total_pixels -= current_chunk;
    }

    return ESP_OK;
}

esp_err_t ili9488_8080_fill_screen(uint16_t color) {
    return ili9488_8080_fill_rect(0, 0, LCD_WIDTH, LCD_HEIGHT, color);
}

void ili9488_8080_draw_pixel(uint16_t x, uint16_t y, uint16_t color) {
    if (x >= LCD_WIDTH || y >= LCD_HEIGHT) return;
    set_window(x, y, x, y);
    esp_lcd_panel_io_tx_color(s_panel_io, 0x2C, &color, sizeof(uint16_t));
    xSemaphoreTake(s_trans_done_sem, portMAX_DELAY);
}

void ili9488_8080_draw_fast_h_line(int16_t x, int16_t y, int16_t w, uint16_t color) {
    if (y < 0 || y >= LCD_HEIGHT || w <= 0) return;
    if (x < 0) { w += x; x = 0; }
    if (x + w > LCD_WIDTH) w = LCD_WIDTH - x;
    if (w <= 0) return;
    ili9488_8080_fill_rect((uint16_t)x, (uint16_t)y, (uint16_t)w, 1, color);
}

void ili9488_8080_draw_fast_v_line(int16_t x, int16_t y, int16_t h, uint16_t color) {
    if (x < 0 || x >= LCD_WIDTH || h <= 0) return;
    if (y < 0) { h += y; y = 0; }
    if (y + h > LCD_HEIGHT) h = LCD_HEIGHT - y;
    if (h <= 0) return;
    ili9488_8080_fill_rect((uint16_t)x, (uint16_t)y, 1, (uint16_t)h, color);
}

void ili9488_8080_draw_line(int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint16_t color) {
    if (x0 == x1) {
        if (y0 > y1) { int16_t t = y0; y0 = y1; y1 = t; }
        ili9488_8080_draw_fast_v_line(x0, y0, y1 - y0 + 1, color);
        return;
    }
    if (y0 == y1) {
        if (x0 > x1) { int16_t t = x0; x0 = x1; x1 = t; }
        ili9488_8080_draw_fast_h_line(x0, y0, x1 - x0 + 1, color);
        return;
    }

    int16_t steep = abs(y1 - y0) > abs(x1 - x0);
    if (steep) {
        int16_t t;
        t = x0; x0 = y0; y0 = t;
        t = x1; x1 = y1; y1 = t;
    }
    if (x0 > x1) {
        int16_t t;
        t = x0; x0 = x1; x1 = t;
        t = y0; y0 = y1; y1 = t;
    }

    int16_t dx = x1 - x0;
    int16_t dy = abs(y1 - y0);
    int16_t err = dx / 2;
    int16_t ystep = (y0 < y1) ? 1 : -1;

    for (; x0 <= x1; x0++) {
        if (steep) {
            ili9488_8080_draw_pixel(y0, x0, color);
        } else {
            ili9488_8080_draw_pixel(x0, y0, color);
        }
        err -= dy;
        if (err < 0) {
            y0 += ystep;
            err += dx;
        }
    }
}

void ili9488_8080_draw_circle(int16_t x0, int16_t y0, int16_t r, uint16_t color) {
    int16_t f = 1 - r;
    int16_t ddF_x = 1;
    int16_t ddF_y = -2 * r;
    int16_t x = 0;
    int16_t y = r;

    ili9488_8080_draw_pixel(x0, y0 + r, color);
    ili9488_8080_draw_pixel(x0, y0 - r, color);
    ili9488_8080_draw_pixel(x0 + r, y0, color);
    ili9488_8080_draw_pixel(x0 - r, y0, color);

    while (x < y) {
        if (f >= 0) {
            y--;
            ddF_y += 2;
            f += ddF_y;
        }
        x++;
        ddF_x += 2;
        f += ddF_x;

        ili9488_8080_draw_pixel(x0 + x, y0 + y, color);
        ili9488_8080_draw_pixel(x0 - x, y0 + y, color);
        ili9488_8080_draw_pixel(x0 + x, y0 - y, color);
        ili9488_8080_draw_pixel(x0 - x, y0 - y, color);
        ili9488_8080_draw_pixel(x0 + y, y0 + x, color);
        ili9488_8080_draw_pixel(x0 - y, y0 + x, color);
        ili9488_8080_draw_pixel(x0 + y, y0 - x, color);
        ili9488_8080_draw_pixel(x0 - y, y0 - x, color);
    }
}

void ili9488_8080_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg, uint8_t size) {
    if (c < 32 || c > 126) c = ' ';
    if (size == 0) size = 1;
    if (size > 2) size = 2;
    uint16_t char_w = 6 * size;
    uint16_t char_h = 8 * size;
    if (x + char_w > LCD_WIDTH || y + char_h > LCD_HEIGHT) return;

    // Buffer temporal para transmisión de bloque único por DMA
    uint16_t char_buf[12 * 16]; // Max tamaño size=2 (12x16 = 192 pixels)
    const uint8_t *glyph = &FONT_5X7[((uint8_t)c) * 5];

    for (int col = 0; col < 6; col++) {
        uint8_t line = (col < 5) ? glyph[col] : 0x00;
        for (int row = 0; row < 8; row++) {
            uint16_t color = (line & (1 << row)) ? fg : bg;
            if (size == 1) {
                char_buf[row * 6 + col] = color;
            } else {
                for (int dy = 0; dy < 2; dy++) {
                    for (int dx = 0; dx < 2; dx++) {
                        char_buf[((row * 2 + dy) * 12) + (col * 2 + dx)] = color;
                    }
                }
            }
        }
    }

    ili9488_8080_draw_bitmap(x, y, x + char_w - 1, y + char_h - 1, char_buf);
}

void ili9488_8080_draw_string(uint16_t x, uint16_t y, const char *str, uint16_t fg, uint16_t bg, uint8_t size) {
    uint16_t cursor_x = x;
    uint16_t char_step = 6 * (size == 0 ? 1 : size);
    while (*str) {
        if (*str == '\n') {
            cursor_x = x;
            y += (8 * (size == 0 ? 1 : size));
        } else {
            ili9488_8080_draw_char(cursor_x, y, *str, fg, bg, size);
            cursor_x += char_step;
        }
        str++;
    }
}

void ili9488_8080_draw_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color) {
    ili9488_8080_draw_fast_h_line(x, y, w, color);
    ili9488_8080_draw_fast_h_line(x, y + h - 1, w, color);
    ili9488_8080_draw_fast_v_line(x, y, h, color);
    ili9488_8080_draw_fast_v_line(x + w - 1, y, h, color);
}

void ili9488_8080_fill_circle(int16_t x0, int16_t y0, int16_t r, uint16_t color) {
    ili9488_8080_draw_fast_v_line(x0, y0 - r, 2 * r + 1, color);
    int16_t f = 1 - r;
    int16_t ddF_x = 1;
    int16_t ddF_y = -2 * r;
    int16_t x = 0;
    int16_t y = r;

    while (x < y) {
        if (f >= 0) {
            y--;
            ddF_y += 2;
            f += ddF_y;
        }
        x++;
        ddF_x += 2;
        f += ddF_x;

        ili9488_8080_draw_fast_v_line(x0 + x, y0 - y, 2 * y + 1, color);
        ili9488_8080_draw_fast_v_line(x0 - x, y0 - y, 2 * y + 1, color);
        ili9488_8080_draw_fast_v_line(x0 + y, y0 - x, 2 * x + 1, color);
        ili9488_8080_draw_fast_v_line(x0 - y, y0 - x, 2 * x + 1, color);
    }
}

void ili9488_8080_draw_triangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t x2, int16_t y2, uint16_t color) {
    ili9488_8080_draw_line(x0, y0, x1, y1, color);
    ili9488_8080_draw_line(x1, y1, x2, y2, color);
    ili9488_8080_draw_line(x2, y2, x0, y0, color);
}

void ili9488_8080_fill_triangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t x2, int16_t y2, uint16_t color) {
    int16_t a, b, y, last;
    if (y0 > y1) { int16_t t = y0; y0 = y1; y1 = t; t = x0; x0 = x1; x1 = t; }
    if (y1 > y2) { int16_t t = y1; y1 = y2; y2 = t; t = x1; x1 = x2; x2 = t; }
    if (y0 > y1) { int16_t t = y0; y0 = y1; y1 = t; t = x0; x0 = x1; x1 = t; }

    if (y0 == y2) {
        a = b = x0;
        if (x1 < a) a = x1; else if (x1 > b) b = x1;
        if (x2 < a) a = x2; else if (x2 > b) b = x2;
        ili9488_8080_draw_fast_h_line(a, y0, b - a + 1, color);
        return;
    }

    int16_t dx01 = x1 - x0, dy01 = y1 - y0;
    int16_t dx02 = x2 - x0, dy02 = y2 - y0;
    int16_t dx12 = x2 - x1, dy12 = y2 - y1;
    int32_t sa = 0, sb = 0;

    if (y1 == y2) last = y1;
    else          last = y1 - 1;

    for (y = y0; y <= last; y++) {
        a = x0 + sa / dy01;
        b = x0 + sb / dy02;
        sa += dx01;
        sb += dx02;
        if (a > b) { int16_t t = a; a = b; b = t; }
        ili9488_8080_draw_fast_h_line(a, y, b - a + 1, color);
    }

    sa = (int32_t)dx12 * (y - y1);
    sb = (int32_t)dx02 * (y - y0);
    for (; y <= y2; y++) {
        a = x1 + sa / dy12;
        b = x0 + sb / dy02;
        sa += dx12;
        sb += dx02;
        if (a > b) { int16_t t = a; a = b; b = t; }
        ili9488_8080_draw_fast_h_line(a, y, b - a + 1, color);
    }
}

void ili9488_8080_draw_round_rect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r, uint16_t color) {
    ili9488_8080_draw_fast_h_line(x + r, y, w - 2 * r, color);
    ili9488_8080_draw_fast_h_line(x + r, y + h - 1, w - 2 * r, color);
    ili9488_8080_draw_fast_v_line(x, y + r, h - 2 * r, color);
    ili9488_8080_draw_fast_v_line(x + w - 1, y + r, h - 2 * r, color);
    // 4 esquinas circulares
    int16_t f = 1 - r, ddF_x = 1, ddF_y = -2 * r, cx = 0, cy = r;
    while (cx < cy) {
        if (f >= 0) { cy--; ddF_y += 2; f += ddF_y; }
        cx++; ddF_x += 2; f += ddF_x;
        ili9488_8080_draw_pixel(x + r - cx, y + r - cy, color);
        ili9488_8080_draw_pixel(x + r - cy, y + r - cx, color);
        ili9488_8080_draw_pixel(x + w - 1 - r + cx, y + r - cy, color);
        ili9488_8080_draw_pixel(x + w - 1 - r + cy, y + r - cx, color);
        ili9488_8080_draw_pixel(x + w - 1 - r + cx, y + h - 1 - r + cy, color);
        ili9488_8080_draw_pixel(x + w - 1 - r + cy, y + h - 1 - r + cx, color);
        ili9488_8080_draw_pixel(x + r - cx, y + h - 1 - r + cy, color);
        ili9488_8080_draw_pixel(x + r - cy, y + h - 1 - r + cx, color);
    }
}

void ili9488_8080_fill_round_rect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r, uint16_t color) {
    ili9488_8080_fill_rect(x + r, y, w - 2 * r, h, color);
    // Lados curvados
    int16_t f = 1 - r, ddF_x = 1, ddF_y = -2 * r, cx = 0, cy = r;
    while (cx < cy) {
        if (f >= 0) { cy--; ddF_y += 2; f += ddF_y; }
        cx++; ddF_x += 2; f += ddF_x;
        ili9488_8080_draw_fast_v_line(x + r - cx, y + r - cy, h - 2 * r + 2 * cy, color);
        ili9488_8080_draw_fast_v_line(x + w - 1 - r + cx, y + r - cy, h - 2 * r + 2 * cy, color);
        ili9488_8080_draw_fast_v_line(x + r - cy, y + r - cx, h - 2 * r + 2 * cx, color);
        ili9488_8080_draw_fast_v_line(x + w - 1 - r + cy, y + r - cx, h - 2 * r + 2 * cx, color);
    }
}
