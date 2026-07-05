#ifndef HAL_DISPLAY_H
#define HAL_DISPLAY_H

#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <lvgl.h>

// Handle global al controlador LCD, necesario para operaciones directas como inversión
extern esp_lcd_panel_handle_t lcd_handle;

/**
 * @brief Inicializa toda la capa física de display: LEDC (backlight), SPI, LCD (ILI9488 IPS), LVGL y panel táctil.
 */
void hal_display_init(void);

/**
 * @brief Cambia el nivel de brillo de la pantalla.
 * @param brightness_percentage Porcentaje de brillo (0 a 100).
 */
void display_brightness_set(int brightness_percentage);

/**
 * @brief Invierte los colores en la pantalla a nivel de hardware (ILI9488 register command).
 */
void update_display_inversion(void);

#endif // HAL_DISPLAY_H
