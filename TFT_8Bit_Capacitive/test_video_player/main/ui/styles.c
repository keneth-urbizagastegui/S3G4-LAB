#include "styles.h"
#include "images.h"
#include "fonts.h"

#include "ui.h"
#include "screens.h"

//
// Style: st_screen
//

void init_style_st_screen_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][0]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_pad_top(style, 0);
    lv_style_set_pad_bottom(style, 0);
    lv_style_set_pad_left(style, 0);
    lv_style_set_pad_right(style, 0);
    lv_style_set_border_width(style, 0);
    lv_style_set_radius(style, 0);
};

lv_style_t *get_style_st_screen_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_screen_MAIN_DEFAULT(style);
    }
    return style;
};

void add_style_st_screen(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_screen_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
};

void remove_style_st_screen(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_screen_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
};

//
// Style: st_bar
//

void init_style_st_bar_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][0]));
    lv_style_set_bg_opa(style, 217);
    lv_style_set_pad_top(style, 0);
    lv_style_set_pad_bottom(style, 0);
    lv_style_set_pad_left(style, 0);
    lv_style_set_pad_right(style, 0);
    lv_style_set_border_width(style, 1);
    lv_style_set_border_color(style, lv_color_hex(theme_colors[active_theme_index][3]));
    lv_style_set_border_side(style, LV_BORDER_SIDE_BOTTOM);
    lv_style_set_radius(style, 0);
};

lv_style_t *get_style_st_bar_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_bar_MAIN_DEFAULT(style);
    }
    return style;
};

void add_style_st_bar(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_bar_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
};

void remove_style_st_bar(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_bar_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
};

//
// Style: st_icon_btn
//

void init_style_st_icon_btn_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_opa(style, 0);
    lv_style_set_radius(style, 255);
    lv_style_set_pad_top(style, 0);
    lv_style_set_pad_bottom(style, 0);
    lv_style_set_pad_left(style, 0);
    lv_style_set_pad_right(style, 0);
    lv_style_set_border_width(style, 0);
    lv_style_set_shadow_width(style, 0);
};

lv_style_t *get_style_st_icon_btn_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_icon_btn_MAIN_DEFAULT(style);
    }
    return style;
};

void init_style_st_icon_btn_MAIN_PRESSED(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][2]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 22);
};

lv_style_t *get_style_st_icon_btn_MAIN_PRESSED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_icon_btn_MAIN_PRESSED(style);
    }
    return style;
};

void init_style_st_icon_btn_MAIN_CHECKED(lv_style_t *style) {
    lv_style_set_bg_opa(style, 0);
};

lv_style_t *get_style_st_icon_btn_MAIN_CHECKED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_icon_btn_MAIN_CHECKED(style);
    }
    return style;
};

void add_style_st_icon_btn(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_icon_btn_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_icon_btn_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
    lv_obj_add_style(obj, get_style_st_icon_btn_MAIN_CHECKED(), LV_PART_MAIN | LV_STATE_CHECKED);
};

void remove_style_st_icon_btn(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_icon_btn_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_icon_btn_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
    lv_obj_remove_style(obj, get_style_st_icon_btn_MAIN_CHECKED(), LV_PART_MAIN | LV_STATE_CHECKED);
};

//
// Style: st_play_btn
//

void init_style_st_play_btn_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][6]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 255);
    lv_style_set_pad_top(style, 0);
    lv_style_set_pad_bottom(style, 0);
    lv_style_set_pad_left(style, 0);
    lv_style_set_pad_right(style, 0);
    lv_style_set_border_width(style, 0);
    lv_style_set_shadow_width(style, 0);
};

lv_style_t *get_style_st_play_btn_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_play_btn_MAIN_DEFAULT(style);
    }
    return style;
};

void init_style_st_play_btn_MAIN_PRESSED(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][6]));
    lv_style_set_bg_opa(style, 180);
};

lv_style_t *get_style_st_play_btn_MAIN_PRESSED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_play_btn_MAIN_PRESSED(style);
    }
    return style;
};

void add_style_st_play_btn(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_play_btn_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_play_btn_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

void remove_style_st_play_btn(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_play_btn_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_play_btn_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

//
// Style: st_card
//

void init_style_st_card_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][1]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 8);
    lv_style_set_pad_top(style, 0);
    lv_style_set_pad_bottom(style, 0);
    lv_style_set_pad_left(style, 0);
    lv_style_set_pad_right(style, 0);
    lv_style_set_border_width(style, 1);
    lv_style_set_border_color(style, lv_color_hex(theme_colors[active_theme_index][3]));
    lv_style_set_shadow_width(style, 0);
};

lv_style_t *get_style_st_card_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_card_MAIN_DEFAULT(style);
    }
    return style;
};

void init_style_st_card_MAIN_PRESSED(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][2]));
    lv_style_set_bg_opa(style, 255);
};

lv_style_t *get_style_st_card_MAIN_PRESSED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_card_MAIN_PRESSED(style);
    }
    return style;
};

void add_style_st_card(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_card_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_card_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

void remove_style_st_card(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_card_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_card_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

//
// Style: st_seek
//

void init_style_st_seek_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][3]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 3);
};

