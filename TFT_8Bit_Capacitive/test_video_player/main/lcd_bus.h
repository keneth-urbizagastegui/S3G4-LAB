#ifndef LCD_BUS_H
#define LCD_BUS_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int16_t x;
    int16_t y;
    int16_t w;
    int16_t h;
} lcd_video_rect_t;

// Inicializa el bus LCD y su mutex recursivo
void lcd_bus_init(void);

// Mutex recursivo del bus LCD (compartido entre direct blit y LVGL flush)
void lcd_bus_lock(void);
void lcd_bus_unlock(void);

// Configuración de la región de video activa (para recorte y direct blit)
void lcd_bus_set_video_rect(int16_t x, int16_t y, int16_t w, int16_t h);
void lcd_bus_get_video_rect(int16_t *x, int16_t *y, int16_t *w, int16_t *h);

// Lanzamiento asíncrono de transmisión DMA de una franja de video con set_window propio
// Requiere haber llamado lcd_bus_lock() antes
esp_err_t lcd_bus_draw_strip_async(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, const uint16_t *data, size_t len_bytes);

// Espera a que termine la transmisión DMA de la franja previa
// out_dma_us entrega el tiempo transcurrido en microsegundos si no es NULL
esp_err_t lcd_bus_wait_strip_done(uint32_t *out_dma_us);

#ifdef __cplusplus
}
#endif

#endif // LCD_BUS_H
