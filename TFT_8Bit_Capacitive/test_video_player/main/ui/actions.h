#ifndef EEZ_LVGL_UI_EVENTS_H
#define EEZ_LVGL_UI_EVENTS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

extern void action_toggle_play(lv_event_t * e);
extern void action_prev(lv_event_t * e);
extern void action_next(lv_event_t * e);
extern void action_rew10(lv_event_t * e);
extern void action_fwd10(lv_event_t * e);
extern void action_seek_begin(lv_event_t * e);
extern void action_seek_preview(lv_event_t * e);
extern void action_seek_commit(lv_event_t * e);
extern void action_cycle_repeat(lv_event_t * e);
extern void action_toggle_shuffle(lv_event_t * e);
extern void action_lock(lv_event_t * e);
extern void action_toggle_osd(lv_event_t * e);
extern void action_open_library(lv_event_t * e);
extern void action_open_queue(lv_event_t * e);
extern void action_close_queue(lv_event_t * e);
extern void action_open_settings(lv_event_t * e);
extern void action_settings_tab(lv_event_t * e);
extern void action_open_stats(lv_event_t * e);
extern void action_play_index(lv_event_t * e);
extern void action_rescan(lv_event_t * e);
extern void action_library_populate(lv_event_t * e);
extern void action_set_brightness(lv_event_t * e);
extern void action_set_osd_timeout(lv_event_t * e);
extern void action_set_show_stats(lv_event_t * e);
extern void action_set_mini_progress(lv_event_t * e);
extern void action_set_repeat(lv_event_t * e);
extern void action_set_shuffle(lv_event_t * e);
extern void action_set_resume(lv_event_t * e);
extern void action_set_seek_step(lv_event_t * e);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_EVENTS_H*/