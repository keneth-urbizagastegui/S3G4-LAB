#include "styles.h"
#include "images.h"
#include "fonts.h"
#include "ui.h"
#include "screens.h"

// Tokens de color Fase 6a / D2
#define C_BG          lv_color_hex(0x0A0E14)
#define C_BG_OSD      lv_color_hex(0x0D1117)
#define C_SURFACE     lv_color_hex(0x161B22)
#define C_SURFACE_HI  lv_color_hex(0x1F242C)
#define C_LINE        lv_color_hex(0x21262D)
#define C_TEXT        lv_color_hex(0xF0F6FC)
#define C_MUTED       lv_color_hex(0x8E929B)
#define C_ACCENT      lv_color_hex(0x2563EB)
#define C_ACCENT_DARK lv_color_hex(0x1D4ED8)

static bool s_styles_initialized = false;

static lv_style_t s_st_screen;
static lv_style_t s_st_bar;

static lv_style_t s_st_icon_btn_default;
static lv_style_t s_st_icon_btn_pressed;
static lv_style_t s_st_icon_btn_checked;

static lv_style_t s_st_play_btn_default;
static lv_style_t s_st_play_btn_pressed;

static lv_style_t s_st_card;
static lv_style_t s_st_card_btn_default;
static lv_style_t s_st_card_btn_pressed;

static lv_style_t s_st_seek_main;
static lv_style_t s_st_seek_indic;
static lv_style_t s_st_seek_knob;

static lv_style_t s_st_chip;
static lv_style_t s_st_list_item_default;
static lv_style_t s_st_list_item_pressed;

