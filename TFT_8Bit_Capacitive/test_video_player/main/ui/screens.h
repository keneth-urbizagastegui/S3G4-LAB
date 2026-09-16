#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Screens

enum ScreensEnum {
    _SCREEN_ID_FIRST = 1,
    SCREEN_ID_SCR_PLAYER = 1,
    SCREEN_ID_SCR_LIBRARY = 2,
    SCREEN_ID_SCR_NO_MEDIA = 3,
    _SCREEN_ID_LAST = 3
};

typedef struct _objects_t {
    lv_obj_t *scr_player;
    lv_obj_t *scr_library;
    lv_obj_t *scr_no_media;
    lv_obj_t *player_touch;
    lv_obj_t *osd_top;
    lv_obj_t *btn_back;
    lv_obj_t *obj0;
    lv_obj_t *lbl_title;
    lv_obj_t *lbl_subtitle;
    lv_obj_t *chip_fps;
    lv_obj_t *obj1;
    lv_obj_t *btn_queue;
    lv_obj_t *osd_bottom;
    lv_obj_t *lbl_pos;
    lv_obj_t *sld_seek;
    lv_obj_t *lbl_dur;
    lv_obj_t *btn_lock;
    lv_obj_t *btn_repeat;
    lv_obj_t *obj2;
    lv_obj_t *btn_prev;
    lv_obj_t *obj3;
    lv_obj_t *btn_rew;
    lv_obj_t *btn_play;
    lv_obj_t *lbl_play_icon;
    lv_obj_t *btn_fwd;
    lv_obj_t *btn_next;
    lv_obj_t *obj4;
    lv_obj_t *btn_shuffle;
    lv_obj_t *obj5;
    lv_obj_t *btn_settings;
    lv_obj_t *obj6;
    lv_obj_t *bar_mini_progress;
    lv_obj_t *lib_header;
    lv_obj_t *lbl_lib_title;
    lv_obj_t *lbl_lib_count;
    lv_obj_t *btn_lib_settings;
    lv_obj_t *obj7;
    lv_obj_t *bar_scan;
    lv_obj_t *lib_grid;
    lv_obj_t *img_nomedia;
    lv_obj_t *lbl_nomedia_title;
    lv_obj_t *lbl_nomedia_sub;
    lv_obj_t *chip_err;
    lv_obj_t *obj8;
    lv_obj_t *btn_retry;
    lv_obj_t *obj9;
    lv_obj_t *btn_settings_alt;
    lv_obj_t *obj10;
    lv_obj_t *lbl_retry_hint;
} objects_t;

extern objects_t objects;

void create_screen_scr_player();
void tick_screen_scr_player();

void create_screen_scr_library();
void tick_screen_scr_library();

void create_screen_scr_no_media();
void tick_screen_scr_no_media();

void create_user_widget_uw_video_card(lv_obj_t *parent_obj, int startWidgetIndex);
void tick_user_widget_uw_video_card(int startWidgetIndex);

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();

// Color themes

enum Themes {
    THEME_ID_DEFAULT,
};
enum Colors {
    COLOR_ID_C_BG,
    COLOR_ID_C_SURFACE,
    COLOR_ID_C_SURFACE_HI,
    COLOR_ID_C_LINE,
    COLOR_ID_C_TEXT,
    COLOR_ID_C_MUTED,
    COLOR_ID_C_ACCENT,
    COLOR_ID_C_ON_ACCENT,
    COLOR_ID_C_DANGER,
};
void change_color_theme(uint32_t themeIndex);
extern uint32_t theme_colors[1][9];
extern uint32_t active_theme_index;

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/