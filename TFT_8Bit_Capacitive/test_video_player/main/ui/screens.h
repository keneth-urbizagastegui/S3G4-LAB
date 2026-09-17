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
    SCREEN_ID_SCR_QUEUE = 4,
    SCREEN_ID_SCR_SETTINGS = 5,
    _SCREEN_ID_LAST = 5
};

typedef struct _objects_t {
    lv_obj_t *scr_player;
    lv_obj_t *scr_library;
    lv_obj_t *scr_no_media;
    lv_obj_t *scr_queue;
    lv_obj_t *scr_settings;
    lv_obj_t *player_touch;
    lv_obj_t *osd_top;
    lv_obj_t *btn_back;
    lv_obj_t *lbl_title;
    lv_obj_t *lbl_subtitle;
    lv_obj_t *chip_fps;
    lv_obj_t *obj0;
    lv_obj_t *btn_queue;
    lv_obj_t *osd_bottom;
    lv_obj_t *lbl_pos;
    lv_obj_t *sld_seek;
    lv_obj_t *lbl_dur;
    lv_obj_t *btn_lock;
    lv_obj_t *btn_repeat;
    lv_obj_t *img_repeat_icon;
    lv_obj_t *btn_prev;
    lv_obj_t *btn_rew;
    lv_obj_t *btn_play;
    lv_obj_t *lbl_play_icon;
    lv_obj_t *btn_fwd;
    lv_obj_t *btn_next;
    lv_obj_t *btn_shuffle;
    lv_obj_t *img_shuffle_icon;
    lv_obj_t *btn_settings;
    lv_obj_t *bar_mini_progress;
    lv_obj_t *ovl_lock;
    lv_obj_t *ovl_brightness;
    lv_obj_t *bar_brightness;
    lv_obj_t *lbl_bri;
    lv_obj_t *ovl_seek_hint;
    lv_obj_t *img_seek_hint;
    lv_obj_t *lbl_seek_hint;
    lv_obj_t *ovl_stats;
    lv_obj_t *obj1;
    lv_obj_t *btn_stats_close;
    lv_obj_t *obj2;
    lv_obj_t *lbl_stat_pres;
    lv_obj_t *obj3;
    lv_obj_t *lbl_stat_dec;
    lv_obj_t *obj4;
    lv_obj_t *lbl_stat_drop;
    lv_obj_t *obj5;
    lv_obj_t *lbl_stat_rd;
    lv_obj_t *obj6;
    lv_obj_t *lbl_stat_dec_time;
    lv_obj_t *obj7;
    lv_obj_t *lbl_stat_blit;
    lv_obj_t *obj8;
    lv_obj_t *lbl_stat_file;
    lv_obj_t *lib_header;
    lv_obj_t *lbl_lib_title;
    lv_obj_t *lbl_lib_count;
    lv_obj_t *btn_lib_settings;
    lv_obj_t *bar_scan;
    lv_obj_t *lib_grid;
    lv_obj_t *img_nomedia;
    lv_obj_t *lbl_nomedia_title;
    lv_obj_t *lbl_nomedia_sub;
    lv_obj_t *chip_err;
    lv_obj_t *obj9;
    lv_obj_t *btn_retry;
    lv_obj_t *obj10;
    lv_obj_t *btn_settings_alt;
    lv_obj_t *obj11;
    lv_obj_t *lbl_retry_hint;
    lv_obj_t *queue_scrim;
    lv_obj_t *queue_sheet;
    lv_obj_t *lbl_queue_title;
    lv_obj_t *btn_queue_close;
    lv_obj_t *queue_list;
    lv_obj_t *queue_footer;
    lv_obj_t *btn_q_repeat;
    lv_obj_t *img_q_repeat;
    lv_obj_t *btn_q_shuffle;
    lv_obj_t *img_q_shuffle;
    lv_obj_t *lbl_q_mode;
    lv_obj_t *settings_nav;
    lv_obj_t *btn_back_settings;
    lv_obj_t *obj12;
    lv_obj_t *btn_tab_0;
    lv_obj_t *lbl_tab_0;
    lv_obj_t *btn_tab_1;
    lv_obj_t *lbl_tab_1;
    lv_obj_t *btn_tab_2;
    lv_obj_t *lbl_tab_2;
    lv_obj_t *btn_tab_3;
    lv_obj_t *lbl_tab_3;
    lv_obj_t *settings_panel;
    lv_obj_t *panel_tab_0;
    lv_obj_t *obj13;
    lv_obj_t *lbl_set_bri_val;
    lv_obj_t *sld_brightness;
    lv_obj_t *obj14;
    lv_obj_t *dd_osd_timeout;
    lv_obj_t *obj15;
    lv_obj_t *sw_show_stats;
    lv_obj_t *obj16;
    lv_obj_t *sw_mini_progress;
    lv_obj_t *panel_tab_1;
    lv_obj_t *obj17;
    lv_obj_t *dd_repeat;
    lv_obj_t *obj18;
    lv_obj_t *sw_shuffle;
    lv_obj_t *obj19;
    lv_obj_t *obj20;
    lv_obj_t *sw_resume;
    lv_obj_t *obj21;
    lv_obj_t *dd_seek_step;
    lv_obj_t *panel_tab_2;
    lv_obj_t *card_sd;
    lv_obj_t *lbl_sd_name;
    lv_obj_t *lbl_sd_fs;
    lv_obj_t *bar_sd_usage;
    lv_obj_t *lbl_sd_free;
    lv_obj_t *obj22;
    lv_obj_t *lbl_sd_speed;
    lv_obj_t *obj23;
    lv_obj_t *lbl_sd_count;
    lv_obj_t *btn_rescan;
    lv_obj_t *obj24;
    lv_obj_t *panel_tab_3;
    lv_obj_t *obj25;
    lv_obj_t *obj26;
    lv_obj_t *obj27;
    lv_obj_t *lbl_about_fw;
    lv_obj_t *obj28;
    lv_obj_t *lbl_about_idf;
    lv_obj_t *obj29;
    lv_obj_t *lbl_about_lvgl;
    lv_obj_t *obj30;
    lv_obj_t *lbl_about_panel;
    lv_obj_t *obj31;
    lv_obj_t *lbl_about_te;
    lv_obj_t *btn_open_stats;
    lv_obj_t *obj32;
} objects_t;

extern objects_t objects;

void create_screen_scr_player();
void tick_screen_scr_player();

void create_screen_scr_library();
void tick_screen_scr_library();

void create_screen_scr_no_media();
void tick_screen_scr_no_media();

void create_screen_scr_queue();
void tick_screen_scr_queue();

void create_screen_scr_settings();
void tick_screen_scr_settings();

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