static void init_all_styles(void) {
    if (s_styles_initialized) return;

    // 1. st_screen: fondo c_bg, texto c_text
    lv_style_init(&s_st_screen);
    lv_style_set_bg_opa(&s_st_screen, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_screen, C_BG);
    lv_style_set_text_color(&s_st_screen, C_TEXT);
    lv_style_set_border_width(&s_st_screen, 0);
    lv_style_set_pad_all(&s_st_screen, 0);

    // 2. st_bar: fondo c_bg_osd, radio 0, sin bordes
    lv_style_init(&s_st_bar);
    lv_style_set_bg_opa(&s_st_bar, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_bar, C_BG_OSD);
    lv_style_set_radius(&s_st_bar, 0);
    lv_style_set_border_width(&s_st_bar, 0);
    lv_style_set_pad_all(&s_st_bar, 0);
    lv_style_set_text_color(&s_st_bar, C_TEXT);

    // 3. st_icon_btn: transparente, radio circular, padding 0, sin borde
    lv_style_init(&s_st_icon_btn_default);
    lv_style_set_bg_opa(&s_st_icon_btn_default, LV_OPA_TRANSP);
    lv_style_set_border_width(&s_st_icon_btn_default, 0);
    lv_style_set_radius(&s_st_icon_btn_default, LV_RADIUS_CIRCLE);
    lv_style_set_pad_all(&s_st_icon_btn_default, 0);
    lv_style_set_shadow_width(&s_st_icon_btn_default, 0);
    lv_style_set_text_color(&s_st_icon_btn_default, C_TEXT);
    lv_style_set_image_recolor(&s_st_icon_btn_default, C_TEXT);
    lv_style_set_image_recolor_opa(&s_st_icon_btn_default, LV_OPA_COVER);

    lv_style_init(&s_st_icon_btn_pressed);
    lv_style_set_bg_opa(&s_st_icon_btn_pressed, LV_OPA_30);
    lv_style_set_bg_color(&s_st_icon_btn_pressed, lv_color_hex(0xFFFFFF));

    lv_style_init(&s_st_icon_btn_checked);
    lv_style_set_text_color(&s_st_icon_btn_checked, C_ACCENT);
    lv_style_set_image_recolor(&s_st_icon_btn_checked, C_ACCENT);
    lv_style_set_image_recolor_opa(&s_st_icon_btn_checked, LV_OPA_COVER);

    // 4. st_play_btn: círculo 56x56, fondo c_accent azul, icono blanco
    lv_style_init(&s_st_play_btn_default);
    lv_style_set_bg_opa(&s_st_play_btn_default, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_play_btn_default, C_ACCENT);
    lv_style_set_border_width(&s_st_play_btn_default, 0);
    lv_style_set_radius(&s_st_play_btn_default, LV_RADIUS_CIRCLE);
    lv_style_set_pad_all(&s_st_play_btn_default, 0);
    lv_style_set_shadow_width(&s_st_play_btn_default, 0);
    lv_style_set_text_color(&s_st_play_btn_default, lv_color_hex(0xFFFFFF));
    lv_style_set_image_recolor(&s_st_play_btn_default, lv_color_hex(0xFFFFFF));
    lv_style_set_image_recolor_opa(&s_st_play_btn_default, LV_OPA_COVER);

    lv_style_init(&s_st_play_btn_pressed);
    lv_style_set_bg_color(&s_st_play_btn_pressed, C_ACCENT_DARK);

    // 5. st_card: fondo c_surface, borde c_line, radio 8
    lv_style_init(&s_st_card);
    lv_style_set_bg_opa(&s_st_card, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_card, C_SURFACE);
    lv_style_set_border_width(&s_st_card, 1);
    lv_style_set_border_color(&s_st_card, C_LINE);
    lv_style_set_radius(&s_st_card, 8);
    lv_style_set_shadow_width(&s_st_card, 0);
    lv_style_set_text_color(&s_st_card, C_TEXT);

    // 6. st_card_btn: igual a card pero botón
    lv_style_init(&s_st_card_btn_default);
    lv_style_set_bg_opa(&s_st_card_btn_default, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_card_btn_default, C_SURFACE);
    lv_style_set_border_width(&s_st_card_btn_default, 1);
    lv_style_set_border_color(&s_st_card_btn_default, C_LINE);
    lv_style_set_radius(&s_st_card_btn_default, 8);
    lv_style_set_shadow_width(&s_st_card_btn_default, 0);
    lv_style_set_pad_all(&s_st_card_btn_default, 0);
    lv_style_set_text_color(&s_st_card_btn_default, C_TEXT);

    lv_style_init(&s_st_card_btn_pressed);
    lv_style_set_bg_color(&s_st_card_btn_pressed, C_SURFACE_HI);

    // 7. st_seek: pista c_line, indicador c_accent, knob c_text
    lv_style_init(&s_st_seek_main);
    lv_style_set_bg_opa(&s_st_seek_main, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_seek_main, C_LINE);
    lv_style_set_radius(&s_st_seek_main, 2);

    lv_style_init(&s_st_seek_indic);
    lv_style_set_bg_opa(&s_st_seek_indic, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_seek_indic, C_ACCENT);
    lv_style_set_radius(&s_st_seek_indic, 2);

    lv_style_init(&s_st_seek_knob);
    lv_style_set_bg_opa(&s_st_seek_knob, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_seek_knob, C_TEXT);
    lv_style_set_radius(&s_st_seek_knob, LV_RADIUS_CIRCLE);
    lv_style_set_pad_all(&s_st_seek_knob, 2);

    // 8. st_chip: fondo c_surface, radio 4, padding compacto
    lv_style_init(&s_st_chip);
    lv_style_set_bg_opa(&s_st_chip, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_chip, C_SURFACE);
    lv_style_set_radius(&s_st_chip, 4);
    lv_style_set_border_width(&s_st_chip, 0);
    lv_style_set_pad_top(&s_st_chip, 2);
    lv_style_set_pad_bottom(&s_st_chip, 2);
    lv_style_set_pad_left(&s_st_chip, 6);
    lv_style_set_pad_right(&s_st_chip, 6);
    lv_style_set_text_color(&s_st_chip, C_ACCENT);

    // 9. st_list_item: transparente con separador inferior
    lv_style_init(&s_st_list_item_default);
    lv_style_set_bg_opa(&s_st_list_item_default, LV_OPA_TRANSP);
    lv_style_set_border_width(&s_st_list_item_default, 1);
    lv_style_set_border_side(&s_st_list_item_default, LV_BORDER_SIDE_BOTTOM);
    lv_style_set_border_color(&s_st_list_item_default, C_LINE);

    lv_style_init(&s_st_list_item_pressed);
    lv_style_set_bg_opa(&s_st_list_item_pressed, LV_OPA_COVER);
    lv_style_set_bg_color(&s_st_list_item_pressed, C_SURFACE_HI);

    s_styles_initialized = true;
}

void add_style_st_screen(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_add_style(obj, &s_st_screen, LV_STATE_DEFAULT);
}

void remove_style_st_screen(lv_obj_t *obj) {
    if (s_styles_initialized) lv_obj_remove_style(obj, &s_st_screen, LV_STATE_DEFAULT);
}

void add_style_st_bar(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_add_style(obj, &s_st_bar, LV_STATE_DEFAULT);
}

void remove_style_st_bar(lv_obj_t *obj) {
    if (s_styles_initialized) lv_obj_remove_style(obj, &s_st_bar, LV_STATE_DEFAULT);
}

