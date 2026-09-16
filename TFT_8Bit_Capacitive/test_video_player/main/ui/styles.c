#include "styles.h"
#include "images.h"
#include "fonts.h"

#include "ui.h"
#include "screens.h"

//
// Style: st_screen
//

void add_style_st_screen(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_screen(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_bar
//

void add_style_st_bar(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_bar(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_icon_btn
//

void add_style_st_icon_btn(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_icon_btn(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_play_btn
//

void add_style_st_play_btn(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_play_btn(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_card
//

void add_style_st_card(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_card(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_seek
//

void add_style_st_seek(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_seek(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_chip
//

void add_style_st_chip(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_chip(lv_obj_t *obj) {
    (void)obj;
};

//
// Style: st_list_item
//

void add_style_st_list_item(lv_obj_t *obj) {
    (void)obj;
};

void remove_style_st_list_item(lv_obj_t *obj) {
    (void)obj;
};

//
//
//

void add_style(lv_obj_t *obj, int32_t styleIndex) {
    typedef void (*AddStyleFunc)(lv_obj_t *obj);
    static const AddStyleFunc add_style_funcs[] = {
        add_style_st_screen,
        add_style_st_bar,
        add_style_st_icon_btn,
        add_style_st_play_btn,
        add_style_st_card,
        add_style_st_seek,
        add_style_st_chip,
        add_style_st_list_item,
    };
    add_style_funcs[styleIndex](obj);
}

void remove_style(lv_obj_t *obj, int32_t styleIndex) {
    typedef void (*RemoveStyleFunc)(lv_obj_t *obj);
    static const RemoveStyleFunc remove_style_funcs[] = {
        remove_style_st_screen,
        remove_style_st_bar,
        remove_style_st_icon_btn,
        remove_style_st_play_btn,
        remove_style_st_card,
        remove_style_st_seek,
        remove_style_st_chip,
        remove_style_st_list_item,
    };
    remove_style_funcs[styleIndex](obj);
}