lv_style_t *get_style_st_seek_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_seek_MAIN_DEFAULT(style);
    }
    return style;
};

void init_style_st_seek_INDICATOR_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][6]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 3);
};

lv_style_t *get_style_st_seek_INDICATOR_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_seek_INDICATOR_DEFAULT(style);
    }
    return style;
};

void init_style_st_seek_KNOB_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][6]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 255);
    lv_style_set_pad_top(style, 4);
    lv_style_set_pad_bottom(style, 4);
    lv_style_set_pad_left(style, 4);
    lv_style_set_pad_right(style, 4);
};

lv_style_t *get_style_st_seek_KNOB_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_seek_KNOB_DEFAULT(style);
    }
    return style;
};

void init_style_st_seek_KNOB_PRESSED(lv_style_t *style) {
    lv_style_set_pad_top(style, 7);
    lv_style_set_pad_bottom(style, 7);
    lv_style_set_pad_left(style, 7);
    lv_style_set_pad_right(style, 7);
};

lv_style_t *get_style_st_seek_KNOB_PRESSED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_seek_KNOB_PRESSED(style);
    }
    return style;
};

void add_style_st_seek(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_seek_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_seek_INDICATOR_DEFAULT(), LV_PART_INDICATOR | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_seek_KNOB_DEFAULT(), LV_PART_KNOB | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_seek_KNOB_PRESSED(), LV_PART_KNOB | LV_STATE_PRESSED);
};

void remove_style_st_seek(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_seek_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_seek_INDICATOR_DEFAULT(), LV_PART_INDICATOR | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_seek_KNOB_DEFAULT(), LV_PART_KNOB | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_seek_KNOB_PRESSED(), LV_PART_KNOB | LV_STATE_PRESSED);
};

//
// Style: st_chip
//

void init_style_st_chip_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][1]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 10);
    lv_style_set_border_width(style, 1);
    lv_style_set_border_color(style, lv_color_hex(theme_colors[active_theme_index][3]));
    lv_style_set_pad_top(style, 2);
    lv_style_set_pad_bottom(style, 2);
    lv_style_set_pad_left(style, 6);
    lv_style_set_pad_right(style, 6);
};

lv_style_t *get_style_st_chip_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_chip_MAIN_DEFAULT(style);
    }
    return style;
};

void add_style_st_chip(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_chip_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
};

void remove_style_st_chip(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_chip_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
};

//
// Style: st_list_item
//

void init_style_st_list_item_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_opa(style, 0);
    lv_style_set_border_width(style, 1);
    lv_style_set_border_color(style, lv_color_hex(theme_colors[active_theme_index][3]));
    lv_style_set_border_side(style, LV_BORDER_SIDE_BOTTOM);
    lv_style_set_radius(style, 0);
};

lv_style_t *get_style_st_list_item_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_list_item_MAIN_DEFAULT(style);
    }
    return style;
};

void init_style_st_list_item_MAIN_PRESSED(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][2]));
    lv_style_set_bg_opa(style, 255);
};

lv_style_t *get_style_st_list_item_MAIN_PRESSED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_list_item_MAIN_PRESSED(style);
    }
    return style;
};

void add_style_st_list_item(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_list_item_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_list_item_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

void remove_style_st_list_item(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_list_item_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_list_item_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

//
// Style: st_card_btn
//

void init_style_st_card_btn_MAIN_DEFAULT(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][1]));
    lv_style_set_bg_opa(style, 255);
    lv_style_set_radius(style, 8);
    lv_style_set_border_width(style, 1);
    lv_style_set_border_color(style, lv_color_hex(theme_colors[active_theme_index][3]));
    lv_style_set_shadow_width(style, 0);
};

lv_style_t *get_style_st_card_btn_MAIN_DEFAULT() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_card_btn_MAIN_DEFAULT(style);
    }
    return style;
};

void init_style_st_card_btn_MAIN_PRESSED(lv_style_t *style) {
    lv_style_set_bg_color(style, lv_color_hex(theme_colors[active_theme_index][2]));
    lv_style_set_bg_opa(style, 255);
};

lv_style_t *get_style_st_card_btn_MAIN_PRESSED() {
    static lv_style_t *style;
    if (!style) {
        style = (lv_style_t *)lv_malloc(sizeof(lv_style_t));
        lv_style_init(style);
        init_style_st_card_btn_MAIN_PRESSED(style);
    }
    return style;
};

void add_style_st_card_btn(lv_obj_t *obj) {
    (void)obj;
    lv_obj_add_style(obj, get_style_st_card_btn_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, get_style_st_card_btn_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
};

void remove_style_st_card_btn(lv_obj_t *obj) {
    (void)obj;
    lv_obj_remove_style(obj, get_style_st_card_btn_MAIN_DEFAULT(), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_remove_style(obj, get_style_st_card_btn_MAIN_PRESSED(), LV_PART_MAIN | LV_STATE_PRESSED);
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
        add_style_st_card_btn,
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
        remove_style_st_card_btn,
    };
    remove_style_funcs[styleIndex](obj);
}