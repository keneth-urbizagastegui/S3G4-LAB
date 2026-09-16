#ifndef EEZ_LVGL_UI_VARS_H
#define EEZ_LVGL_UI_VARS_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// enum declarations

// Flow global variables

enum FlowGlobalVariables {
    FLOW_GLOBAL_VARIABLE_TITLE = 0,
    FLOW_GLOBAL_VARIABLE_SUBTITLE = 1,
    FLOW_GLOBAL_VARIABLE_POS_TEXT = 2,
    FLOW_GLOBAL_VARIABLE_DUR_TEXT = 3,
    FLOW_GLOBAL_VARIABLE_SEEK_VALUE = 4,
    FLOW_GLOBAL_VARIABLE_IS_PLAYING = 5,
    FLOW_GLOBAL_VARIABLE_REPEAT_MODE = 6,
    FLOW_GLOBAL_VARIABLE_SHUFFLE = 7,
    FLOW_GLOBAL_VARIABLE_FPS_TEXT = 8,
    FLOW_GLOBAL_VARIABLE_SHOW_STATS = 9,
    FLOW_GLOBAL_VARIABLE_LIBRARY_SUMMARY = 10,
    FLOW_GLOBAL_VARIABLE_BRIGHTNESS = 11,
    FLOW_GLOBAL_VARIABLE_STATS_PRES_FPS = 12,
    FLOW_GLOBAL_VARIABLE_STATS_DEC_FPS = 13,
    FLOW_GLOBAL_VARIABLE_STATS_DROPPED = 14,
    FLOW_GLOBAL_VARIABLE_STATS_READ = 15,
    FLOW_GLOBAL_VARIABLE_STATS_DECODE = 16,
    FLOW_GLOBAL_VARIABLE_STATS_BLIT = 17,
    FLOW_GLOBAL_VARIABLE_STATS_FILE = 18
};

// Native global variables

extern const char *get_var_title();
extern void set_var_title(const char *value);
extern const char *get_var_subtitle();
extern void set_var_subtitle(const char *value);
extern const char *get_var_pos_text();
extern void set_var_pos_text(const char *value);
extern const char *get_var_dur_text();
extern void set_var_dur_text(const char *value);
extern int32_t get_var_seek_value();
extern void set_var_seek_value(int32_t value);
extern bool get_var_is_playing();
extern void set_var_is_playing(bool value);
extern int32_t get_var_repeat_mode();
extern void set_var_repeat_mode(int32_t value);
extern bool get_var_shuffle();
extern void set_var_shuffle(bool value);
extern const char *get_var_fps_text();
extern void set_var_fps_text(const char *value);
extern bool get_var_show_stats();
extern void set_var_show_stats(bool value);
extern const char *get_var_library_summary();
extern void set_var_library_summary(const char *value);
extern int32_t get_var_brightness();
extern void set_var_brightness(int32_t value);
extern const char *get_var_stats_pres_fps();
extern void set_var_stats_pres_fps(const char *value);
extern const char *get_var_stats_dec_fps();
extern void set_var_stats_dec_fps(const char *value);
extern const char *get_var_stats_dropped();
extern void set_var_stats_dropped(const char *value);
extern const char *get_var_stats_read();
extern void set_var_stats_read(const char *value);
extern const char *get_var_stats_decode();
extern void set_var_stats_decode(const char *value);
extern const char *get_var_stats_blit();
extern void set_var_stats_blit(const char *value);
extern const char *get_var_stats_file();
extern void set_var_stats_file(const char *value);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_VARS_H*/