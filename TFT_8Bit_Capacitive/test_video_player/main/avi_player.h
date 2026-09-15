#ifndef AVI_PLAYER_H
#define AVI_PLAYER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t width;
    uint32_t height;
    uint32_t fps;
    uint32_t us_per_frame;
    uint32_t total_frames;
    uint32_t duration_sec;
    uint32_t current_frame;
    uint32_t elapsed_sec;
    bool is_open;
    bool is_eof;
} avi_info_t;

esp_err_t avi_player_init(void);
esp_err_t avi_player_open(const char *filepath);
void avi_player_close(void);

// Decodifica el siguiente cuadro a un búfer RGB565 utilizando aceleración SIMD en ESP32-S3 (esp_new_jpeg)
// scale: 0 = 1:1 (480x320 Fullscreen), 1 = 1/2 (240x160 Studio)
esp_err_t avi_player_read_next_frame(uint16_t *out_rgb565, uint8_t scale);

// Salta el siguiente cuadro sin decodificar (lectura de cabecera de chunk + fseek)
esp_err_t avi_player_skip_next_frame(void);

void avi_player_seek_percent(int percent);
void avi_player_restart(void);

const avi_info_t *avi_player_get_info(void);

// Registro de informacion de medio (formato MEDIA)
void avi_player_log_media(const char *filepath);

// Escaneo dinamico de MicroSD
int media_scan_sdcard(void);
int media_get_avi_count(void);
const char *media_get_avi_path(int index);

#ifdef __cplusplus
}
#endif

#endif // AVI_PLAYER_H
