#ifndef ILI9488_8080_H
#define ILI9488_8080_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define LCD_WIDTH   480
#define LCD_HEIGHT  320

// Colores RGB565 estandar
#define COLOR_BLACK       0x0000
#define COLOR_WHITE       0xFFFF
#define COLOR_RED         0xF800
#define COLOR_GREEN       0x07E0
#define COLOR_BLUE        0x001F
#define COLOR_YELLOW      0xFFE0
#define COLOR_CYAN        0x07FF
#define COLOR_MAGENTA     0xF81F
#define COLOR_GRAY        0x7BEF
#define COLOR_DARKGRAY    0x39E7
#define COLOR_NAVY        0x000F
#define COLOR_DARKGREEN   0x03E0
#define COLOR_DARKCYAN    0x03EF
#define COLOR_MAROON      0x7800
#define COLOR_PURPLE      0x780F
#define COLOR_ORANGE      0xFD20
#define COLOR_GOLD        0xFEA0

// Inicializacion con Overclock a 16 MHz (128 Mbps sobre bus paralelo de 8 bits)
esp_err_t ili9488_8080_init_clock(uint32_t freq_hz);
esp_err_t ili9488_8080_init(void);

esp_err_t ili9488_8080_fill_screen(uint16_t color);
esp_err_t ili9488_8080_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
void ili9488_8080_draw_pixel(uint16_t x, uint16_t y, uint16_t color);
void ili9488_8080_draw_line(int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint16_t color);
void ili9488_8080_draw_fast_h_line(int16_t x, int16_t y, int16_t w, uint16_t color);
void ili9488_8080_draw_fast_v_line(int16_t x, int16_t y, int16_t h, uint16_t color);
void ili9488_8080_draw_rect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);
void ili9488_8080_draw_circle(int16_t x0, int16_t y0, int16_t r, uint16_t color);
void ili9488_8080_fill_circle(int16_t x0, int16_t y0, int16_t r, uint16_t color);
void ili9488_8080_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg, uint8_t size);
void ili9488_8080_draw_string(uint16_t x, uint16_t y, const char *str, uint16_t fg, uint16_t bg, uint8_t size);
esp_err_t ili9488_8080_draw_bitmap(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, const uint16_t *data);
void ili9488_8080_set_backlight(uint8_t brightness_pct);
void board_turn_off_rgb_led(void);

#ifdef __cplusplus
}
#endif

#endif // ILI9488_8080_H
