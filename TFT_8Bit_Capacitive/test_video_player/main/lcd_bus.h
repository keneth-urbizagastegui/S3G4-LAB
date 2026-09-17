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

#define LCD_OVERLAY_MAX_RECTS 4
#define LCD_OVERLAY_MAX_SPANS_PER_ROW 4
// Color clave RGB565 para las zonas transparentes de las capas LVGL.
// Verde puro (0x07E0) no forma parte del diseño de la OSD.
#define LCD_OVERLAY_COLOR_KEY 0x07E0u

typedef struct {
    int16_t x;
    int16_t y;
    int16_t w;
    int16_t h;
    bool enabled;
    int16_t nat_y_min; // Native coordinate row min (= x)
    int16_t nat_y_max; // Native coordinate row max (= x + w - 1)
    int16_t nat_x_min; // Native coordinate col min (= 319 - (y + h - 1))
    int16_t nat_x_max; // Native coordinate col max (= 319 - y)
} lcd_overlay_rect_t;

// Gestión de capas de superposición (overlay) en coordenadas apaisadas (LVGL)
void lcd_bus_set_overlay_rect(int id, int16_t x, int16_t y, int16_t w, int16_t h, bool enabled);
void lcd_bus_clear_overlays(void);
int lcd_bus_get_active_overlays(lcd_overlay_rect_t out_rects[LCD_OVERLAY_MAX_RECTS]);
bool lcd_bus_has_active_overlays(void);
const uint16_t *lcd_bus_get_overlay_buffer(void);
// Copia los tramos opacos ya indexados de una fila nativa al búfer de video.
// x_min/x_max limitan la copia a la intersección con una capa activa.
void lcd_bus_overlay_copy_row(uint16_t *dst_row, int phys_y, int x_min, int x_max);
void lcd_bus_overlay_update_from_lvgl(int16_t x1, int16_t y1, int16_t x2, int16_t y2, const uint16_t *src_pixels);
void lcd_bus_get_overlay_stats(int *out_rects, uint32_t *out_px);

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

// Fija la ventana de visualización una única vez por fotograma para direct blit
// Requiere haber llamado lcd_bus_lock() antes
esp_err_t lcd_bus_set_frame_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2);

// Lanzamiento asíncrono de franja DMA continuando la escritura de la ventana establecida.
// is_first=true envía comando 0x2C (RAMWR); is_first=false envía -1 (continuación sin comando)
esp_err_t lcd_bus_draw_strip_continue_async(const uint16_t *data, size_t len_bytes, bool is_first);

// Espera a que termine la transmisión DMA de la franja previa
// out_dma_us entrega el tiempo transcurrido en microsegundos si no es NULL
esp_err_t lcd_bus_wait_strip_done(uint32_t *out_dma_us);

// Sincronización y monitoreo del pin TE (Tearing Effect)
#include "driver/gpio.h"

esp_err_t lcd_bus_te_init(gpio_num_t pin);
bool lcd_bus_te_is_present(void);
float lcd_bus_te_get_hz(void);
float lcd_bus_te_get_jitter_ms(void);
uint32_t lcd_bus_te_get_period_us(void);
esp_err_t lcd_bus_wait_te(uint32_t timeout_us, uint32_t *out_wait_us);
void lcd_bus_te_purge(void);
void lcd_bus_te_perf_sample(uint32_t *out_pulses, float *out_hz, float *out_jitter_ms, bool *out_present);

#ifdef __cplusplus
}
#endif

#endif // LCD_BUS_H
