#ifndef PLAYER_H
#define PLAYER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    PCMD_OPEN,
    PCMD_PLAY,
    PCMD_PAUSE,
    PCMD_TOGGLE,
    PCMD_STOP,
    PCMD_SEEK_MS,
    PCMD_SEEK_REL_MS,
    PCMD_NEXT,
    PCMD_PREV,
    PCMD_SET_REPEAT,
    PCMD_SET_SHUFFLE,
    PCMD_SET_VIDEO_RECT
} player_cmd_type_t;

typedef struct {
    player_cmd_type_t type;
    int32_t arg;
    char path[128];
    struct {
        int16_t x, y, w, h;
    } rect;
} player_cmd_t;

typedef enum {
    PST_IDLE,
    PST_PLAYING,
    PST_PAUSED,
    PST_ENDED,
    PST_ERROR,
    PST_NO_MEDIA
} player_state_t;

typedef enum {
    REPEAT_OFF,
    REPEAT_ALL,
    REPEAT_ONE
} repeat_mode_t;

typedef struct {
    player_state_t state;
    repeat_mode_t repeat;
    bool shuffle;
    int32_t track_index;
    int32_t track_count;
    uint64_t pos_ms, dur_ms;          // milisegundos, 64 bits (A3)
    uint16_t width, height;
    uint32_t fps_milli;               // 29970 = 29.97 fps
    float pres_fps, dec_fps;
    uint32_t dropped;
    char title[64];
    char subtitle[64];
    uint32_t err_code;
} player_status_t;

esp_err_t player_start(void);                       // crea la tarea en el núcleo 1
bool player_cmd_send(const player_cmd_t *c);        // no bloqueante (timeout 0); devuelve false si la cola está llena
void player_get_status(player_status_t *out);       // copia bajo spinlock
uint32_t player_get_repeat_loop_count(void);        // contador para la autoprueba S8
void player_reset_repeat_loop_metrics(void);
void player_get_repeat_loop_metrics(uint32_t *out_samples, uint32_t *out_gap_ms_max);

// Metadata auxiliar para consistencia UI y autotest
void player_get_track_title(int track_index, char *out_title, size_t max_len);
void player_get_track_subtitle(int track_index, char *out_sub, size_t max_len);

// Traspaso de fotogramas desacoplado (para consumo exclusivo de Core 0 / UI)
// Devuelve true si hay fotograma nuevo disponible y entrega puntero y dimensiones
bool player_check_and_clear_new_frame(uint16_t **out_frame_buf, int *out_w, int *out_h);

// Diagnóstico de memoria para Observación O2
uint32_t player_get_task_stack_high_water_mark(void);

#ifdef __cplusplus
}
#endif

#endif // PLAYER_H
