#ifndef FT6236_I2C_H
#define FT6236_I2C_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint16_t x1;
    uint16_t y1;
    uint16_t x2;
    uint16_t y2;
    uint16_t x;          // Alias retrocompatible de x1
    uint16_t y;          // Alias retrocompatible de y1
    uint8_t touch_count; // Número de puntos detectados por hardware (0, 1 o 2)
    bool touched;
} ft6236_touch_data_t;

/**
 * @brief Inicializa el bus I2C maestro y registra el dispositivo FT6236 (dirección 0x38).
 */
esp_err_t ft6236_i2c_init(void);

/**
 * @brief Lee las coordenadas táctiles actuales.
 * @param[out] data Puntero a la estructura donde se devuelven las coordenadas.
 * @return ESP_OK si se leyó correctamente.
 */
esp_err_t ft6236_i2c_read(ft6236_touch_data_t *data);

#ifdef __cplusplus
}
#endif

#endif // FT6236_I2C_H
