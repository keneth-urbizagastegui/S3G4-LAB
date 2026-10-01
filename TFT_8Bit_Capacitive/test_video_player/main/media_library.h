#ifndef MEDIA_LIBRARY_H
#define MEDIA_LIBRARY_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char path[128];        // /sdcard/videos/harry.avi o /sdcard/harry.avi
    char title[64];        // del .json, o el nombre sin extension
    char subtitle[64];     // del .json ("artista"), o ""
    uint32_t dur_ms;       // de la cabecera AVI (frames * us_per_frame), NO del .json
    uint32_t frames;
    uint16_t w, h;
    uint32_t fps_milli;
    uint32_t chunk_max;    // recorriendo idx1 (ya se hace en la linea MEDIA)
    bool has_thumb;        // existe <nombre>.jpg
    void *thumb_dsc;       // lv_image_dsc_t* en PSRAM, NULL si no hay; lo rellena la UI en F6
    uint32_t resume_ms;    // posicion guardada en NVS, 0 si ninguna
    bool compatible;       // Seccion 7: formato compatible
    char incompat[48];     // motivo mostrado si falla (sin comas)
    bool rotated;          // true si 320x480 (girado), false si 480x320 (clasico)
    bool failed_playback;  // true si fallo la presentacion o el watchdog en esta sesion
} media_item_t;

typedef void (*media_scan_progress_cb_t)(int done, int total);

esp_err_t media_library_scan(void);     // escanea y ordena; devuelve ESP_OK aunque haya 0 videos
int  media_library_count(void);         // CONTADO, sin constantes
int  media_library_compatible_count(void);
const media_item_t *media_library_get(int index);
int  media_library_index_of(const char *path);
void media_library_set_progress_cb(media_scan_progress_cb_t cb);
void media_library_mark_failed(int index);
void media_library_set_resume(const char *path, uint32_t pos_ms);

#ifdef __cplusplus
}
#endif

#endif // MEDIA_LIBRARY_H
