#ifndef UI_GLUE_H
#define UI_GLUE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "player.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    VIEW_MODE_STUDIO = 0,
    VIEW_MODE_FULLSCREEN = 1
} view_mode_t;

void ui_glue_init(void);
void ui_glue_update_cache(const player_status_t *st);
void ui_glue_tick(void);

void ui_glue_set_hud_forced(int mode);
int  ui_glue_get_hud_forced(void);
bool ui_glue_is_osd_visible(void);
void ui_glue_set_osd_visible(bool visible);
void ui_glue_set_view_mode(view_mode_t mode);
view_mode_t ui_glue_get_view_mode(void);

void ui_glue_get_published_info(char *title_buf, size_t max_len, int *track_idx, view_mode_t *vmode, int *hud_vis);

bool ui_glue_is_locked(void);
void ui_glue_unlock(void);
void ui_glue_run_uinav_test(void);

#ifdef __cplusplus
}
#endif

#endif // UI_GLUE_H