void add_style_st_icon_btn(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_remove_style_all(obj);
    lv_obj_add_style(obj, &s_st_icon_btn_default, LV_STATE_DEFAULT);
    lv_obj_add_style(obj, &s_st_icon_btn_pressed, LV_STATE_PRESSED);
    lv_obj_add_style(obj, &s_st_icon_btn_checked, LV_STATE_CHECKED);
    lv_obj_set_flex_flow(obj, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(obj, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
}

void remove_style_st_icon_btn(lv_obj_t *obj) {
    if (s_styles_initialized) {
        lv_obj_remove_style(obj, &s_st_icon_btn_default, LV_STATE_DEFAULT);
        lv_obj_remove_style(obj, &s_st_icon_btn_pressed, LV_STATE_PRESSED);
        lv_obj_remove_style(obj, &s_st_icon_btn_checked, LV_STATE_CHECKED);
    }
}

void add_style_st_play_btn(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_remove_style_all(obj);
    lv_obj_add_style(obj, &s_st_play_btn_default, LV_STATE_DEFAULT);
    lv_obj_add_style(obj, &s_st_play_btn_pressed, LV_STATE_PRESSED);
    lv_obj_set_flex_flow(obj, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(obj, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
}

void remove_style_st_play_btn(lv_obj_t *obj) {
    if (s_styles_initialized) {
        lv_obj_remove_style(obj, &s_st_play_btn_default, LV_STATE_DEFAULT);
        lv_obj_remove_style(obj, &s_st_play_btn_pressed, LV_STATE_PRESSED);
    }
}

void add_style_st_card(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_add_style(obj, &s_st_card, LV_STATE_DEFAULT);
}

void remove_style_st_card(lv_obj_t *obj) {
    if (s_styles_initialized) lv_obj_remove_style(obj, &s_st_card, LV_STATE_DEFAULT);
}

void add_style_st_card_btn(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_remove_style_all(obj);
    lv_obj_add_style(obj, &s_st_card_btn_default, LV_STATE_DEFAULT);
    lv_obj_add_style(obj, &s_st_card_btn_pressed, LV_STATE_PRESSED);
}

void remove_style_st_card_btn(lv_obj_t *obj) {
    if (s_styles_initialized) {
        lv_obj_remove_style(obj, &s_st_card_btn_default, LV_STATE_DEFAULT);
        lv_obj_remove_style(obj, &s_st_card_btn_pressed, LV_STATE_PRESSED);
    }
}

void add_style_st_seek(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_add_style(obj, &s_st_seek_main, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, &s_st_seek_indic, LV_PART_INDICATOR | LV_STATE_DEFAULT);
    lv_obj_add_style(obj, &s_st_seek_knob, LV_PART_KNOB | LV_STATE_DEFAULT);
}

void remove_style_st_seek(lv_obj_t *obj) {
    if (s_styles_initialized) {
        lv_obj_remove_style(obj, &s_st_seek_main, LV_PART_MAIN | LV_STATE_DEFAULT);
        lv_obj_remove_style(obj, &s_st_seek_indic, LV_PART_INDICATOR | LV_STATE_DEFAULT);
        lv_obj_remove_style(obj, &s_st_seek_knob, LV_PART_KNOB | LV_STATE_DEFAULT);
    }
}

void add_style_st_chip(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_add_style(obj, &s_st_chip, LV_STATE_DEFAULT);
}

void remove_style_st_chip(lv_obj_t *obj) {
    if (s_styles_initialized) lv_obj_remove_style(obj, &s_st_chip, LV_STATE_DEFAULT);
}

void add_style_st_list_item(lv_obj_t *obj) {
    init_all_styles();
    lv_obj_add_style(obj, &s_st_list_item_default, LV_STATE_DEFAULT);
    lv_obj_add_style(obj, &s_st_list_item_pressed, LV_STATE_PRESSED);
}

void remove_style_st_list_item(lv_obj_t *obj) {
    if (s_styles_initialized) {
        lv_obj_remove_style(obj, &s_st_list_item_default, LV_STATE_DEFAULT);
        lv_obj_remove_style(obj, &s_st_list_item_pressed, LV_STATE_PRESSED);
    }
}

void add_style(lv_obj_t *obj, int32_t styleIndex) {
    typedef void (*AddStyleFunc)(lv_obj_t *obj);
    static const AddStyleFunc add_style_funcs[] = {
        add_style_st_screen,
        add_style_st_bar,
        add_style_st_icon_btn,
        add_style_st_play_btn,
        add_style_st_card,
        add_style_st_card_btn,
        add_style_st_seek,
        add_style_st_chip,
        add_style_st_list_item,
    };
    if (styleIndex >= 0 && styleIndex < (int32_t)(sizeof(add_style_funcs) / sizeof(add_style_funcs[0]))) {
        add_style_funcs[styleIndex](obj);
    }
}

void remove_style(lv_obj_t *obj, int32_t styleIndex) {
    typedef void (*RemoveStyleFunc)(lv_obj_t *obj);
    static const RemoveStyleFunc remove_style_funcs[] = {
        remove_style_st_screen,
        remove_style_st_bar,
        remove_style_st_icon_btn,
        remove_style_st_play_btn,
        remove_style_st_card,
        remove_style_st_card_btn,
        remove_style_st_seek,
        remove_style_st_chip,
        remove_style_st_list_item,
    };
    if (styleIndex >= 0 && styleIndex < (int32_t)(sizeof(remove_style_funcs) / sizeof(remove_style_funcs[0]))) {
        remove_style_funcs[styleIndex](obj);
    }
}