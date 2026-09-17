#ifndef EEZ_LVGL_UI_STYLES_H
#define EEZ_LVGL_UI_STYLES_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Style: st_screen
lv_style_t *get_style_st_screen_MAIN_DEFAULT();
void add_style_st_screen(lv_obj_t *obj);
void remove_style_st_screen(lv_obj_t *obj);

// Style: st_bar
lv_style_t *get_style_st_bar_MAIN_DEFAULT();
void add_style_st_bar(lv_obj_t *obj);
void remove_style_st_bar(lv_obj_t *obj);

// Style: st_icon_btn
lv_style_t *get_style_st_icon_btn_MAIN_DEFAULT();
lv_style_t *get_style_st_icon_btn_MAIN_PRESSED();
void add_style_st_icon_btn(lv_obj_t *obj);
void remove_style_st_icon_btn(lv_obj_t *obj);

// Style: st_play_btn
lv_style_t *get_style_st_play_btn_MAIN_DEFAULT();
lv_style_t *get_style_st_play_btn_MAIN_PRESSED();
void add_style_st_play_btn(lv_obj_t *obj);
void remove_style_st_play_btn(lv_obj_t *obj);

// Style: st_card
lv_style_t *get_style_st_card_MAIN_DEFAULT();
lv_style_t *get_style_st_card_MAIN_PRESSED();
void add_style_st_card(lv_obj_t *obj);
void remove_style_st_card(lv_obj_t *obj);

// Style: st_seek
lv_style_t *get_style_st_seek_MAIN_DEFAULT();
lv_style_t *get_style_st_seek_INDICATOR_DEFAULT();
lv_style_t *get_style_st_seek_KNOB_DEFAULT();
lv_style_t *get_style_st_seek_KNOB_PRESSED();
void add_style_st_seek(lv_obj_t *obj);
void remove_style_st_seek(lv_obj_t *obj);

// Style: st_chip
lv_style_t *get_style_st_chip_MAIN_DEFAULT();
void add_style_st_chip(lv_obj_t *obj);
void remove_style_st_chip(lv_obj_t *obj);

// Style: st_list_item
lv_style_t *get_style_st_list_item_MAIN_DEFAULT();
lv_style_t *get_style_st_list_item_MAIN_PRESSED();
void add_style_st_list_item(lv_obj_t *obj);
void remove_style_st_list_item(lv_obj_t *obj);

// Style: st_card_btn
lv_style_t *get_style_st_card_btn_MAIN_DEFAULT();
lv_style_t *get_style_st_card_btn_MAIN_PRESSED();
void add_style_st_card_btn(lv_obj_t *obj);
void remove_style_st_card_btn(lv_obj_t *obj);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_STYLES_H*/