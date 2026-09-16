#ifndef EEZ_LVGL_UI_STYLES_H
#define EEZ_LVGL_UI_STYLES_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Style: st_screen
void add_style_st_screen(lv_obj_t *obj);
void remove_style_st_screen(lv_obj_t *obj);

// Style: st_bar
void add_style_st_bar(lv_obj_t *obj);
void remove_style_st_bar(lv_obj_t *obj);

// Style: st_icon_btn
void add_style_st_icon_btn(lv_obj_t *obj);
void remove_style_st_icon_btn(lv_obj_t *obj);

// Style: st_play_btn
void add_style_st_play_btn(lv_obj_t *obj);
void remove_style_st_play_btn(lv_obj_t *obj);

// Style: st_card
void add_style_st_card(lv_obj_t *obj);
void remove_style_st_card(lv_obj_t *obj);

// Style: st_card_btn
void add_style_st_card_btn(lv_obj_t *obj);
void remove_style_st_card_btn(lv_obj_t *obj);

// Style: st_seek
void add_style_st_seek(lv_obj_t *obj);
void remove_style_st_seek(lv_obj_t *obj);

// Style: st_chip
void add_style_st_chip(lv_obj_t *obj);
void remove_style_st_chip(lv_obj_t *obj);

// Style: st_list_item
void add_style_st_list_item(lv_obj_t *obj);
void remove_style_st_list_item(lv_obj_t *obj);

void add_style(lv_obj_t *obj, int32_t styleIndex);
void remove_style(lv_obj_t *obj, int32_t styleIndex);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_STYLES_H*/