#ifndef SPOTIFY_UI_H
#define SPOTIFY_UI_H

#include <stdint.h>
#include <stdbool.h>
#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    PLAYBACK_STATE_PLAYING = 0,
    PLAYBACK_STATE_PAUSED,
    PLAYBACK_STATE_STOPPED,
} playback_state_t;

typedef enum {
    VIEW_MODE_STUDIO = 0,
    VIEW_MODE_FULLSCREEN,
} view_mode_t;

typedef struct {
    const char *title;
    const char *artist;
    const char *filepath;
} track_meta_t;

#define PLAYLIST_SIZE 4
extern const track_meta_t g_playlist[PLAYLIST_SIZE];

typedef void (*track_change_cb_t)(int new_index);
typedef void (*playback_ctrl_cb_t)(playback_state_t state);
typedef void (*seek_cb_t)(int percent);

void spotify_ui_init(track_change_cb_t track_cb, playback_ctrl_cb_t play_cb, seek_cb_t seek_cb);
void spotify_ui_update_progress(uint32_t elapsed_sec, uint32_t duration_sec, int percent);
void spotify_ui_update_fps(float fps);
void spotify_ui_tick(void);

void spotify_ui_set_track(int index);
void spotify_ui_set_play_state(playback_state_t state);
void spotify_ui_set_view_mode(view_mode_t mode);
void spotify_ui_set_hud_forced(int mode);
view_mode_t spotify_ui_get_view_mode(void);
playback_state_t spotify_ui_get_play_state(void);

uint16_t *spotify_ui_get_studio_buffer(void);
uint16_t *spotify_ui_get_fullscreen_buffer(void);
void spotify_ui_commit_frame(void);
void spotify_ui_invalidate_video(void);

#ifdef __cplusplus
}
#endif

#endif // SPOTIFY_UI_H
