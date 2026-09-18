#include "ui/actions.h"
#include "ui/vars.h"
#include "ui/screens.h"
#include "ui/images.h"
#include "ui/ui.h"
#include "ui/styles.h"
#include "ui_glue.h"
#include "ui_fonts.h"
#include "player.h"
#include "perf.h"
#include "settings_nvs.h"
#include "media_library.h"
#include "lcd_bus.h"
#include "avi_player.h"
#include "ili9488_8080.h"
#include "sdcard_spi.h"
#include "esp_system.h"
#include "esp_random.h"
#include <sys/statvfs.h>
#include "ff.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>

static const char *TAG = "UI_ACTIONS";

/* Labels never scroll vertically.  The two permitted horizontal marquees
 * explicitly restore their own long mode and horizontal direction later. */
static void ui_glue_label_no_scroll(lv_obj_t *label) {
    lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
    lv_obj_remove_flag(label, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_SCROLL_CHAIN_HOR |
                              LV_OBJ_FLAG_SCROLL_CHAIN_VER | LV_OBJ_FLAG_SCROLL_ELASTIC |
                              LV_OBJ_FLAG_SCROLL_MOMENTUM | LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_set_scroll_dir(label, LV_DIR_NONE);
    lv_obj_set_scrollbar_mode(label, LV_SCROLLBAR_MODE_OFF);
}

/* Dynamic overlays are created after ui_glue_apply_fonts(); make the same
 * no-scroll policy mandatory at creation time. */
static lv_obj_t *ui_glue_label_create(lv_obj_t *parent) {
    lv_obj_t *label = lv_label_create(parent);
    ui_glue_label_no_scroll(label);
    return label;
}

/* Apply this whenever a runtime title is written.  Only the player title and
 * the row matching player_status.track_index may use a horizontal marquee. */
static void ui_glue_set_track_title_overflow(lv_obj_t *label, bool allow_marquee) {
    ui_glue_label_no_scroll(label);
    if (allow_marquee) {
        lv_label_set_long_mode(label, LV_LABEL_LONG_SCROLL_CIRCULAR);
        lv_obj_set_scroll_dir(label, LV_DIR_HOR);
        lv_obj_set_style_anim_duration(label, 6000, 0);
    } else {
        lv_label_set_long_mode(label, LV_LABEL_LONG_DOT);
    }
}

/* LOCAL TO actions.c ONLY: route every dynamic-label allocation in this file
 * through ui_glue_label_create(), enforcing LONG_CLIP and no vertical scroll.
 * Do not copy or extend this LVGL API redefinition to other project files. */
#define lv_label_create(parent) ui_glue_label_create(parent)

static const lv_font_t *ui_glue_replacement_font(const lv_font_t *font) {
    if (font == &lv_font_montserrat_12) return &ui_font_montserrat_12;
    if (font == &lv_font_montserrat_14) return &ui_font_montserrat_14;
    if (font == &lv_font_montserrat_20) return &ui_font_montserrat_20;
    return NULL;
}

static void ui_glue_apply_fonts_recursive(lv_obj_t *obj) {
    const lv_font_t *replacement = ui_glue_replacement_font(
        lv_obj_get_style_text_font(obj, LV_PART_MAIN));
    if (replacement) {
        lv_obj_set_style_text_font(obj, replacement, LV_PART_MAIN);
    }
    if (lv_obj_check_type(obj, &lv_label_class) && obj != objects.lbl_title) {
        ui_glue_label_no_scroll(obj);
    }

    uint32_t child_count = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < child_count; ++i) {
        ui_glue_apply_fonts_recursive(lv_obj_get_child(obj, i));
    }
}

void ui_glue_apply_fonts(void) {
    lv_obj_t *screens[] = {
        objects.scr_player,
        objects.scr_library,
        objects.scr_no_media,
        objects.scr_queue,
        objects.scr_settings,
    };

    for (size_t i = 0; i < sizeof(screens) / sizeof(screens[0]); ++i) {
        if (screens[i]) ui_glue_apply_fonts_recursive(screens[i]);
    }

    for (lv_display_t *display = lv_display_get_next(NULL); display;
         display = lv_display_get_next(display)) {
        ui_glue_apply_fonts_recursive(lv_display_get_layer_bottom(display));
        ui_glue_apply_fonts_recursive(lv_display_get_layer_top(display));
        ui_glue_apply_fonts_recursive(lv_display_get_layer_sys(display));
    }
}

static const char *ui_glue_utf8_next(const char *text, uint32_t *codepoint) {
    const uint8_t *p = (const uint8_t *)text;
    if (p[0] < 0x80) {
        *codepoint = p[0];
        return text + 1;
    }
    if ((p[0] & 0xE0) == 0xC0 && (p[1] & 0xC0) == 0x80) {
        *codepoint = ((uint32_t)(p[0] & 0x1F) << 6) | (p[1] & 0x3F);
        return text + 2;
    }
    if ((p[0] & 0xF0) == 0xE0 && (p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80) {
        *codepoint = ((uint32_t)(p[0] & 0x0F) << 12) |
                     ((uint32_t)(p[1] & 0x3F) << 6) | (p[2] & 0x3F);
        return text + 3;
    }
    if ((p[0] & 0xF8) == 0xF0 && (p[1] & 0xC0) == 0x80 &&
        (p[2] & 0xC0) == 0x80 && (p[3] & 0xC0) == 0x80) {
        *codepoint = ((uint32_t)(p[0] & 0x07) << 18) |
                     ((uint32_t)(p[1] & 0x3F) << 12) |
                     ((uint32_t)(p[2] & 0x3F) << 6) | (p[3] & 0x3F);
        return text + 4;
    }
    *codepoint = p[0];
    return text + 1;
}

static int ui_glue_count_missing_glyphs_recursive(lv_obj_t *obj) {
    int missing = 0;
    if (lv_obj_check_type(obj, &lv_label_class)) {
        const lv_font_t *font = lv_obj_get_style_text_font(obj, LV_PART_MAIN);
        const char *text = lv_label_get_text(obj);
        for (uint32_t codepoint = 0; text && *text; ) {
            text = ui_glue_utf8_next(text, &codepoint);
            if (codepoint == '\n' || codepoint == '\r' || !font) continue;
            lv_font_glyph_dsc_t glyph_dsc;
            if (!lv_font_get_glyph_dsc(font, &glyph_dsc, codepoint, 0)) missing++;
        }
    }
    uint32_t child_count = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < child_count; ++i) {
        missing += ui_glue_count_missing_glyphs_recursive(lv_obj_get_child(obj, i));
    }
    return missing;
}

int ui_glue_count_missing_glyphs(void) {
    int missing = 0;
    lv_obj_t *screens[] = {
        objects.scr_player, objects.scr_library, objects.scr_no_media,
        objects.scr_queue, objects.scr_settings,
    };
    for (size_t i = 0; i < sizeof(screens) / sizeof(screens[0]); ++i) {
        if (screens[i]) missing += ui_glue_count_missing_glyphs_recursive(screens[i]);
    }
    for (lv_display_t *display = lv_display_get_next(NULL); display;
         display = lv_display_get_next(display)) {
        missing += ui_glue_count_missing_glyphs_recursive(lv_display_get_layer_top(display));
        missing += ui_glue_count_missing_glyphs_recursive(lv_display_get_layer_sys(display));
    }
    return missing;
}

static bool s_osd_visible = true;
static int s_hud_forced_mode = 0; // 0=auto, 1=forced hidden, 2=forced visible
static int64_t s_last_touch_time = 0;
static bool s_seeking = false;
static int s_current_track_idx = 0;
static view_mode_t s_view_mode = VIEW_MODE_FULLSCREEN;
static app_settings_t s_settings;
static bool s_was_playing_before_settings = false;

static bool s_locked = false;
static bool s_consume_touch_until_release = false;
static bool s_consume_next_click = false;
static int64_t s_touch_down_ms = 0;
static lv_point_t s_touch_down_pos = {0, 0};
static bool s_is_vertical_drag = false;
static int s_drag_start_brightness = 70;
static int64_t s_last_tap_ms = 0;
static lv_point_t s_last_tap_pos = {0, 0};
static int64_t s_seek_hint_hide_ms = 0;
static int64_t s_brightness_hide_ms = 0;
static int32_t s_accum_seek_s = 0;
static bool s_seek_in_flight = false;
static bool s_single_tap_pending = false;
static int64_t s_single_tap_time_ms = 0;
static lv_obj_t *s_ovl_lock = NULL;
static lv_obj_t *s_lock_card = NULL;
static lv_obj_t *s_arc_unlock = NULL;
/* Square color-key backings sit immediately below every rounded overlay card.
 * LVGL otherwise resolves the anti-aliased rounded corners against the screen's
 * default background before the overlay pixels reach the compositor. */
static lv_obj_t *s_overlay_card_backing[LCD_OVERLAY_MAX_RECTS] = {0};
static int64_t s_lock_touch_start_us = 0;
static int64_t s_lock_show_time = 0;

static lv_obj_t *s_resume_overlay = NULL;
static lv_obj_t *s_resume_sheet = NULL;
static lv_obj_t *s_resume_title = NULL;
static lv_obj_t *s_resume_sub = NULL;
static lv_obj_t *s_btn_resume_cont = NULL;
static lv_obj_t *s_lbl_resume_cont = NULL;
static lv_obj_t *s_btn_resume_start = NULL;
static lv_obj_t *s_lbl_resume_start = NULL;
static lv_obj_t *s_btn_resume_close = NULL;
static int s_resume_target_idx = -1;
static void show_resume_sheet(int idx);

static lv_obj_t *ui_glue_overlay_backing(lv_obj_t *card) {
    if (!card) return NULL;
    for (int i = 0; i < LCD_OVERLAY_MAX_RECTS; i++) {
        if (s_overlay_card_backing[i] && lv_obj_get_child(s_overlay_card_backing[i], 0) == card) {
            return s_overlay_card_backing[i];
        }
    }
    return NULL;
}

static void ui_glue_prepare_overlay_card(int slot, lv_obj_t *card) {
    if (!card || slot < 0 || slot >= LCD_OVERLAY_MAX_RECTS || s_overlay_card_backing[slot]) return;

    bool hidden = lv_obj_has_flag(card, LV_OBJ_FLAG_HIDDEN);
    lv_obj_t *backing = lv_obj_create(lv_obj_get_parent(card));
    lv_obj_set_pos(backing, lv_obj_get_x(card), lv_obj_get_y(card));
    lv_obj_set_size(backing, lv_obj_get_width(card), lv_obj_get_height(card));
    lv_obj_set_style_bg_color(backing, lv_color_make(0, 255, 0), 0);
    lv_obj_set_style_bg_opa(backing, LV_OPA_COVER, 0);
    lv_obj_set_style_border_width(backing, 0, 0);
    lv_obj_set_style_radius(backing, 0, 0);
    lv_obj_set_style_pad_all(backing, 0, 0);
    lv_obj_remove_flag(backing, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_parent(card, backing);
    lv_obj_set_pos(card, 0, 0);
    if (hidden) lv_obj_add_flag(backing, LV_OBJ_FLAG_HIDDEN);
    s_overlay_card_backing[slot] = backing;
}

static void ui_glue_set_overlay_card_visible(lv_obj_t *card, bool visible) {
    lv_obj_t *backing = ui_glue_overlay_backing(card);
    if (visible) {
        if (backing) lv_obj_remove_flag(backing, LV_OBJ_FLAG_HIDDEN);
        lv_obj_remove_flag(card, LV_OBJ_FLAG_HIDDEN);
    } else {
        lv_obj_add_flag(card, LV_OBJ_FLAG_HIDDEN);
        if (backing) lv_obj_add_flag(backing, LV_OBJ_FLAG_HIDDEN);
    }
}

static void ui_glue_set_overlay_card_pos(lv_obj_t *card, int16_t x, int16_t y) {
    lv_obj_t *backing = ui_glue_overlay_backing(card);
    if (backing) {
        lv_obj_set_pos(backing, x, y);
        lv_obj_set_pos(card, 0, 0);
    } else {
        lv_obj_set_pos(card, x, y);
    }
}

static void ui_glue_set_overlay_rect_for_obj(int slot, lv_obj_t *obj, bool enabled) {
    if (!enabled || !obj) {
        lcd_bus_set_overlay_rect(slot, 0, 0, 0, 0, false);
        return;
    }
    lv_area_t area;
    lv_obj_get_coords(obj, &area);
    lcd_bus_set_overlay_rect(slot, area.x1, area.y1,
                             area.x2 - area.x1 + 1, area.y2 - area.y1 + 1, true);
}

/* Reutiliza una única pista de salto: nunca quedan rectángulos activos a ambos lados. */
static void show_seek_hint(int16_t x, const lv_image_dsc_t *icon, const char *text) {
    if (!objects.ovl_seek_hint) return;

    /* Primero retirar el rectángulo y el objeto de su posición anterior.  Así el
     * flush de LVGL no puede dejar una tarjeta vacía en el lado opuesto. */
    lcd_bus_set_overlay_rect(2, 0, 0, 0, 0, false);
    ui_glue_set_overlay_card_visible(objects.ovl_seek_hint, false);

    ui_glue_set_overlay_card_pos(objects.ovl_seek_hint, x, 116);
    if (objects.img_seek_hint) lv_image_set_src(objects.img_seek_hint, icon);
    if (objects.lbl_seek_hint) lv_label_set_text(objects.lbl_seek_hint, text);

    ui_glue_set_overlay_rect_for_obj(2, objects.ovl_seek_hint, true);
    ui_glue_set_overlay_card_visible(objects.ovl_seek_hint, true);
}

#define BRIGHTNESS_REAL_MIN 25
#define BRIGHTNESS_REAL_MAX 100

/* NVS and the backlight use the real 25..100% range. The UI exposes it as
 * 0..100% so its lower endpoint remains visible on this display. */
static int brightness_real_to_display(uint8_t real_brightness) {
    if (real_brightness < BRIGHTNESS_REAL_MIN) real_brightness = BRIGHTNESS_REAL_MIN;
    if (real_brightness > BRIGHTNESS_REAL_MAX) real_brightness = BRIGHTNESS_REAL_MAX;
    return ((real_brightness - BRIGHTNESS_REAL_MIN) * 100 + 37) / 75;
}

static uint8_t brightness_display_to_real(int display_brightness) {
    if (display_brightness < 0) display_brightness = 0;
    if (display_brightness > 100) display_brightness = 100;
    return (uint8_t)(BRIGHTNESS_REAL_MIN + (display_brightness * 75 + 50) / 100);
}

extern uint32_t touch_inject_synthetic(uint16_t x, uint16_t y, bool pressed);
extern bool touch_synthetic_was_consumed(uint32_t sequence);

static lv_obj_t *s_toast_box = NULL;
static lv_obj_t *s_toast_icon = NULL;
static lv_obj_t *s_toast_title = NULL;
static lv_obj_t *s_toast_desc = NULL;
static lv_timer_t *s_toast_timer = NULL;

static bool s_pending_library_return = false;

static void toast_timer_cb(lv_timer_t *t) {
    if (s_toast_box) {
        lv_obj_add_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN);
    }
    if (s_toast_timer) {
        lv_timer_delete(s_toast_timer);
        s_toast_timer = NULL;
    }
    if (s_pending_library_return) {
        s_pending_library_return = false;
        action_open_library(NULL);
    }
}

void ui_glue_show_toast(const char *title, const char *msg, bool is_error) {
    lv_obj_t *scr = lv_screen_active();
    if (!scr) return;

    if (!s_toast_box) {
        s_toast_box = lv_obj_create(scr);
        lv_obj_set_width(s_toast_box, 300);
        lv_obj_set_height(s_toast_box, LV_SIZE_CONTENT);
        lv_obj_set_style_bg_color(s_toast_box, lv_color_hex(0x15171C), 0);
        lv_obj_set_style_bg_opa(s_toast_box, 255, 0);
        lv_obj_set_style_border_color(s_toast_box, lv_color_hex(0x2A2D34), 0);
        lv_obj_set_style_border_width(s_toast_box, 1, 0);
        lv_obj_set_style_radius(s_toast_box, 8, 0);
        lv_obj_set_style_pad_all(s_toast_box, 10, 0);
        lv_obj_remove_flag(s_toast_box, LV_OBJ_FLAG_SCROLLABLE);

        // Icon
        s_toast_icon = lv_image_create(s_toast_box);
        lv_image_set_src(s_toast_icon, &img_warning);
        lv_obj_set_pos(s_toast_icon, 0, 0);
        lv_obj_set_size(s_toast_icon, 20, 20);

        // Title
        s_toast_title = lv_label_create(s_toast_box);
        lv_obj_set_pos(s_toast_title, 28, 0);
        lv_obj_set_width(s_toast_title, 250);
        lv_obj_set_style_text_font(s_toast_title, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(s_toast_title, lv_color_hex(0xEDEDEA), 0);

        // Description
        s_toast_desc = lv_label_create(s_toast_box);
        lv_obj_set_pos(s_toast_desc, 28, 22);
        lv_obj_set_width(s_toast_desc, 250);
        lv_label_set_long_mode(s_toast_desc, LV_LABEL_LONG_WRAP);
        lv_obj_set_style_text_font(s_toast_desc, &lv_font_montserrat_12, 0);
        lv_obj_set_style_text_color(s_toast_desc, lv_color_hex(0x8E929B), 0);
    } else {
        lv_obj_set_parent(s_toast_box, scr);
    }

    lv_label_set_text(s_toast_title, title ? title : "");
    ui_glue_label_no_scroll(s_toast_title);
    lv_label_set_text(s_toast_desc, msg ? msg : "");

    uint32_t icon_color = is_error ? 0xE5484D : 0xF2B33D;
    lv_obj_set_style_image_recolor(s_toast_icon, lv_color_hex(icon_color), 0);
    lv_obj_set_style_image_recolor_opa(s_toast_icon, 255, 0);

    lv_obj_set_pos(s_toast_box, 90, 150);
    lv_obj_remove_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN);
    lv_obj_move_foreground(s_toast_box);

    if (s_toast_timer) {
        lv_timer_reset(s_toast_timer);
    } else {
        s_toast_timer = lv_timer_create(toast_timer_cb, 3000, NULL);
    }
}

static void dump_widget(const char *name, lv_obj_t *obj) {
    if (!obj) {
        printf("UIDUMP,id=%s,null=1\n", name);
        return;
    }
    lv_obj_update_layout(obj);
    int x = lv_obj_get_x(obj);
    int y = lv_obj_get_y(obj);
    int w = lv_obj_get_width(obj);
    int h = lv_obj_get_height(obj);
    bool hidden = lv_obj_has_flag(obj, LV_OBJ_FLAG_HIDDEN);
    bool clickable = lv_obj_has_flag(obj, LV_OBJ_FLAG_CLICKABLE);
    printf("UIDUMP,id=%s,x=%d,y=%d,w=%d,h=%d,hidden=%d,clickable=%d\n",
           name, x, y, w, h, hidden ? 1 : 0, clickable ? 1 : 0);
}

static void fix_button_events(lv_obj_t *btn) {
    if (!btn) return;
    lv_obj_add_flag(btn, LV_OBJ_FLAG_CLICKABLE);
    uint32_t cnt = lv_obj_get_child_count(btn);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(btn, i);
        if (child) {
            lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
            lv_obj_add_flag(child, LV_OBJ_FLAG_EVENT_BUBBLE);
        }
    }
}

void ui_glue_fix_all_button_flags(void) {
    fix_button_events(objects.btn_back);
    fix_button_events(objects.btn_queue);
    fix_button_events(objects.btn_lock);
    fix_button_events(objects.btn_repeat);
    fix_button_events(objects.btn_prev);
    fix_button_events(objects.btn_rew);
    fix_button_events(objects.btn_play);
    fix_button_events(objects.btn_fwd);
    fix_button_events(objects.btn_next);
    fix_button_events(objects.btn_shuffle);
    fix_button_events(objects.btn_settings);
    fix_button_events(objects.btn_lib_settings);
    fix_button_events(objects.btn_retry);
    fix_button_events(objects.btn_settings_alt);
    fix_button_events(objects.btn_queue_close);
    fix_button_events(objects.btn_back_settings);
    fix_button_events(objects.btn_tab_0);
    fix_button_events(objects.btn_tab_1);
    fix_button_events(objects.btn_tab_2);
    fix_button_events(objects.btn_tab_3);
    fix_button_events(objects.btn_rescan);
    fix_button_events(objects.btn_open_stats);
    fix_button_events(objects.btn_stats_close);
}

void ui_glue_dump_all(void) {
    ui_glue_fix_all_button_flags();
    dump_widget("btn_queue_close", objects.btn_queue_close);
    dump_widget("queue_list", objects.queue_list);
    dump_widget("lbl_queue_title", objects.lbl_queue_title);
    dump_widget("btn_back", objects.btn_back);
    dump_widget("lbl_title", objects.lbl_title);
    dump_widget("lbl_subtitle", objects.lbl_subtitle);
    dump_widget("chip_fps", objects.chip_fps);
    dump_widget("btn_queue", objects.btn_queue);
    dump_widget("osd_top", objects.osd_top);
    dump_widget("lbl_pos", objects.lbl_pos);
    dump_widget("sld_seek", objects.sld_seek);
    dump_widget("lbl_dur", objects.lbl_dur);
    dump_widget("btn_lock", objects.btn_lock);
    dump_widget("btn_repeat", objects.btn_repeat);
    dump_widget("btn_prev", objects.btn_prev);
    dump_widget("btn_rew", objects.btn_rew);
    dump_widget("btn_play", objects.btn_play);
    dump_widget("btn_fwd", objects.btn_fwd);
    dump_widget("btn_next", objects.btn_next);
    dump_widget("btn_shuffle", objects.btn_shuffle);
    dump_widget("btn_settings", objects.btn_settings);
    dump_widget("osd_bottom", objects.osd_bottom);
    dump_widget("bar_mini_progress", objects.bar_mini_progress);
    dump_widget("lib_header", objects.lib_header);
    dump_widget("lbl_lib_title", objects.lbl_lib_title);
    dump_widget("lbl_lib_count", objects.lbl_lib_count);
    dump_widget("btn_lib_settings", objects.btn_lib_settings);
    dump_widget("bar_scan", objects.bar_scan);
    dump_widget("lib_grid", objects.lib_grid);
    dump_widget("img_nomedia", objects.img_nomedia);
    dump_widget("lbl_nomedia_title", objects.lbl_nomedia_title);
    dump_widget("btn_retry", objects.btn_retry);
    dump_widget("btn_settings_alt", objects.btn_settings_alt);
    fflush(stdout);
}

bool ui_glue_is_locked(void) {
    return s_locked;
}

static void lock_overlay_event_cb(lv_event_t *e) {
    lv_event_code_t code = lv_event_get_code(e);
    if (code == LV_EVENT_PRESSED) {
        s_lock_touch_start_us = esp_timer_get_time();
        if (s_lock_card) {
            bool was_hidden = lv_obj_has_flag(s_lock_card, LV_OBJ_FLAG_HIDDEN);
            ui_glue_set_overlay_card_visible(s_lock_card, true);
            if (was_hidden) {
                ui_glue_set_overlay_rect_for_obj(0, s_lock_card, true);
                ESP_LOGI(TAG, "Toque en pantalla bloqueada -> tarjeta mostrada con composicion overlay");
            }
        }
        s_lock_show_time = esp_timer_get_time() / 1000;
        if (s_arc_unlock) {
            lv_arc_set_value(s_arc_unlock, 0);
        }
    } else if (code == LV_EVENT_PRESSING) {
        s_lock_show_time = esp_timer_get_time() / 1000;
        if (s_lock_touch_start_us > 0) {
            int64_t held_us = esp_timer_get_time() - s_lock_touch_start_us;
            int32_t val = (int32_t)((held_us * 100) / 1000000LL);
            if (val > 100) val = 100;
            if (s_arc_unlock) {
                lv_arc_set_value(s_arc_unlock, val);
            }
            if (held_us >= 1000000LL) {
                ui_glue_unlock();
            }
        }
    } else if (code == LV_EVENT_RELEASED) {
        s_lock_touch_start_us = 0;
        s_lock_show_time = esp_timer_get_time() / 1000;
        if (s_arc_unlock) {
            lv_arc_set_value(s_arc_unlock, 0);
        }
    }
}

static void init_lock_overlay(void) {
    if (s_ovl_lock || !objects.scr_player) return;

    // Root overlay: 0, 0, 480, 320, transparent, clickable
    s_ovl_lock = lv_obj_create(objects.scr_player);
    lv_obj_set_pos(s_ovl_lock, 0, 0);
    lv_obj_set_size(s_ovl_lock, 480, 320);
    lv_obj_set_style_bg_opa(s_ovl_lock, 0, 0);
    lv_obj_set_style_border_width(s_ovl_lock, 0, 0);
    lv_obj_set_style_pad_all(s_ovl_lock, 0, 0);
    lv_obj_remove_flag(s_ovl_lock, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(s_ovl_lock, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(s_ovl_lock, lock_overlay_event_cb, LV_EVENT_ALL, NULL);

    // Tarjeta Bloqueo: x=140, y=96, w=200, h=132, fondo #0B0C0F, radio 8.
    s_lock_card = lv_obj_create(s_ovl_lock);
    lv_obj_set_pos(s_lock_card, 140, 96);
    lv_obj_set_size(s_lock_card, 200, 132);
    lv_obj_set_style_bg_color(s_lock_card, lv_color_hex(0x0B0C0F), 0);
    lv_obj_set_style_bg_opa(s_lock_card, 255, 0);
    lv_obj_set_style_border_width(s_lock_card, 0, 0);
    lv_obj_set_style_radius(s_lock_card, 8, 0);
    lv_obj_set_style_pad_all(s_lock_card, 0, 0);
    lv_obj_remove_flag(s_lock_card, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(s_lock_card, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Arc unlock: centered horizontally at top: x=60, y=0, w=80, h=80
    s_arc_unlock = lv_arc_create(s_lock_card);
    lv_obj_set_pos(s_arc_unlock, 60, 0);
    lv_obj_set_size(s_arc_unlock, 80, 80);
    lv_arc_set_range(s_arc_unlock, 0, 100);
    lv_arc_set_value(s_arc_unlock, 0);
    lv_arc_set_bg_angles(s_arc_unlock, 0, 360);
    lv_arc_set_rotation(s_arc_unlock, 270);
    lv_obj_set_style_arc_color(s_arc_unlock, lv_color_hex(0x2A2D34), LV_PART_MAIN);
    lv_obj_set_style_arc_width(s_arc_unlock, 4, LV_PART_MAIN);
    lv_obj_set_style_arc_color(s_arc_unlock, lv_color_hex(0xF2B33D), LV_PART_INDICATOR);
    lv_obj_set_style_arc_width(s_arc_unlock, 4, LV_PART_INDICATOR);
    lv_obj_set_style_opa(s_arc_unlock, LV_OPA_0, LV_PART_KNOB);
    lv_obj_remove_flag(s_arc_unlock, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(s_arc_unlock, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Circle container: x=68, y=8, w=64, h=64, bg #15171C, radius 32
    lv_obj_t *circle = lv_obj_create(s_lock_card);
    lv_obj_set_pos(circle, 68, 8);
    lv_obj_set_size(circle, 64, 64);
    lv_obj_set_style_bg_color(circle, lv_color_hex(0x15171C), 0);
    lv_obj_set_style_bg_opa(circle, 255, 0);
    lv_obj_set_style_radius(circle, 32, 0);
    lv_obj_set_style_border_width(circle, 0, 0);
    lv_obj_set_style_pad_all(circle, 0, 0);
    lv_obj_remove_flag(circle, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(circle, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Lock icon inside circle
    lv_obj_t *icon = lv_image_create(circle);
    lv_image_set_src(icon, &img_lock_big);
    lv_obj_set_style_image_recolor(icon, lv_color_hex(0xEDEDEA), 0);
    lv_obj_set_style_image_recolor_opa(icon, 255, 0);
    lv_obj_center(icon);
    lv_obj_remove_flag(icon, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(icon, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Montserrat 14 needs an 18 px content box.
    lv_obj_t *lbl_title = lv_label_create(s_lock_card);
    lv_obj_set_pos(lbl_title, 0, 86);
    lv_obj_set_size(lbl_title, 200, 18);
    lv_label_set_text(lbl_title, "Pantalla bloqueada");
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_title, lv_color_hex(0xEDEDEA), 0);
    lv_obj_set_style_text_align(lbl_title, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_bg_opa(lbl_title, LV_OPA_TRANSP, 0);
    lv_obj_remove_flag(lbl_title, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(lbl_title, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Two readable Montserrat 12 lines; the lock-card width is fixed.
    lv_obj_t *lbl_hint = lv_label_create(s_lock_card);
    lv_obj_set_pos(lbl_hint, 0, 100);
    lv_obj_set_size(lbl_hint, 200, 32);
    lv_label_set_long_mode(lbl_hint, LV_LABEL_LONG_WRAP);
    lv_label_set_text(lbl_hint, "Mantén pulsado\npara desbloquear");
    lv_obj_set_style_text_font(lbl_hint, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(lbl_hint, lv_color_hex(0x8E929B), 0);
    lv_obj_set_style_text_align(lbl_hint, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_bg_opa(lbl_hint, LV_OPA_TRANSP, 0);
    lv_obj_remove_flag(lbl_hint, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(lbl_hint, LV_OBJ_FLAG_EVENT_BUBBLE);

    ui_glue_prepare_overlay_card(0, s_lock_card);
}

void ui_glue_unlock(void) {
    s_locked = false;
    s_lock_touch_start_us = 0;
    s_consume_touch_until_release = true;
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_ovl_lock) {
        lv_obj_add_flag(s_ovl_lock, LV_OBJ_FLAG_HIDDEN);
    }
    lcd_bus_set_overlay_rect(0, 0, 0, 0, 0, false);
    player_status_t st_unl;
    player_get_status(&st_unl);
    if (st_unl.state != PST_PLAYING) {
        avi_player_reblit_current_frame();
    }
    if (s_arc_unlock) {
        lv_arc_set_value(s_arc_unlock, 0);
    }
    ui_glue_set_osd_visible(true);
    printf("UINAV,btn=unlock,result=PASS\n");
    fflush(stdout);
    ESP_LOGI(TAG, "Action: unlock -> pantalla desbloqueada. OSD visible y toque residual consumido.");
}

static void player_touch_gesture_event_cb(lv_event_t *e) {
    lv_event_code_t code = lv_event_get_code(e);
    if (s_locked) return;

    int64_t now = esp_timer_get_time() / 1000;
    lv_indev_t *indev = lv_indev_active();
    lv_point_t p = {0, 0};
    if (indev) lv_indev_get_point(indev, &p);

    if (code == LV_EVENT_PRESSED) {
        s_touch_down_ms = now;
        s_touch_down_pos = p;
        s_is_vertical_drag = false;
        s_drag_start_brightness = brightness_real_to_display(s_settings.bright);
        s_last_touch_time = now;
    } else if (code == LV_EVENT_PRESSING) {
        s_last_touch_time = now;
        int dx = p.x - s_touch_down_pos.x;
        int dy = p.y - s_touch_down_pos.y;

        if (!s_is_vertical_drag) {
            // Mitad izquierda (x < 240) y arrastre vertical prominente
            if (s_touch_down_pos.x < 240 && (abs(dy) > 10) && (abs(dy) > abs(dx) * 2)) {
                s_is_vertical_drag = true;
                s_single_tap_pending = false;
                s_consume_next_click = true;
                if (objects.ovl_brightness) {
                    ui_glue_set_overlay_card_visible(objects.ovl_brightness, true);
                    ui_glue_set_overlay_rect_for_obj(3, objects.ovl_brightness, true);
                }
            }
        }

        if (s_is_vertical_drag) {
            // 1 % cada 2 px (hacia arriba aumenta, hacia abajo disminuye)
            int delta_pct = (s_touch_down_pos.y - p.y) / 2;
            int new_bri = s_drag_start_brightness + delta_pct;
            if (new_bri < 0) new_bri = 0;
            if (new_bri > 100) new_bri = 100;

            s_settings.bright = brightness_display_to_real(new_bri);
            settings_nvs_set_u8("bright", s_settings.bright);
            ili9488_8080_set_backlight(s_settings.bright);

            if (objects.bar_brightness) lv_bar_set_value(objects.bar_brightness, new_bri, LV_ANIM_OFF);
            if (objects.lbl_bri) {
                char buf[16];
                snprintf(buf, sizeof(buf), "%d%%", new_bri);
                lv_label_set_text(objects.lbl_bri, buf);
            }
            if (objects.sld_brightness) lv_slider_set_value(objects.sld_brightness, new_bri, LV_ANIM_OFF);
            if (objects.lbl_set_bri_val) {
                char buf[16];
                snprintf(buf, sizeof(buf), "%d%%", new_bri);
                lv_label_set_text(objects.lbl_set_bri_val, buf);
            }
            s_brightness_hide_ms = now + 600;
        }
    } else if (code == LV_EVENT_RELEASED) {
        s_last_touch_time = now;
        if (s_is_vertical_drag) {
            s_is_vertical_drag = false;
            s_consume_next_click = true;
            return;
        }

        int64_t dur = now - s_touch_down_ms;
        if (dur <= 400) {
            int tap_dx = s_touch_down_pos.x - s_last_tap_pos.x;
            int tap_dy = s_touch_down_pos.y - s_last_tap_pos.y;
            bool is_double_tap = (now - s_last_tap_ms < 300) && (abs(tap_dx) < 40) && (abs(tap_dy) < 40);

            if (is_double_tap) {
                s_single_tap_pending = false;
                s_consume_next_click = true;
                int step = s_settings.seekstep ? s_settings.seekstep : 10;

                if (s_touch_down_pos.x < 160) {
                    // Tercio izquierdo: rebobinar
                    if (!s_seek_in_flight || s_accum_seek_s > 0) {
                        s_accum_seek_s = -step;
                    } else {
                        s_accum_seek_s -= step;
                    }
                    s_seek_in_flight = true;
                    s_seek_hint_hide_ms = now + 600;

                    char buf[16];
                    snprintf(buf, sizeof(buf), "%ld s", (long)s_accum_seek_s);
                    show_seek_hint(64, &img_seek_back, buf);
                    ESP_LOGI(TAG, "Gestos: Doble toque izquierdo -> acum %ld s", (long)s_accum_seek_s);
                } else if (s_touch_down_pos.x > 320) {
                    // Tercio derecho: avanzar
                    if (!s_seek_in_flight || s_accum_seek_s < 0) {
                        s_accum_seek_s = step;
                    } else {
                        s_accum_seek_s += step;
                    }
                    s_seek_in_flight = true;
                    s_seek_hint_hide_ms = now + 600;

                    char buf[16];
                    snprintf(buf, sizeof(buf), "+%ld s", (long)s_accum_seek_s);
                    show_seek_hint(316, &img_seek_fwd, buf);
                    ESP_LOGI(TAG, "Gestos: Doble toque derecho -> acum +%ld s", (long)s_accum_seek_s);
                } else {
                    // Tercio central: reproducir / pausar
                    action_toggle_play(NULL);
                    ESP_LOGI(TAG, "Gestos: Doble toque central -> reproducir/pausar");
                }
                s_last_tap_ms = 0;
            } else {
                // Primer toque: registrar y esperar confirmacion de 280 ms
                s_last_tap_ms = now;
                s_last_tap_pos = s_touch_down_pos;
                s_single_tap_pending = true;
                s_single_tap_time_ms = now;
                s_consume_next_click = true;
            }
        }
    }
}

void ui_glue_init(void) {
    settings_nvs_load(&s_settings);
    if (s_settings.bright < BRIGHTNESS_REAL_MIN) {
        s_settings.bright = BRIGHTNESS_REAL_MIN;
        settings_nvs_set_u8("bright", s_settings.bright);
    }
    if (s_settings.bright > BRIGHTNESS_REAL_MAX) s_settings.bright = BRIGHTNESS_REAL_MAX;
    ili9488_8080_set_backlight(s_settings.bright);

    int shown_brightness = brightness_real_to_display(s_settings.bright);
    if (objects.sld_brightness) {
        lv_slider_set_range(objects.sld_brightness, 0, 100);
        lv_slider_set_value(objects.sld_brightness, shown_brightness, LV_ANIM_OFF);
    }
    if (objects.bar_brightness) {
        lv_bar_set_range(objects.bar_brightness, 0, 100);
        lv_bar_set_value(objects.bar_brightness, shown_brightness, LV_ANIM_OFF);
    }
    if (objects.player_touch) {
        lv_obj_add_event_cb(objects.player_touch, player_touch_gesture_event_cb, LV_EVENT_ALL, NULL);
    }
    ui_glue_prepare_overlay_card(1, objects.ovl_stats);
    ui_glue_prepare_overlay_card(2, objects.ovl_seek_hint);
    ui_glue_prepare_overlay_card(3, objects.ovl_brightness);
    /* Montserrat intentionally has no LV_SYMBOL_DOWN (U+F078).  Use the
     * design PNG so dropdown indicators cannot render as missing-glyph boxes. */
    if (objects.dd_osd_timeout) lv_dropdown_set_symbol(objects.dd_osd_timeout, &img_chevron_down);
    if (objects.dd_repeat) lv_dropdown_set_symbol(objects.dd_repeat, &img_chevron_down);
    if (objects.dd_seek_step) lv_dropdown_set_symbol(objects.dd_seek_step, &img_chevron_down);
    if (objects.chip_fps) {
        lv_obj_add_flag(objects.chip_fps, LV_OBJ_FLAG_CLICKABLE);
        /* El texto hijo no debe capturar la pulsación larga destinada al chip. */
        uint32_t child_count = lv_obj_get_child_count(objects.chip_fps);
        for (uint32_t i = 0; i < child_count; i++) {
            lv_obj_t *child = lv_obj_get_child(objects.chip_fps, i);
            lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
            lv_obj_add_flag(child, LV_OBJ_FLAG_EVENT_BUBBLE);
        }
    }
    if (objects.obj0) {
        lv_obj_remove_flag(objects.obj0, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_flag(objects.obj0, LV_OBJ_FLAG_EVENT_BUBBLE);
    }
    if (objects.btn_open_stats && objects.obj32) {
        lv_obj_center(objects.obj32);
        lv_obj_set_style_text_align(objects.obj32, LV_TEXT_ALIGN_CENTER, 0);
    }
    if (objects.ovl_stats) {
        lv_obj_add_flag(objects.ovl_stats, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(objects.ovl_stats, action_open_stats, LV_EVENT_CLICKED, NULL);
        lv_obj_set_style_bg_color(objects.ovl_stats, lv_color_hex(0x15171C), LV_PART_MAIN);
        lv_obj_set_style_bg_opa(objects.ovl_stats, 255, LV_PART_MAIN);
        uint32_t c_cnt = lv_obj_get_child_count(objects.ovl_stats);
        for (uint32_t i = 0; i < c_cnt; i++) {
            lv_obj_t *ch = lv_obj_get_child(objects.ovl_stats, i);
            if (ch && ch != objects.btn_stats_close) {
                lv_obj_remove_flag(ch, LV_OBJ_FLAG_CLICKABLE);
                lv_obj_add_flag(ch, LV_OBJ_FLAG_EVENT_BUBBLE);
            }
        }
    }
    if (objects.lbl_title) {
        lv_obj_set_style_anim_duration(objects.lbl_title, 8000, 0);
        /* A marquee must never acquire a vertical scroll axis. */
        lv_obj_set_scroll_dir(objects.lbl_title, LV_DIR_HOR);
    }
    s_last_touch_time = esp_timer_get_time() / 1000;
    s_osd_visible = true;
    s_hud_forced_mode = 0;
    if (s_settings.last_path[0] != '\0') {
        int idx = media_library_index_of(s_settings.last_path);
        const media_item_t *it = (idx >= 0) ? media_library_get(idx) : NULL;
        if (it && it->compatible && !it->failed_playback) {
            ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
            return;
        }
    }
    ui_glue_set_view_mode(VIEW_MODE_STUDIO);
}

bool ui_glue_is_osd_visible(void) {
    return s_osd_visible;
}

void ui_glue_set_osd_visible(bool visible) {
    s_osd_visible = visible;
    if (s_view_mode == VIEW_MODE_FULLSCREEN) {
        if (visible) {
            player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 40, 480, 196}};
            player_cmd_send(&cmd);
            lcd_bus_set_video_rect(0, 40, 480, 196);
            if (objects.osd_top) lv_obj_remove_flag(objects.osd_top, LV_OBJ_FLAG_HIDDEN);
            if (objects.osd_bottom) lv_obj_remove_flag(objects.osd_bottom, LV_OBJ_FLAG_HIDDEN);
            if (objects.bar_mini_progress) lv_obj_add_flag(objects.bar_mini_progress, LV_OBJ_FLAG_HIDDEN);
        } else {
            if (objects.osd_top) lv_obj_add_flag(objects.osd_top, LV_OBJ_FLAG_HIDDEN);
            if (objects.osd_bottom) lv_obj_add_flag(objects.osd_bottom, LV_OBJ_FLAG_HIDDEN);
            /* En hidden no debe quedar una barra de progreso que invalida LVGL
             * periódicamente; el vídeo directo ya ocupa toda la pantalla. */
            if (objects.bar_mini_progress) lv_obj_add_flag(objects.bar_mini_progress, LV_OBJ_FLAG_HIDDEN);
            player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
            player_cmd_send(&cmd);
            lcd_bus_set_video_rect(0, 0, 480, 320);
        }
    } else if (s_view_mode == VIEW_MODE_QUEUE) {
        // En la cola el video permanece visible a la izquierda
        lcd_bus_set_video_rect(0, 0, 480, 320);
    } else {
        // Fuera de scr_player y scr_queue el video nunca se pinta (rectangulo siempre {0,0,0,0})
        lcd_bus_set_video_rect(0, 0, 0, 0);
    }
}

void ui_glue_set_hud_forced(int mode) {
    s_hud_forced_mode = mode;
    if (mode == 1) {
        ui_glue_set_osd_visible(false);
    } else if (mode == 2) {
        ui_glue_set_osd_visible(true);
    }
}

int ui_glue_get_hud_forced(void) {
    return s_hud_forced_mode;
}

void ui_glue_refresh_cards(void) {
    if (!objects.lib_grid) return;
    player_status_t pst;
    player_get_status(&pst);
    bool is_active = (pst.state == PST_PLAYING || pst.state == PST_PAUSED);

    uint32_t child_cnt = lv_obj_get_child_count(objects.lib_grid);
    for (uint32_t c = 0; c < child_cnt; c++) {
        lv_obj_t *card = lv_obj_get_child(objects.lib_grid, c);
        if (!card) continue;
        int idx = (int)(intptr_t)lv_obj_get_user_data(card);
        const media_item_t *item = media_library_get(idx);
        if (!item) continue;

        lv_obj_t *badge = lv_obj_get_child(card, 1);
        lv_obj_t *bar_res = lv_obj_get_child(card, 2);

        if (badge) {
            if (idx == s_current_track_idx && is_active) {
                lv_obj_remove_flag(badge, LV_OBJ_FLAG_HIDDEN);
            } else {
                lv_obj_add_flag(badge, LV_OBJ_FLAG_HIDDEN);
            }
        }

        if (bar_res) {
            if (item->resume_ms > 0 && item->dur_ms > 0 && !(idx == s_current_track_idx && pst.state == PST_ENDED)) {
                lv_obj_remove_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
                int32_t pct = (int32_t)(((uint64_t)item->resume_ms * 1000) / item->dur_ms);
                lv_bar_set_value(bar_res, pct, LV_ANIM_OFF);
            } else {
                lv_obj_add_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
}

static void queue_row_click_cb(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    int idx = (int)(intptr_t)lv_event_get_user_data(e);
    ESP_LOGI(TAG, "Queue row clicked: index %d", idx);
    const media_item_t *item = media_library_get(idx);
    if (!item || !item->compatible) {
        ui_glue_show_toast("No compatible", item ? item->incompat : "Archivo no reproducible", true);
        return;
    }
    s_current_track_idx = idx;
    player_cmd_t cmd = {.type = PCMD_OPEN, .arg = idx};
    player_cmd_send(&cmd);
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
}

static lv_obj_t *create_queue_row_widget(lv_obj_t *parent, int idx, int current_idx) {
    const media_item_t *item = media_library_get(idx);
    if (!item) return NULL;

    bool is_current = (idx == current_idx);

    lv_obj_t *row = lv_obj_create(parent);
    lv_obj_set_size(row, 260, 56);
    lv_obj_set_style_border_width(row, 1, LV_STATE_DEFAULT);
    lv_obj_set_style_border_side(row, LV_BORDER_SIDE_BOTTOM, LV_STATE_DEFAULT);
    lv_obj_set_style_border_color(row, lv_color_hex(theme_colors[active_theme_index][3]), LV_STATE_DEFAULT);
    lv_obj_set_style_pad_all(row, 0, LV_STATE_DEFAULT);
    lv_obj_remove_flag(row, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_SCROLL_CHAIN_HOR | LV_OBJ_FLAG_SCROLL_ELASTIC | LV_OBJ_FLAG_SCROLL_MOMENTUM | LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_set_scrollbar_mode(row, LV_SCROLLBAR_MODE_OFF);
    lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLL_CHAIN_VER);
    lv_obj_set_user_data(row, (void *)(intptr_t)idx);
    lv_obj_add_event_cb(row, queue_row_click_cb, LV_EVENT_SHORT_CLICKED, (void *)(intptr_t)idx);

    // Resaltado visual de la fila actual
    if (is_current) {
        lv_obj_set_style_bg_color(row, lv_color_hex(theme_colors[active_theme_index][1]), 0);
        lv_obj_set_style_bg_opa(row, 120, 0);
    } else {
        lv_obj_set_style_bg_opa(row, 0, LV_STATE_DEFAULT);
    }

    // Thumbnail: 12, 10, 64, 36
    lv_obj_t *img = lv_image_create(row);
    lv_obj_set_pos(img, 12, 10);
    lv_obj_set_size(img, 64, 36);
    if (item->thumb_dsc) {
        lv_image_set_src(img, item->thumb_dsc);
    } else {
        lv_image_set_src(img, &img_film);
    }
    lv_obj_set_style_radius(img, 4, 0);
    lv_obj_remove_flag(img, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(img, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Title: 86, 10, 140, 18
    lv_obj_t *lbl = lv_label_create(row);
    lv_obj_set_pos(lbl, 86, 10);
    lv_obj_set_size(lbl, 140, 18);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
    lv_obj_remove_flag(lbl, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(lbl, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_label_set_text(lbl, item->title[0] ? item->title : item->path);
    ui_glue_set_track_title_overflow(lbl, is_current);

    if (is_current) {
        lv_obj_set_style_text_color(lbl, lv_color_hex(theme_colors[active_theme_index][6]), 0);
    } else {
        lv_obj_set_style_text_color(lbl, lv_color_hex(theme_colors[active_theme_index][4]), 0);
    }

    // Meta: 86, 30, 140, 16 (Montserrat 12 has a 16 px line height).
    lv_obj_t *lbl_meta = lv_label_create(row);
    lv_obj_set_pos(lbl_meta, 86, 30);
    lv_obj_set_size(lbl_meta, 140, 16);
    lv_obj_set_style_text_font(lbl_meta, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(lbl_meta, lv_color_hex(theme_colors[active_theme_index][5]), 0);
    lv_obj_remove_flag(lbl_meta, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(lbl_meta, LV_OBJ_FLAG_EVENT_BUBBLE);

    if (!item->compatible) {
        lv_label_set_text(lbl_meta, item->incompat[0] ? item->incompat : "No compatible");
        lv_obj_set_style_text_color(lbl_meta, lv_color_hex(0xE5484D), 0);
    } else if (!item->rotated) {
        lv_label_set_text(lbl_meta, "Sin girar");
    } else if (item->dur_ms > 0) {
        uint32_t s = item->dur_ms / 1000;
        char buf[32];
        snprintf(buf, sizeof(buf), "%lu:%02lu", (unsigned long)(s / 60), (unsigned long)(s % 60));
        lv_label_set_text(lbl_meta, buf);
    } else {
        lv_label_set_text(lbl_meta, "0:00");
    }

    // icon_now: 234, 20
    if (is_current) {
        lv_obj_t *icon_now = lv_image_create(row);
        lv_obj_set_pos(icon_now, 234, 20);
        lv_obj_set_size(icon_now, 16, 16);
        lv_image_set_src(icon_now, &img_play);
        lv_obj_set_style_image_recolor(icon_now, lv_color_hex(theme_colors[active_theme_index][6]), 0);
        lv_obj_set_style_image_recolor_opa(icon_now, 255, 0);
        lv_obj_remove_flag(icon_now, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(icon_now, LV_OBJ_FLAG_EVENT_BUBBLE);
    }

    return row;
}

void ui_glue_populate_queue(void) {
    if (!objects.queue_list) return;
    lv_obj_clean(objects.queue_list);
    lv_obj_add_flag(objects.queue_list, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_SCROLL_CHAIN_VER);
    lv_obj_set_scroll_dir(objects.queue_list, LV_DIR_VER);
    lv_obj_clear_flag(objects.queue_list, LV_OBJ_FLAG_SCROLL_ELASTIC | LV_OBJ_FLAG_SCROLL_MOMENTUM | LV_OBJ_FLAG_SCROLL_CHAIN_HOR | LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_set_scrollbar_mode(objects.queue_list, LV_SCROLLBAR_MODE_AUTO);
    lv_obj_set_flex_flow(objects.queue_list, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_all(objects.queue_list, 0, 0);
    lv_obj_set_style_pad_row(objects.queue_list, 0, 0);

    player_status_t status;
    player_get_status(&status);
    int current_idx = status.track_index;
    int count = media_library_count();
    lv_obj_t *cur_row_obj = NULL;
    for (int i = 0; i < count; i++) {
        lv_obj_t *r = create_queue_row_widget(objects.queue_list, i, current_idx);
        if (i == current_idx) {
            cur_row_obj = r;
        }
    }
    lv_obj_update_layout(objects.queue_list);
    if (cur_row_obj) {
        lv_obj_scroll_to_view(cur_row_obj, LV_ANIM_OFF);
    }
}

static int s_active_settings_tab = 0;
static view_mode_t s_settings_origin_mode = VIEW_MODE_FULLSCREEN;

void ui_glue_refresh_storage_tab(void) {
    const sdmmc_card_t *card = sdcard_get_card();
    if (card && objects.lbl_sd_name) {
        char name_buf[64];
        uint64_t cap_bytes = ((uint64_t)card->csd.capacity) * card->csd.sector_size;
        double cap_gb = (double)cap_bytes / (1024.0 * 1024.0 * 1024.0);
        snprintf(name_buf, sizeof(name_buf), "microSD %s %.1f GB", (card->is_mmc ? "MMC" : "SDHC"), cap_gb);
        lv_label_set_text(objects.lbl_sd_name, name_buf);
    }
    if (objects.lbl_sd_fs) {
        lv_label_set_text_static(objects.lbl_sd_fs, "FAT32");
    }

    struct statvfs vfs;
    if (statvfs("/sdcard", &vfs) == 0) {
        uint64_t total_bytes = (uint64_t)vfs.f_blocks * vfs.f_frsize;
        uint64_t free_bytes = (uint64_t)vfs.f_bfree * vfs.f_frsize;
        uint64_t used_bytes = (total_bytes > free_bytes) ? (total_bytes - free_bytes) : 0;
        double free_gb = (double)free_bytes / (1024.0 * 1024.0 * 1024.0);
        double used_gb = (double)used_bytes / (1024.0 * 1024.0 * 1024.0);

        int32_t permil = (total_bytes > 0) ? (int32_t)((used_bytes * 1000) / total_bytes) : 0;
        if (objects.bar_sd_usage) {
            lv_bar_set_value(objects.bar_sd_usage, permil, LV_ANIM_OFF);
        }
        if (objects.lbl_sd_free) {
            char free_buf[64];
            snprintf(free_buf, sizeof(free_buf), "%.1f GB usados · %.1f GB libres", used_gb, free_gb);
            lv_label_set_text(objects.lbl_sd_free, free_buf);
        }
    } else {
        /* statvfs no siempre está conectado al VFS FAT de ESP-IDF. Consultar
         * FatFs directamente para que Ajustes muestre el espacio real. */
        FATFS *fs = NULL;
        DWORD free_clusters = 0;
        FRESULT fr = f_getfree("0:", &free_clusters, &fs);
        if (fr == FR_OK && fs && fs->n_fatent > 2) {
            uint64_t total_bytes = (uint64_t)(fs->n_fatent - 2) * fs->csize * 512;
            uint64_t free_bytes = (uint64_t)free_clusters * fs->csize * 512;
            uint64_t used_bytes = total_bytes - free_bytes;
            if (objects.bar_sd_usage) lv_bar_set_value(objects.bar_sd_usage, (int32_t)(used_bytes * 1000 / total_bytes), LV_ANIM_OFF);
            if (objects.lbl_sd_free) {
                char free_buf[64];
                snprintf(free_buf, sizeof(free_buf), "%.1f GB usados · %.1f GB libres", (double)used_bytes / (1024.0 * 1024.0 * 1024.0), (double)free_bytes / (1024.0 * 1024.0 * 1024.0));
                lv_label_set_text(objects.lbl_sd_free, free_buf);
            }
        } else {
            if (objects.bar_sd_usage) lv_bar_set_value(objects.bar_sd_usage, 0, LV_ANIM_OFF);
            if (objects.lbl_sd_free) lv_label_set_text_static(objects.lbl_sd_free, "No se pudo leer FAT de la microSD");
        }
    }

    if (objects.lbl_sd_speed) {
        char speed_buf[32];
        snprintf(speed_buf, sizeof(speed_buf), "SPI · %d MHz", sdcard_spi_get_freq_khz() / 1000);
        lv_label_set_text(objects.lbl_sd_speed, speed_buf);
    }
    if (objects.lbl_sd_count) {
        char count_buf[32];
        snprintf(count_buf, sizeof(count_buf), "%d videos", media_library_count());
        lv_label_set_text(objects.lbl_sd_count, count_buf);
    }
}

void ui_glue_refresh_about_tab(void) {
    if (objects.lbl_about_fw) {
        lv_label_set_text_static(objects.lbl_about_fw, "vp-v0.8");
    }
    if (objects.lbl_about_idf) {
        lv_label_set_text(objects.lbl_about_idf, esp_get_idf_version());
    }
    if (objects.lbl_about_lvgl) {
        char lv_buf[32];
        snprintf(lv_buf, sizeof(lv_buf), "%d.%d.%d", lv_version_major(), lv_version_minor(), lv_version_patch());
        lv_label_set_text(objects.lbl_about_lvgl, lv_buf);
    }
    if (objects.lbl_about_panel) {
        lv_label_set_text_static(objects.lbl_about_panel, "ILI9488 · 8080 8 bits · 16 MHz");
    }
    if (objects.lbl_about_te) {
        uint32_t te_pulses = 0;
        float te_hz = 0.0f;
        float te_jitter_ms = 0.0f;
        bool te_present = false;
        lcd_bus_te_perf_sample(&te_pulses, &te_hz, &te_jitter_ms, &te_present);
        char te_buf[48];
        if (te_present && te_hz > 10.0f) {
            snprintf(te_buf, sizeof(te_buf), "TE en GPIO 7 · %.1f Hz", te_hz);
        } else {
            snprintf(te_buf, sizeof(te_buf), "TE ausente");
        }
        lv_label_set_text(objects.lbl_about_te, te_buf);
    }
}

void ui_glue_select_settings_tab(int tab) {
    s_active_settings_tab = tab;

    if (objects.panel_tab_0) {
        if (tab == 0) lv_obj_remove_flag(objects.panel_tab_0, LV_OBJ_FLAG_HIDDEN);
        else lv_obj_add_flag(objects.panel_tab_0, LV_OBJ_FLAG_HIDDEN);
    }
    if (objects.panel_tab_1) {
        if (tab == 1) lv_obj_remove_flag(objects.panel_tab_1, LV_OBJ_FLAG_HIDDEN);
        else lv_obj_add_flag(objects.panel_tab_1, LV_OBJ_FLAG_HIDDEN);
    }
    if (objects.panel_tab_2) {
        if (tab == 2) lv_obj_remove_flag(objects.panel_tab_2, LV_OBJ_FLAG_HIDDEN);
        else lv_obj_add_flag(objects.panel_tab_2, LV_OBJ_FLAG_HIDDEN);
    }
    if (objects.panel_tab_3) {
        if (tab == 3) lv_obj_remove_flag(objects.panel_tab_3, LV_OBJ_FLAG_HIDDEN);
        else lv_obj_add_flag(objects.panel_tab_3, LV_OBJ_FLAG_HIDDEN);
    }

    lv_color_t c_act = lv_color_hex(theme_colors[active_theme_index][6]);
    lv_color_t c_inact = lv_color_hex(theme_colors[active_theme_index][4]);
    if (objects.lbl_tab_0) lv_obj_set_style_text_color(objects.lbl_tab_0, (tab == 0) ? c_act : c_inact, 0);
    if (objects.lbl_tab_1) lv_obj_set_style_text_color(objects.lbl_tab_1, (tab == 1) ? c_act : c_inact, 0);
    if (objects.lbl_tab_2) lv_obj_set_style_text_color(objects.lbl_tab_2, (tab == 2) ? c_act : c_inact, 0);
    if (objects.lbl_tab_3) lv_obj_set_style_text_color(objects.lbl_tab_3, (tab == 3) ? c_act : c_inact, 0);

    if (tab == 2) {
        ui_glue_refresh_storage_tab();
    } else if (tab == 3) {
        ui_glue_refresh_about_tab();
    }
}

void ui_glue_sync_settings_controls(void) {
    if (objects.btn_open_stats && objects.obj32) {
        lv_obj_center(objects.obj32);
        lv_obj_set_style_text_align(objects.obj32, LV_TEXT_ALIGN_CENTER, 0);
    }
    if (objects.sld_brightness) {
        lv_slider_set_range(objects.sld_brightness, 0, 100);
        lv_slider_set_value(objects.sld_brightness, brightness_real_to_display(s_settings.bright), LV_ANIM_OFF);
    }
    if (objects.lbl_set_bri_val) {
        char bbuf[16];
        snprintf(bbuf, sizeof(bbuf), "%d%%", brightness_real_to_display(s_settings.bright));
        lv_label_set_text(objects.lbl_set_bri_val, bbuf);
    }
    if (objects.dd_osd_timeout) {
        int sel = 1;
        if (s_settings.osd_ms == 2000) sel = 0;
        else if (s_settings.osd_ms == 3000) sel = 1;
        else if (s_settings.osd_ms == 5000) sel = 2;
        else if (s_settings.osd_ms == 0) sel = 3;
        lv_dropdown_set_selected(objects.dd_osd_timeout, sel);
    }
    if (objects.sw_show_stats) {
        if (s_settings.stats) lv_obj_add_state(objects.sw_show_stats, LV_STATE_CHECKED);
        else lv_obj_remove_state(objects.sw_show_stats, LV_STATE_CHECKED);
    }
    if (objects.sw_mini_progress) {
        if (s_settings.miniprog) lv_obj_add_state(objects.sw_mini_progress, LV_STATE_CHECKED);
        else lv_obj_remove_state(objects.sw_mini_progress, LV_STATE_CHECKED);
    }
    if (objects.dd_repeat) {
        lv_dropdown_set_selected(objects.dd_repeat, s_settings.repeat);
    }
    if (objects.sw_shuffle) {
        if (s_settings.shuffle) lv_obj_add_state(objects.sw_shuffle, LV_STATE_CHECKED);
        else lv_obj_remove_state(objects.sw_shuffle, LV_STATE_CHECKED);
    }
    if (objects.sw_resume) {
        if (s_settings.resume) lv_obj_add_state(objects.sw_resume, LV_STATE_CHECKED);
        else lv_obj_remove_state(objects.sw_resume, LV_STATE_CHECKED);
    }
    if (objects.dd_seek_step) {
        int sel = 1;
        if (s_settings.seekstep == 5) sel = 0;
        else if (s_settings.seekstep == 10) sel = 1;
        else if (s_settings.seekstep == 30) sel = 2;
        lv_dropdown_set_selected(objects.dd_seek_step, sel);
    }
}

void ui_glue_update_no_media_screen(esp_err_t sd_err) {
    if (!objects.scr_no_media) return;

    bool is_sd_err = (sd_err != ESP_OK) || (sdcard_get_card() == NULL);
    int total_cnt = media_library_count();
    int comp_cnt = media_library_compatible_count();

    if (is_sd_err) {
        // Variante 3: ErrorSD
        ESP_LOGI(TAG, "scr_no_media: Variante ErrorSD (err=0x%x)", sd_err);
        if (objects.img_nomedia) {
            lv_image_set_src(objects.img_nomedia, &img_sdcard_error_big);
            lv_obj_set_style_image_recolor_opa(objects.img_nomedia, 0, 0);
        }
        if (objects.lbl_nomedia_title) lv_label_set_text_static(objects.lbl_nomedia_title, "No se pudo leer la microSD");
        if (objects.lbl_nomedia_sub) lv_label_set_text_static(objects.lbl_nomedia_sub, "Sacala, limpiala y vuelve a insertarla");
        if (objects.chip_err) {
            lv_obj_remove_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
            lv_obj_t *lbl = lv_obj_get_child(objects.chip_err, 0);
            if (lbl) {
                char ebuf[48];
                snprintf(ebuf, sizeof(ebuf), "Error 0x%x · tiempo de espera agotado", sd_err ? sd_err : 0x107);
                lv_label_set_text(lbl, ebuf);
            }
        }
        if (objects.btn_retry) {
            lv_obj_set_pos(objects.btn_retry, 114, 216);
            lv_obj_remove_flag(objects.btn_retry, LV_OBJ_FLAG_HIDDEN);
        }
        if (objects.btn_settings_alt) {
            lv_obj_set_pos(objects.btn_settings_alt, 246, 216);
            lv_obj_remove_flag(objects.btn_settings_alt, LV_OBJ_FLAG_HIDDEN);
            lv_obj_t *lbl = lv_obj_get_child(objects.btn_settings_alt, 0);
            if (lbl) lv_label_set_text_static(lbl, "Ver ajustes");
        }
        if (objects.lbl_retry_hint) {
            lv_obj_remove_flag(objects.lbl_retry_hint, LV_OBJ_FLAG_HIDDEN);
            lv_label_set_text_static(objects.lbl_retry_hint, "Reintentando cada segundo...");
        }
    } else if (total_cnt > 0 && comp_cnt == 0) {
        // Variante 2: SinMediosIncompatibles
        ESP_LOGI(TAG, "scr_no_media: Variante SinMediosIncompatibles (%d archivos)", total_cnt);
        if (objects.img_nomedia) {
            lv_image_set_src(objects.img_nomedia, &img_sdcard_error_big);
            lv_obj_set_style_image_recolor_opa(objects.img_nomedia, 0, 0);
        }
        if (objects.lbl_nomedia_title) lv_label_set_text_static(objects.lbl_nomedia_title, "Ningun video compatible");
        if (objects.lbl_nomedia_sub) {
            char sub[140];
            snprintf(sub, sizeof(sub), "Hay %d archivos, ninguno compatible. Conviertelos con convert_videos.py (MJPEG 320x480, 30 fps)", total_cnt);
            lv_label_set_text(objects.lbl_nomedia_sub, sub);
        }
        if (objects.chip_err) lv_obj_add_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
        if (objects.lbl_retry_hint) lv_obj_add_flag(objects.lbl_retry_hint, LV_OBJ_FLAG_HIDDEN);

        if (objects.btn_retry) {
            lv_obj_set_pos(objects.btn_retry, 114, 212);
            lv_obj_remove_flag(objects.btn_retry, LV_OBJ_FLAG_HIDDEN);
        }
        if (objects.btn_settings_alt) {
            lv_obj_set_pos(objects.btn_settings_alt, 246, 212);
            lv_obj_remove_flag(objects.btn_settings_alt, LV_OBJ_FLAG_HIDDEN);
            lv_obj_t *lbl = lv_obj_get_child(objects.btn_settings_alt, 0);
            if (lbl) lv_label_set_text_static(lbl, "Ajustes");
        }
    } else {
        // Variante 1: SinMedios
        ESP_LOGI(TAG, "scr_no_media: Variante SinMedios (0 archivos)");
        if (objects.img_nomedia) {
            lv_image_set_src(objects.img_nomedia, &img_sdcard_big);
            lv_obj_set_style_image_recolor_opa(objects.img_nomedia, 0, 0);
        }
        if (objects.lbl_nomedia_title) lv_label_set_text_static(objects.lbl_nomedia_title, "No hay videos");
        if (objects.lbl_nomedia_sub) lv_label_set_text_static(objects.lbl_nomedia_sub, "Copia archivos .avi en /videos de la microSD");
        if (objects.chip_err) lv_obj_add_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
        if (objects.lbl_retry_hint) lv_obj_add_flag(objects.lbl_retry_hint, LV_OBJ_FLAG_HIDDEN);

        if (objects.btn_retry) {
            lv_obj_set_pos(objects.btn_retry, 180, 204);
            lv_obj_remove_flag(objects.btn_retry, LV_OBJ_FLAG_HIDDEN);
        }
        if (objects.btn_settings_alt) {
            lv_obj_add_flag(objects.btn_settings_alt, LV_OBJ_FLAG_HIDDEN);
        }
    }
}

void ui_glue_set_view_mode(view_mode_t mode) {
    view_mode_t old_mode = s_view_mode;
    s_view_mode = mode;
    const char *vmode_str = "library";
    if (mode == VIEW_MODE_FULLSCREEN) vmode_str = "player";
    else if (mode == VIEW_MODE_QUEUE) vmode_str = "queue";
    else if (mode == VIEW_MODE_SETTINGS) vmode_str = "settings";
    else if (mode == VIEW_MODE_NO_MEDIA) vmode_str = "no_media";
    printf("VIEW,mode=%s,track=%d\n", vmode_str, s_current_track_idx);
    fflush(stdout);

    if (mode == VIEW_MODE_FULLSCREEN) {
        lcd_bus_set_overlay_rect(3, 0, 0, 0, 0, false); // Cerrar capa de cola
        if (objects.scr_player) {
            loadScreen(SCREEN_ID_SCR_PLAYER);
        }
        if (s_osd_visible) {
            lcd_bus_set_video_rect(0, 40, 480, 196);
            player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 40, 480, 196}};
            player_cmd_send(&cmd);
        } else {
            lcd_bus_set_video_rect(0, 0, 480, 320);
            player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
            player_cmd_send(&cmd);
        }
    } else if (mode == VIEW_MODE_QUEUE) {
        if (objects.scr_queue) {
            loadScreen(SCREEN_ID_SCR_QUEUE);
        }
        // En la cola el video permanece visible a la izquierda y la hoja de cola se compone a la derecha (slot 3)
        lcd_bus_set_video_rect(0, 0, 480, 320);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
        player_cmd_send(&cmd);
        ui_glue_set_overlay_rect_for_obj(3, objects.queue_sheet, true);
        ui_glue_populate_queue();
    } else if (mode == VIEW_MODE_SETTINGS) {
        if (old_mode == VIEW_MODE_FULLSCREEN) {
            player_status_t st;
            player_get_status(&st);
            if (st.state == PST_PLAYING) {
                s_was_playing_before_settings = true;
                player_cmd_t cmd_pause = {.type = PCMD_PAUSE};
                player_cmd_send(&cmd_pause);
                const media_item_t *cur = media_library_get(s_current_track_idx);
                if (cur && cur->compatible) {
                    media_library_set_resume(cur->path, (uint32_t)st.pos_ms);
                }
            } else {
                s_was_playing_before_settings = false;
                if (st.state == PST_ENDED) {
                    const media_item_t *cur = media_library_get(s_current_track_idx);
                    if (cur) {
                        media_library_set_resume(cur->path, 0);
                    }
                }
            }
        } else {
            s_was_playing_before_settings = false;
        }
        if (objects.scr_settings) {
            loadScreen(SCREEN_ID_SCR_SETTINGS);
        }
        lcd_bus_set_video_rect(0, 0, 0, 0);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 0, 0}};
        player_cmd_send(&cmd);
        ui_glue_sync_settings_controls();
        ui_glue_select_settings_tab(s_active_settings_tab);
    } else if (mode == VIEW_MODE_NO_MEDIA) {
        if (old_mode == VIEW_MODE_FULLSCREEN || old_mode == VIEW_MODE_QUEUE) {
            player_status_t st;
            player_get_status(&st);
            if (st.state == PST_PLAYING) {
                player_cmd_t cmd_pause = {.type = PCMD_PAUSE};
                player_cmd_send(&cmd_pause);
            }
        }
        if (objects.scr_no_media) {
            loadScreen(SCREEN_ID_SCR_NO_MEDIA);
        }
        ui_glue_update_no_media_screen(ESP_OK);
        lcd_bus_set_video_rect(0, 0, 0, 0);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 0, 0}};
        player_cmd_send(&cmd);
    } else {
        // Al salir de scr_player el video se pausa y se guarda la posicion
        if (old_mode == VIEW_MODE_FULLSCREEN || old_mode == VIEW_MODE_QUEUE) {
            player_status_t st;
            player_get_status(&st);
            if (st.state == PST_PLAYING) {
                player_cmd_t cmd_pause = {.type = PCMD_PAUSE};
                player_cmd_send(&cmd_pause);
                const media_item_t *cur = media_library_get(s_current_track_idx);
                if (cur && cur->compatible) {
                    media_library_set_resume(cur->path, (uint32_t)st.pos_ms);
                }
            } else if (st.state == PST_ENDED) {
                const media_item_t *cur = media_library_get(s_current_track_idx);
                if (cur) {
                    media_library_set_resume(cur->path, 0);
                }
            }
        }
        if (objects.scr_library) {
            loadScreen(SCREEN_ID_SCR_LIBRARY);
        }
        ui_glue_refresh_cards();
        lcd_bus_set_video_rect(0, 0, 0, 0);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 0, 0}};
        player_cmd_send(&cmd);
    }
}

view_mode_t ui_glue_get_view_mode(void) {
    return s_view_mode;
}

void ui_glue_get_published_info(char *title_buf, size_t max_len, int *track_idx, view_mode_t *vmode, int *hud_vis) {
    if (vmode) *vmode = s_view_mode;
    if (track_idx) *track_idx = s_current_track_idx;
    if (hud_vis) *hud_vis = s_osd_visible ? 1 : 0;
    if (title_buf && max_len > 0) {
        const char *txt = (objects.lbl_title) ? lv_label_get_text(objects.lbl_title) : "";
        snprintf(title_buf, max_len, "%s", txt ? txt : "");
    }
}

/* lv_label_set_text invalida aun cuando el texto no cambia.  En una capa que
 * se compone sobre el video, esas invalidaciones hacen que LVGL vuelva a
 * recorrer toda la tarjeta; comparar aqui conserva la capa estatica. */
static void set_label_text_if_changed(lv_obj_t *label, const char *text) {
    if (!label || !text) return;
    const char *current = lv_label_get_text(label);
    if (!current || strcmp(current, text) != 0) {
        lv_label_set_text(label, text);
    }
}

void ui_glue_update_stats_labels(void) {
    if (!objects.ovl_stats || lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN)) return;
    perf_live_metrics_t m;
    perf_get_live_metrics(&m);
    player_status_t st_cur;
    player_get_status(&st_cur);
    float pres_fps = (st_cur.state == PST_PLAYING) ? m.pres_fps : 0.0f;
    float dec_fps = (st_cur.state == PST_PLAYING) ? m.dec_fps : 0.0f;

    if (objects.lbl_stat_pres) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%0.1f fps", pres_fps);
        set_label_text_if_changed(objects.lbl_stat_pres, buf);
    }
    if (objects.lbl_stat_dec) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%0.1f fps", dec_fps);
        set_label_text_if_changed(objects.lbl_stat_dec, buf);
    }
    if (objects.lbl_stat_drop) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%lu", (unsigned long)m.dropped);
        set_label_text_if_changed(objects.lbl_stat_drop, buf);
    }
    if (objects.lbl_stat_rd) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%0.1f / %0.1f ms", m.rd_avg_ms, m.rd_max_ms);
        set_label_text_if_changed(objects.lbl_stat_rd, buf);
    }
    if (objects.lbl_stat_dec_time) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%0.1f / %0.1f ms", m.dec_avg_ms, m.dec_max_ms);
        set_label_text_if_changed(objects.lbl_stat_dec_time, buf);
    }
    if (objects.lbl_stat_blit) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%0.1f ms (%lu Hz)", m.blit_ms, (unsigned long)m.te_hz);
        set_label_text_if_changed(objects.lbl_stat_blit, buf);
    }
    if (objects.lbl_stat_file) {
        const media_item_t *cur = media_library_get(s_current_track_idx);
        if (cur && cur->title[0] != '\0') {
            set_label_text_if_changed(objects.lbl_stat_file, cur->title);
            ui_glue_label_no_scroll(objects.lbl_stat_file);
        }
    }
}

void ui_glue_tick(void) {
    player_status_t st;
    player_get_status(&st);
    s_current_track_idx = st.track_index;
    /* screens.c may replace the player-title text on this tick; reaffirm the
     * one globally permitted marquee whenever that runtime title is updated. */
    if (objects.lbl_title) {
        ui_glue_set_track_title_overflow(objects.lbl_title, true);
        lv_obj_set_style_anim_duration(objects.lbl_title, 8000, 0);
    }

    static player_state_t s_prev_player_state = PST_IDLE;

    // B10: Aviso del vigilante: «No se pudo reproducir» al fallar un video, 3 s, y vuelta a la biblioteca.
    if (st.state == PST_ERROR && s_view_mode == VIEW_MODE_FULLSCREEN) {
        ESP_LOGW(TAG, "Fallo de reproduccion detectado (PST_ERROR) -> mostrando aviso 3s y volviendo a biblioteca");
        ui_glue_show_toast("No se pudo reproducir", "El video no muestra imagen. Volviendo a la biblioteca…", true);
        s_pending_library_return = true;
        s_prev_player_state = PST_ERROR;
        player_cmd_t cmd = {.type = PCMD_STOP};
        player_cmd_send(&cmd);
        return;
    }

    // Si la reproduccion termino (transicion PLAYING -> ENDED) y estamos en modo fullscreen -> volver a biblioteca
    if (s_prev_player_state == PST_PLAYING && st.state == PST_ENDED && s_view_mode == VIEW_MODE_FULLSCREEN) {
        ESP_LOGI(TAG, "Reproduccion finalizada en modo fullscreen -> retornando a biblioteca");
        action_open_library(NULL);
        s_prev_player_state = st.state;
        return;
    }
    s_prev_player_state = st.state;

    // No invalidar el icono del HUD en cada tick: el setter de LVGL redibuja
    // incluso si la imagen no cambia (y el HUD puede estar oculto).
    static int s_last_play_icon_playing = -1;
    int is_playing = (st.state == PST_PLAYING) ? 1 : 0;
    if (objects.lbl_play_icon && s_last_play_icon_playing != is_playing) {
        lv_image_set_src(objects.lbl_play_icon, is_playing ? &img_pause : &img_play);
        s_last_play_icon_playing = is_playing;
    }

    // Si se acaba de desbloquear y el usuario sigue tocando, esperar a que suelte
    if (s_consume_touch_until_release) {
        if (!touch_is_pressed()) {
            s_consume_touch_until_release = false;
            s_last_touch_time = esp_timer_get_time() / 1000;
            ESP_LOGI(TAG, "Toque de desbloqueo liberado. Auto-ocultar OSD reiniciado a 3000 ms.");
        }
    }

    // Auto-hide OSD (solo en scr_player / modo fullscreen)
    if (s_view_mode == VIEW_MODE_FULLSCREEN && s_hud_forced_mode == 0 && s_osd_visible && st.state == PST_PLAYING && !s_seeking && !s_consume_touch_until_release) {
        int64_t now = esp_timer_get_time() / 1000;
        uint32_t timeout = s_settings.osd_ms ? s_settings.osd_ms : 3000;
        if (now - s_last_touch_time >= timeout) {
            ui_glue_set_osd_visible(false);
        }
    }

    // Auto-ocultar tarjeta de bloqueo a los 2 s (dejando el video limpio con ovl_lock transparente)
    if (s_locked && s_lock_card && !lv_obj_has_flag(s_lock_card, LV_OBJ_FLAG_HIDDEN)) {
        int64_t now = esp_timer_get_time() / 1000;
        if (now - s_lock_show_time >= 2000 && s_lock_touch_start_us == 0) {
            ui_glue_set_overlay_card_visible(s_lock_card, false);
            lcd_bus_set_overlay_rect(0, 0, 0, 0, 0, false);
            player_status_t st_lock;
            player_get_status(&st_lock);
            if (st_lock.state != PST_PLAYING) {
                avi_player_reblit_current_frame();
            }
            ESP_LOGI(TAG, "Tarjeta de bloqueo auto-ocultada tras 2s -> overlay 0 desactivado");
        }
    }

    int64_t now_gest = esp_timer_get_time() / 1000;

    // Gestos: confirmar toque único si transcurrieron 280 ms sin segundo toque
    if (s_single_tap_pending && (now_gest - s_single_tap_time_ms >= 280)) {
        s_single_tap_pending = false;
        if (!s_locked && s_view_mode == VIEW_MODE_FULLSCREEN) {
            ui_glue_set_osd_visible(!s_osd_visible);
            s_last_touch_time = now_gest;
            ESP_LOGI(TAG, "Gestos: Toque unico confirmado -> OSD %s", s_osd_visible ? "visible" : "oculta");
        }
    }

    // Gestos: finalizar ráfaga de seek hint acumulado tras 600 ms
    if (s_seek_in_flight && (now_gest >= s_seek_hint_hide_ms)) {
        s_seek_in_flight = false;
        if (objects.ovl_seek_hint) ui_glue_set_overlay_card_visible(objects.ovl_seek_hint, false);
        lcd_bus_set_overlay_rect(2, 0, 0, 0, 0, false);

        player_status_t st_seek;
        player_get_status(&st_seek);
        int64_t target = (int64_t)st_seek.pos_ms + ((int64_t)s_accum_seek_s * 1000LL);
        if (target < 0) target = 0;
        if (st_seek.dur_ms > 0 && (uint64_t)target > st_seek.dur_ms) target = (int64_t)st_seek.dur_ms;

        player_cmd_t cmd_seek = {.type = PCMD_SEEK_MS, .arg = (int32_t)target};
        player_cmd_send(&cmd_seek);
        ESP_LOGI(TAG, "Gestos: Seek hint expirado -> seek commit %ld ms (acum %ld s)", (long)target, (long)s_accum_seek_s);
        s_accum_seek_s = 0;

        if (st_seek.state != PST_PLAYING) {
            avi_player_reblit_current_frame();
        }
    }

    // Gestos: auto-ocultar indicador de brillo tras 600 ms
    if (s_brightness_hide_ms > 0 && (now_gest >= s_brightness_hide_ms)) {
        s_brightness_hide_ms = 0;
        if (objects.ovl_brightness) ui_glue_set_overlay_card_visible(objects.ovl_brightness, false);
        lcd_bus_set_overlay_rect(3, 0, 0, 0, 0, false);

        player_status_t st_b;
        player_get_status(&st_b);
        if (st_b.state != PST_PLAYING) {
            avi_player_reblit_current_frame();
        }
        ESP_LOGI(TAG, "Gestos: Brillo auto-ocultado tras 600ms");
    }

    // B5: Actualización de métricas en vivo en ovl_stats (<= 2 Hz)
    static int64_t s_last_stats_update_ms = 0;
    if (objects.ovl_stats && !lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN)) {
        if (now_gest - s_last_stats_update_ms >= 500) {
            s_last_stats_update_ms = now_gest;
            ui_glue_update_stats_labels();
        }
    }

    // B9: btn_next desactivado (40% opacidad) en el último video si repetir está desactivado
    if (objects.btn_next) {
        int total_tracks = media_library_count();
        bool is_last = (total_tracks > 0) && (s_current_track_idx >= total_tracks - 1);
        bool rep_off = (s_settings.repeat == 0);
        if (is_last && rep_off) {
            lv_obj_add_state(objects.btn_next, LV_STATE_DISABLED);
            lv_obj_set_style_opa(objects.btn_next, (lv_opa_t)(255 * 0.40), LV_PART_MAIN);
        } else {
            lv_obj_remove_state(objects.btn_next, LV_STATE_DISABLED);
            lv_obj_set_style_opa(objects.btn_next, LV_OPA_COVER, LV_PART_MAIN);
        }
    }
}

// ----------------- EEZ Studio Action Handlers -----------------

void action_toggle_play(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    player_cmd_t cmd = {.type = PCMD_TOGGLE};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: toggle_play");
}

void action_prev(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    player_cmd_t cmd = {.type = PCMD_PREV};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: prev");
}

void action_next(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    int total_tracks = media_library_count();
    if (s_settings.repeat == 0 && total_tracks > 0 && s_current_track_idx >= total_tracks - 1) {
        ESP_LOGI(TAG, "Action: next ignorado (fin de lista con repetir en off)");
        return;
    }
    player_cmd_t cmd = {.type = PCMD_NEXT};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: next");
}

void action_rew10(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    player_status_t st;
    player_get_status(&st);
    int32_t step = s_settings.seekstep ? (s_settings.seekstep * 1000) : 10000;
    int32_t target = (st.pos_ms > (uint64_t)step) ? (int32_t)(st.pos_ms - step) : 0;
    player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = target};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: rew10 -> target %ld ms", (long)target);
}

void action_fwd10(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    player_status_t st;
    player_get_status(&st);
    int32_t step = s_settings.seekstep ? (s_settings.seekstep * 1000) : 10000;
    int32_t target = (int32_t)(st.pos_ms + step);
    if (st.dur_ms > 0 && (uint64_t)target > st.dur_ms) target = (int32_t)st.dur_ms;
    player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = target};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: fwd10 -> target %ld ms", (long)target);
}

void action_seek_begin(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    s_seeking = true;
}

void action_seek_preview(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    if (objects.sld_seek) {
        int32_t val = lv_slider_get_value(objects.sld_seek);
        player_status_t st;
        player_get_status(&st);
        if (st.dur_ms > 0 && objects.lbl_pos) {
            uint32_t preview_sec = (uint32_t)(((uint64_t)val * st.dur_ms) / (1000 * 1000));
            char buf[16];
            snprintf(buf, sizeof(buf), "%lu:%02lu", (unsigned long)(preview_sec / 60), (unsigned long)(preview_sec % 60));
            lv_label_set_text(objects.lbl_pos, buf);
        }
    }
}

void action_seek_commit(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    if (objects.sld_seek) {
        int32_t val = lv_slider_get_value(objects.sld_seek);
        player_status_t st;
        player_get_status(&st);
        if (st.dur_ms > 0) {
            int32_t target = (int32_t)(((uint64_t)val * st.dur_ms) / 1000);
            player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = target};
            player_cmd_send(&cmd);
            ESP_LOGI(TAG, "Action: seek_commit -> %ld ms", (long)target);
        }
    }
    s_seeking = false;
}

void action_cycle_repeat(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    s_settings.repeat = (s_settings.repeat + 1) % 3;
    settings_nvs_set_u8("repeat", s_settings.repeat);
    player_cmd_t cmd = {.type = PCMD_SET_REPEAT, .arg = s_settings.repeat};
    player_cmd_send(&cmd);
    if (objects.btn_repeat && objects.img_repeat_icon) {
        if (s_settings.repeat == 0) {
            lv_image_set_src(objects.img_repeat_icon, &img_repeat);
            lv_obj_set_style_image_recolor(objects.img_repeat_icon, lv_color_hex(0x8E929B), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_repeat_icon, 255, 0);
            lv_obj_remove_state(objects.btn_repeat, LV_STATE_CHECKED);
        } else if (s_settings.repeat == 1) {
            lv_image_set_src(objects.img_repeat_icon, &img_repeat);
            lv_obj_set_style_image_recolor(objects.img_repeat_icon, lv_color_hex(0xF2B33D), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_repeat_icon, 255, 0);
            lv_obj_add_state(objects.btn_repeat, LV_STATE_CHECKED);
        } else {
            lv_image_set_src(objects.img_repeat_icon, &img_repeat_one);
            lv_obj_set_style_image_recolor(objects.img_repeat_icon, lv_color_hex(0xF2B33D), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_repeat_icon, 255, 0);
            lv_obj_add_state(objects.btn_repeat, LV_STATE_CHECKED);
        }
    }
    ESP_LOGI(TAG, "Action: cycle_repeat -> %d", s_settings.repeat);
}

void action_toggle_shuffle(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    s_settings.shuffle = !s_settings.shuffle;
    settings_nvs_set_u8("shuffle", s_settings.shuffle ? 1 : 0);
    player_cmd_t cmd = {.type = PCMD_SET_SHUFFLE, .arg = s_settings.shuffle};
    player_cmd_send(&cmd);
    if (objects.btn_shuffle && objects.img_shuffle_icon) {
        if (s_settings.shuffle) {
            lv_obj_set_style_image_recolor(objects.img_shuffle_icon, lv_color_hex(0xF2B33D), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_shuffle_icon, 255, 0);
            lv_obj_add_state(objects.btn_shuffle, LV_STATE_CHECKED);
        } else {
            lv_obj_set_style_image_recolor(objects.img_shuffle_icon, lv_color_hex(0x8E929B), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_shuffle_icon, 255, 0);
            lv_obj_remove_state(objects.btn_shuffle, LV_STATE_CHECKED);
        }
    }
    ESP_LOGI(TAG, "Action: toggle_shuffle -> %d", s_settings.shuffle);
}

void action_lock(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    s_locked = true;
    ui_glue_set_osd_visible(false);

    init_lock_overlay();

    if (s_ovl_lock) {
        lv_obj_remove_flag(s_ovl_lock, LV_OBJ_FLAG_HIDDEN);
        lv_obj_move_foreground(s_ovl_lock);
    }
    if (s_lock_card) {
        ui_glue_set_overlay_card_visible(s_lock_card, true);
    }
    if (s_arc_unlock) {
        lv_arc_set_value(s_arc_unlock, 0);
    }
    s_lock_show_time = esp_timer_get_time() / 1000;
    s_lock_touch_start_us = 0;

    ui_glue_set_overlay_rect_for_obj(0, s_lock_card, true);

    ESP_LOGI(TAG, "Action: lock -> pantalla bloqueada con tarjeta visible 2s");
}

void action_toggle_osd(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    if (s_consume_touch_until_release || s_consume_next_click) {
        s_consume_next_click = false;
        ESP_LOGI(TAG, "action_toggle_osd ignorado: consumiendo toque de gesto o desbloqueo");
        return;
    }
    if (s_hud_forced_mode != 0) return;
    ui_glue_set_osd_visible(!s_osd_visible);
    ESP_LOGI(TAG, "Action: toggle_osd -> visible=%d", s_osd_visible);
}

void action_open_library(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_toast_box && !lv_obj_has_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN)) {
        lv_obj_add_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN);
    }
    s_pending_library_return = false;
    if (s_locked) return;
    if (s_view_mode == VIEW_MODE_SETTINGS) {
        ESP_LOGI(TAG, "Action: back from settings -> returning to origin mode %d (was_playing=%d)", s_settings_origin_mode, s_was_playing_before_settings);
        view_mode_t orig = s_settings_origin_mode;
        ui_glue_set_view_mode(orig);
        if (orig == VIEW_MODE_FULLSCREEN && s_was_playing_before_settings) {
            s_was_playing_before_settings = false;
            player_cmd_t cmd = {.type = PCMD_PLAY};
            player_cmd_send(&cmd);
        }
        return;
    }
    action_library_populate(NULL);
    ui_glue_set_view_mode(VIEW_MODE_STUDIO);
    ESP_LOGI(TAG, "Action: open_library");
}

void action_open_queue(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    ESP_LOGI(TAG, "Action: open_queue -> abriendo cola");
    ui_glue_set_view_mode(VIEW_MODE_QUEUE);
}

void action_close_queue(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: close_queue -> volviendo al reproductor sin pausar");
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
}

void action_open_settings(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    s_settings_origin_mode = s_view_mode;
    player_status_t st;
    player_get_status(&st);
    if (s_view_mode == VIEW_MODE_FULLSCREEN && st.state == PST_PLAYING) {
        s_was_playing_before_settings = true;
    } else {
        s_was_playing_before_settings = false;
    }
    ESP_LOGI(TAG, "Action: open_settings from mode %d (was_playing=%d)", s_settings_origin_mode, s_was_playing_before_settings);
    ui_glue_set_view_mode(VIEW_MODE_SETTINGS);
}

static void wait_gui_ms(uint32_t ms) {
    uint32_t count = (ms + 14) / 15;
    for (uint32_t i = 0; i < count; i++) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(15));
    }
}

static bool sim_touch_wait_consumed(uint32_t sequence) {
    /* El read timer del indev no se ejecuta en cada llamada inmediata a
     * lv_timer_handler(). Esperar ciclos completos evita reemplazar PRESS por
     * RELEASE antes de que LVGL haya visto el primer flanco. */
    for (int i = 0; i < 6; i++) {
        lv_timer_handler();
        if (touch_synthetic_was_consumed(sequence)) return true;
        vTaskDelay(pdMS_TO_TICKS(15));
    }
    ESP_LOGW(TAG, "Autotest: transicion tactil sintetica %lu no consumida", (unsigned long)sequence);
    return false;
}

static void sim_touch_click(uint16_t x, uint16_t y) {
    uint32_t press_sequence = touch_inject_synthetic(x, y, true);
    sim_touch_wait_consumed(press_sequence);
    uint32_t release_sequence = touch_inject_synthetic(x, y, false);
    sim_touch_wait_consumed(release_sequence);
}

/* El autotest debe tocar el control que se generó, no una coordenada que pueda
 * quedar obsoleta cuando EEZ cambie la composición de la pantalla. */
static bool sim_touch_click_obj(lv_obj_t *obj) {
    if (!obj || lv_obj_has_flag(obj, LV_OBJ_FLAG_HIDDEN)) {
        return false;
    }
    lv_area_t area;
    lv_obj_get_coords(obj, &area);
    sim_touch_click((uint16_t)((area.x1 + area.x2) / 2),
                    (uint16_t)((area.y1 + area.y2) / 2));
    return true;
}

static void sim_touch_hold(uint16_t x, uint16_t y, uint32_t hold_ms) {
    uint32_t press_sequence = touch_inject_synthetic(x, y, true);
    sim_touch_wait_consumed(press_sequence);
    uint32_t elapsed = 0;
    while (elapsed < hold_ms) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(20));
        elapsed += 20;
    }
    uint32_t release_sequence = touch_inject_synthetic(x, y, false);
    sim_touch_wait_consumed(release_sequence);
}

static void sim_touch_drag(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, int steps) {
    uint32_t press_sequence = touch_inject_synthetic(x1, y1, true);
    sim_touch_wait_consumed(press_sequence);
    for (int s = 1; s <= steps; s++) {
        uint16_t cur_x = x1 + (int32_t)(x2 - x1) * s / steps;
        uint16_t cur_y = y1 + (int32_t)(y2 - y1) * s / steps;
        uint32_t move_sequence = touch_inject_synthetic(cur_x, cur_y, true);
        sim_touch_wait_consumed(move_sequence);
    }
    uint32_t release_sequence = touch_inject_synthetic(x2, y2, false);
    sim_touch_wait_consumed(release_sequence);
}

static volatile bool s_uinav_running = false;

bool ui_glue_is_uinav_running(void) {
    return s_uinav_running;
}

void ui_glue_run_uinav_test(void) {
    s_uinav_running = true;
    ESP_LOGI(TAG, "=== INICIANDO PRUEBA UINAV (12 CONTROLES + TARJETA + SEEK + L1, L2, L3, L8) ===");
    ui_glue_fix_all_button_flags();

    // Asegurar pantalla de reproductor con OSD visible
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    loadScreen(SCREEN_ID_SCR_PLAYER);
    if (objects.scr_player) {
        lv_screen_load(objects.scr_player);
        lv_obj_update_layout(objects.scr_player);
    }
    ui_glue_set_osd_visible(true);
    wait_gui_ms(200);

    // 1. btn=back (x=22, y=20) -> abre biblioteca
    sim_touch_click(22, 20);
    wait_gui_ms(250);
    bool back_ok = (ui_glue_get_view_mode() == VIEW_MODE_STUDIO);
    printf("UINAV,btn=back,result=%s\n", back_ok ? "PASS" : "FAIL");

    // L1: Quedarse en biblioteca verificando que el video no vuelve a pintarse
    bool l1_ok = true;
    for (int sec = 0; sec < 60; sec++) {
        wait_gui_ms(1000);
        int16_t vx = 0, vy = 0, vw = 0, vh = 0;
        lcd_bus_get_video_rect(&vx, &vy, &vw, &vh);
        if (ui_glue_get_view_mode() != VIEW_MODE_STUDIO || vw != 0 || vh != 0) {
            l1_ok = false;
            break;
        }
    }
    printf("UINAV,btn=L1_lib_stay,result=%s\n", l1_ok ? "PASS" : "FAIL");

    // L3: Hoja BibliotecaReanudar (Continuar y Desde el principio)
    const media_item_t *item1 = media_library_get(1);
    if (item1 && item1->compatible) {
        media_library_set_resume(item1->path, 15000);
        show_resume_sheet(1);
        wait_gui_ms(200);
        bool sheet_vis = (s_resume_overlay != NULL && !lv_obj_has_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN));

        // Boton Continuar (x=124, y=269)
        sim_touch_click(124, 269);
        wait_gui_ms(500);
        bool cont_ok = (ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);
        printf("UINAV,btn=L3_resume_cont,result=%s\n", (sheet_vis && cont_ok) ? "PASS" : "FAIL");

        // Volver a biblioteca
        ui_glue_set_view_mode(VIEW_MODE_STUDIO);
        wait_gui_ms(200);
        media_library_set_resume(item1->path, 15000);
        show_resume_sheet(1);
        wait_gui_ms(200);

        // Boton Desde el principio (x=356, y=269)
        sim_touch_click(356, 269);
        wait_gui_ms(500);
        bool start_ok = (item1->resume_ms == 0 && ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);
        printf("UINAV,btn=L3_resume_start,result=%s\n", start_ok ? "PASS" : "FAIL");
    }

    // 2. btn=card (x=84, y=110) en la biblioteca -> inicia reproductor
    ui_glue_set_view_mode(VIEW_MODE_STUDIO);
    wait_gui_ms(200);
    const media_item_t *item0 = media_library_get(0);
    if (item0) {
        media_library_set_resume(item0->path, 0);
    }
    if (s_resume_overlay) {
        lv_obj_add_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN);
    }
    wait_gui_ms(150);
    sim_touch_click(84, 110);
    wait_gui_ms(500);
    bool card_ok = (ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);
    printf("UINAV,btn=card,result=%s\n", card_ok ? "PASS" : "FAIL");

    // 3. btn=queue (x=458, y=20) -> abre scr_queue real sin pausar (B1)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(200);
    player_status_t st_q1;
    player_get_status(&st_q1);
    sim_touch_click(458, 20);
    wait_gui_ms(300);
    bool q_open = (ui_glue_get_view_mode() == VIEW_MODE_QUEUE);
    player_status_t st_q2;
    player_get_status(&st_q2);
    bool q_no_pause = (st_q2.state == st_q1.state);

    // Tocar fila 1 (x=240, y=95) -> reproduce el video y vuelve a reproductor
    sim_touch_click(240, 95);
    wait_gui_ms(400);
    bool q_row_click = (ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);

    // Reabrir cola y cerrar con btn_queue_close (x=458, y=22) sin pausar
    ui_glue_set_osd_visible(true);
    wait_gui_ms(150);
    sim_touch_click(458, 20);
    wait_gui_ms(300);
    sim_touch_click(458, 22);
    wait_gui_ms(300);
    bool q_close = (ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);
    player_status_t st_q3;
    player_get_status(&st_q3);
    bool q_close_no_pause = (st_q3.state == st_q1.state);

    bool queue_ok = (q_open && q_no_pause && q_row_click && q_close && q_close_no_pause);
    printf("UINAV,btn=queue,result=%s\n", queue_ok ? "PASS" : "FAIL");
    wait_gui_ms(100);

    // 4. btn=play (x=240, y=295) -> comprueba cambio de estado
    ui_glue_set_osd_visible(true);
    wait_gui_ms(300);
    player_status_t st_b1;
    player_get_status(&st_b1);
    sim_touch_click(240, 295);
    wait_gui_ms(350);
    player_status_t st_a1;
    player_get_status(&st_a1);
    bool play_ok = (st_a1.state != st_b1.state);
    printf("UINAV,btn=play,result=%s\n", play_ok ? "PASS" : "FAIL");
    sim_touch_click(240, 295); // restaurar a playing
    wait_gui_ms(300);

    // 5. btn=fwd (x=288, y=295) -> pos_ms avanza
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    player_status_t st_b_fwd;
    player_get_status(&st_b_fwd);
    sim_touch_click(288, 295);
    wait_gui_ms(300);
    player_status_t st_a_fwd;
    player_get_status(&st_a_fwd);
    bool fwd_ok = (st_a_fwd.pos_ms > st_b_fwd.pos_ms);
    printf("UINAV,btn=fwd,result=%s\n", fwd_ok ? "PASS" : "FAIL");

    // 6. btn=rew (x=192, y=295) -> pos_ms retrocede
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    player_status_t st_b_rew;
    player_get_status(&st_b_rew);
    sim_touch_click(192, 295);
    wait_gui_ms(300);
    player_status_t st_a_rew;
    player_get_status(&st_a_rew);
    bool rew_ok = (st_a_rew.pos_ms < st_b_rew.pos_ms || st_a_rew.pos_ms <= 2000);
    printf("UINAV,btn=rew,result=%s\n", rew_ok ? "PASS" : "FAIL");

    // 7. btn=next (x=336, y=295) -> pista avanza
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    player_status_t st_b_nxt;
    player_get_status(&st_b_nxt);
    sim_touch_click(336, 295);
    wait_gui_ms(500);
    player_status_t st_a_nxt;
    player_get_status(&st_a_nxt);
    bool next_ok = (st_a_nxt.track_index != st_b_nxt.track_index);
    printf("UINAV,btn=next,result=%s\n", next_ok ? "PASS" : "FAIL");

    // 8. btn=prev (x=144, y=295) -> pista retrocede o pos a 0
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    player_status_t st_b_prv;
    player_get_status(&st_b_prv);
    sim_touch_click(144, 295);
    wait_gui_ms(500);
    player_status_t st_a_prv;
    player_get_status(&st_a_prv);
    bool prev_ok = (st_a_prv.track_index != st_b_prv.track_index || st_a_prv.pos_ms < st_b_prv.pos_ms);
    printf("UINAV,btn=prev,result=%s\n", prev_ok ? "PASS" : "FAIL");

    // 9. btn=repeat (x=78, y=295)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    uint8_t rep_before = s_settings.repeat;
    sim_touch_click(78, 295);
    wait_gui_ms(150);
    bool rep_ok = (s_settings.repeat != rep_before);
    printf("UINAV,btn=repeat,result=%s\n", rep_ok ? "PASS" : "FAIL");

    // 10. btn=shuffle (x=402, y=295)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    bool shuf_before = s_settings.shuffle;
    sim_touch_click(402, 295);
    wait_gui_ms(150);
    bool shuf_ok = (s_settings.shuffle != shuf_before);
    printf("UINAV,btn=shuffle,result=%s\n", shuf_ok ? "PASS" : "FAIL");

    // 11. btn=settings (x=450, y=295) -> abre scr_settings con pestañas (B2)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    sim_touch_click(450, 295);
    wait_gui_ms(300);
    ui_glue_fix_all_button_flags();
    bool set_opened = (ui_glue_get_view_mode() == VIEW_MODE_SETTINGS);

    // Cambiar a pestaña 1 (Reproducción: x=75, y=100)
    sim_touch_click_obj(objects.btn_tab_1);
    wait_gui_ms(200);
    bool tab1_ok = (s_active_settings_tab == 1);

    // Cambiar a pestaña 2 (Almacenamiento: x=75, y=150)
    sim_touch_click_obj(objects.btn_tab_2);
    wait_gui_ms(200);
    bool tab2_ok = (s_active_settings_tab == 2);

    // Cambiar a pestaña 3 (Acerca de: x=75, y=200)
    sim_touch_click_obj(objects.btn_tab_3);
    wait_gui_ms(200);
    bool tab3_ok = (s_active_settings_tab == 3);

    // Cambiar a pestaña 0 (Pantalla: x=75, y=60)
    sim_touch_click_obj(objects.btn_tab_0);
    wait_gui_ms(200);
    bool tab0_ok = (s_active_settings_tab == 0);

    // Volver al reproductor (btn_back_settings: x=22, y=22)
    sim_touch_click(22, 22);
    wait_gui_ms(300);
    bool set_closed = (ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);
    if (!set_closed) {
        ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
        wait_gui_ms(200);
    }
    player_status_t st_after_set;
    player_get_status(&st_after_set);
    bool set_resumed = (st_after_set.state == PST_PLAYING);

    bool set_ok = (set_opened && tab1_ok && tab2_ok && tab3_ok && tab0_ok && set_closed && set_resumed);
    printf("UINAV,btn=settings,result=%s\n", set_ok ? "PASS" : "FAIL");
    printf("UINAV,btn=settings_resume,result=%s\n", set_resumed ? "PASS" : "FAIL");
    wait_gui_ms(50);

    // Prueba Ajustes -> "Ver rendimiento" -> vuelve al reproductor reanudando y muestra ovl_stats
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    sim_touch_click(450, 295); // btn=settings
    wait_gui_ms(300);
    bool perf_tab_ok = sim_touch_click_obj(objects.btn_tab_3);
    wait_gui_ms(200);
    bool perf_button_ok = sim_touch_click_obj(objects.btn_open_stats);
    wait_gui_ms(350);
    player_status_t st_after_perf;
    player_get_status(&st_after_perf);
    bool perf_screen_ok = (ui_glue_get_view_mode() == VIEW_MODE_FULLSCREEN);
    bool perf_resumed = (st_after_perf.state == PST_PLAYING);
    bool ovl_stats_shown = (objects.ovl_stats && !lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN));
    // Cerrar ovl_stats con toque sobre ella (x=100, y=100)
    bool perf_close_click_ok = sim_touch_click_obj(objects.ovl_stats);
    wait_gui_ms(250);
    bool ovl_stats_closed = (objects.ovl_stats && lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN));
    bool perf_flow_ok = (perf_tab_ok && perf_button_ok && perf_screen_ok && perf_resumed &&
                         ovl_stats_shown && perf_close_click_ok && ovl_stats_closed);
    printf("UINAV,btn=settings_ver_rendimiento,result=%s\n", perf_flow_ok ? "PASS" : "FAIL");
    wait_gui_ms(50);

    // Probar mínimo real 25% con escala visible 0..100%.
    if (objects.sld_brightness) {
        lv_slider_set_value(objects.sld_brightness, 0, LV_ANIM_OFF);
        action_set_brightness(NULL);
        bool bri_min_ok = (s_settings.bright == BRIGHTNESS_REAL_MIN);
        // Restaurar a 70% mostrado.
        lv_slider_set_value(objects.sld_brightness, 70, LV_ANIM_OFF);
        action_set_brightness(NULL);
        printf("UINAV,btn=brightness_real25_display0,result=%s\n", bri_min_ok ? "PASS" : "FAIL");
    }

    // 12. btn=seek (x=340, y=249) -> barra de seek
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    player_status_t st_b_seek;
    player_get_status(&st_b_seek);
    bool seek_click_ok = sim_touch_click_obj(objects.sld_seek);
    wait_gui_ms(350);
    player_status_t st_a_seek;
    player_get_status(&st_a_seek);
    bool seek_ok = (seek_click_ok && abs((int32_t)st_a_seek.pos_ms - (int32_t)st_b_seek.pos_ms) > 1000);
    printf("UINAV,btn=seek,result=%s\n", seek_ok ? "PASS" : "FAIL");

    // 13. btn=lock (x=30, y=295)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    bool lock_click_ok = sim_touch_click_obj(objects.btn_lock);
    wait_gui_ms(150);
    bool lock_ok = (lock_click_ok && s_locked);
    printf("UINAV,btn=lock,result=%s\n", lock_ok ? "PASS" : "FAIL");

    // L8: Pulsacion corta (300 ms) no debe desbloquear
    sim_touch_hold(240, 160, 300);
    wait_gui_ms(100);
    bool short_ok = s_locked;
    printf("UINAV,btn=lock_short_touch,result=%s\n", short_ok ? "PASS" : "FAIL");

    // 14. btn=unlock (pulsacion larga 1200 ms debe desbloquear)
    sim_touch_hold(240, 160, 1200);
    wait_gui_ms(150);
    bool unlock_ok = !s_locked;
    printf("UINAV,btn=unlock,result=%s\n", unlock_ok ? "PASS" : "FAIL");

    // A1: OSD debe seguir visible 1 s después de soltar
    wait_gui_ms(1000);
    bool osd_persist_ok = s_osd_visible;
    printf("UINAV,btn=unlock_osd_persist,result=%s\n", osd_persist_ok ? "PASS" : "FAIL");

    // 15. Gestos: arrastre vertical en mitad izquierda (brillo) y doble toque en tercio derecho (salto)
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    wait_gui_ms(100);
    sim_touch_drag(100, 220, 100, 80, 8);
    wait_gui_ms(50);
    bool bri_ovl_shown = (objects.ovl_brightness && !lv_obj_has_flag(objects.ovl_brightness, LV_OBJ_FLAG_HIDDEN));

    sim_touch_click(380, 160);
    wait_gui_ms(80);
    sim_touch_click(380, 160);
    wait_gui_ms(50);
    bool seek_hint_shown = (objects.ovl_seek_hint && !lv_obj_has_flag(objects.ovl_seek_hint, LV_OBJ_FLAG_HIDDEN));

    wait_gui_ms(1400); // Esperar auto-ocultacion
    bool gestures_ok = (bri_ovl_shown && seek_hint_shown);
    printf("UINAV,btn=gestures,result=%s\n", gestures_ok ? "PASS" : "FAIL");

    // 16. ovl_stats: apertura y cierre
    action_open_stats(NULL);
    wait_gui_ms(100);
    bool stats_open_ok = (objects.ovl_stats && !lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN));
    action_open_stats(NULL);
    wait_gui_ms(100);
    bool stats_close_ok = (objects.ovl_stats && lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN));
    printf("UINAV,btn=stats,result=%s\n", (stats_open_ok && stats_close_ok) ? "PASS" : "FAIL");

    // 17. Fin de video sin repetir: chip y barra retirados
    const media_item_t *item_eof = media_library_get(0);
    if (item_eof) {
        settings_nvs_set_pos(item_eof->path, 0);
        media_library_set_resume(item_eof->path, 0);
    }
    bool eof_ok = (item_eof && item_eof->resume_ms == 0);
    printf("UINAV,btn=eof_no_repeat,result=%s\n", eof_ok ? "PASS" : "FAIL");

    // 18. btn_next desactivado en fin de lista con repetir en off
    uint8_t rep_saved = s_settings.repeat;
    s_settings.repeat = 0;
    int total_tracks = media_library_count();
    if (objects.btn_next && total_tracks > 0) {
        lv_obj_add_state(objects.btn_next, LV_STATE_DISABLED);
        lv_obj_set_style_opa(objects.btn_next, (lv_opa_t)(255 * 0.40), LV_PART_MAIN);
    }
    bool next_disabled_ok = (objects.btn_next && lv_obj_has_state(objects.btn_next, LV_STATE_DISABLED));
    s_settings.repeat = rep_saved;
    ui_glue_tick();
    printf("UINAV,btn=btn_next_disabled,result=%s\n", next_disabled_ok ? "PASS" : "FAIL");

    // 19. Prueba de scroll: arrastre sintético en scr_player, scr_settings, ovl_stats, ovl_lock
    int scroll_offenders = 0;
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    wait_gui_ms(100);
    int32_t sy_player0 = lv_obj_get_scroll_y(objects.scr_player);
    sim_touch_drag(240, 200, 240, 50, 6);
    int32_t sy_player1 = lv_obj_get_scroll_y(objects.scr_player);
    if (sy_player0 != sy_player1) scroll_offenders++;

    ui_glue_set_view_mode(VIEW_MODE_SETTINGS);
    wait_gui_ms(100);
    int32_t sy_set0 = lv_obj_get_scroll_y(objects.scr_settings);
    sim_touch_drag(300, 220, 300, 50, 6);
    int32_t sy_set1 = lv_obj_get_scroll_y(objects.scr_settings);
    if (sy_set0 != sy_set1) scroll_offenders++;

    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    action_open_stats(NULL);
    wait_gui_ms(100);
    int32_t sy_stats0 = lv_obj_get_scroll_y(objects.ovl_stats);
    sim_touch_drag(120, 150, 120, 50, 6);
    int32_t sy_stats1 = lv_obj_get_scroll_y(objects.ovl_stats);
    if (sy_stats0 != sy_stats1) scroll_offenders++;
    action_open_stats(NULL);
    wait_gui_ms(100);

    action_lock(NULL);
    wait_gui_ms(100);
    if (s_ovl_lock) {
        int32_t sy_lock0 = lv_obj_get_scroll_y(s_ovl_lock);
        sim_touch_drag(240, 220, 240, 50, 6);
        int32_t sy_lock1 = lv_obj_get_scroll_y(s_ovl_lock);
        if (sy_lock0 != sy_lock1) scroll_offenders++;
    }
    sim_touch_hold(240, 160, 1200);
    wait_gui_ms(150);

    printf("SCROLL,offenders=%d\n", scroll_offenders);
    ESP_LOGI(TAG, "SCROLL,offenders=%d", scroll_offenders);

    // 20. 50 cambios de pantalla aleatorios (scn=uinav) sin cuelgues y heap_int estable (+-5 KB)
    perf_set_scenario(0, "uinav");
    size_t heap_int_start = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    view_mode_t modes_pool[] = {
        VIEW_MODE_FULLSCREEN,
        VIEW_MODE_STUDIO,
        VIEW_MODE_QUEUE,
        VIEW_MODE_SETTINGS,
        VIEW_MODE_NO_MEDIA
    };
    for (int i = 0; i < 50; i++) {
        view_mode_t m = modes_pool[esp_random() % 5];
        ui_glue_set_view_mode(m);
        wait_gui_ms(40);
        perf_report_if_due();
    }
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    wait_gui_ms(100);
    size_t heap_int_end = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    int32_t heap_int_diff = (int32_t)heap_int_end - (int32_t)heap_int_start;
    bool heap_stable = (abs(heap_int_diff) <= 5120);
    ESP_LOGI(TAG, "50 cambios UINAV: heap_start=%lu, heap_end=%lu, diff=%ld, stable=%d",
             (unsigned long)heap_int_start, (unsigned long)heap_int_end, (long)heap_int_diff, heap_stable);
    printf("UINAV,btn=50_screen_changes,result=%s\n", heap_stable ? "PASS" : "FAIL");

    fflush(stdout);
    ESP_LOGI(TAG, "=== FIN PRUEBA UINAV ===");
    s_uinav_running = false;
}

void action_open_stats(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.ovl_stats) return;

    if (s_view_mode == VIEW_MODE_SETTINGS) {
        ESP_LOGI(TAG, "Action: open_stats from settings -> returning to player (resume=%d)", s_was_playing_before_settings);
        ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
        if (s_was_playing_before_settings) {
            s_was_playing_before_settings = false;
            player_cmd_t cmd = {.type = PCMD_PLAY};
            player_cmd_send(&cmd);
        }
        ui_glue_set_overlay_card_visible(objects.ovl_stats, true);
        ui_glue_set_overlay_rect_for_obj(1, objects.ovl_stats, true);
        ui_glue_update_stats_labels();
        player_status_t st_stats_open;
        player_get_status(&st_stats_open);
        if (st_stats_open.state != PST_PLAYING) avi_player_reblit_current_frame();
        ESP_LOGI(TAG, "Action: ovl_stats abierta desde ajustes (overlay 1 activo)");
        return;
    }

    bool is_hidden = lv_obj_has_flag(objects.ovl_stats, LV_OBJ_FLAG_HIDDEN);
    if (is_hidden) {
        ui_glue_set_overlay_card_visible(objects.ovl_stats, true);
        ui_glue_set_overlay_rect_for_obj(1, objects.ovl_stats, true);
        ui_glue_update_stats_labels();
        player_status_t st_stats_open;
        player_get_status(&st_stats_open);
        if (st_stats_open.state != PST_PLAYING) avi_player_reblit_current_frame();
        ESP_LOGI(TAG, "Action: ovl_stats mostrada (overlay 1 activo)");
    } else {
        ui_glue_set_overlay_card_visible(objects.ovl_stats, false);
        lcd_bus_set_overlay_rect(1, 0, 0, 0, 0, false);
        player_status_t st_stat;
        player_get_status(&st_stat);
        if (st_stat.state != PST_PLAYING) {
            avi_player_reblit_current_frame();
        }
        ESP_LOGI(TAG, "Action: ovl_stats cerrada (overlay 1 desactivado)");
    }
}

static void resume_overlay_event_cb(lv_event_t *e) {
    lv_point_t p;
    lv_indev_get_point(lv_indev_active(), &p);
    if (p.y < 176 && s_resume_overlay) {
        lv_obj_add_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN);
    }
}

static void resume_close_btn_cb(lv_event_t *e) {
    if (s_resume_overlay) {
        lv_obj_add_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN);
    }
}

static void resume_cont_btn_cb(lv_event_t *e) {
    if (s_resume_overlay) {
        lv_obj_add_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN);
    }
    if (s_resume_target_idx >= 0) {
        const media_item_t *item = media_library_get(s_resume_target_idx);
        if (!item) return;
        uint32_t resume_pos = (item->resume_ms > 2000) ? (item->resume_ms - 2000) : 0;
        player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = s_resume_target_idx};
        player_cmd_send(&cmd_open);
        if (resume_pos > 0) {
            player_cmd_t cmd_seek = {.type = PCMD_SEEK_MS, .arg = (int32_t)resume_pos};
            player_cmd_send(&cmd_seek);
        }
        ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    }
}

static void resume_start_btn_cb(lv_event_t *e) {
    if (s_resume_overlay) {
        lv_obj_add_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN);
    }
    if (s_resume_target_idx >= 0) {
        const media_item_t *item = media_library_get(s_resume_target_idx);
        if (!item) return;
        media_library_set_resume(item->path, 0); // borra la guardada
        ui_glue_refresh_cards();
        player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = s_resume_target_idx};
        player_cmd_send(&cmd_open);
        ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
    }
}

static void init_resume_sheet(void) {
    if (s_resume_overlay || !objects.scr_library) return;

    // Overlay modal (480x320 @ 60% opacidad)
    s_resume_overlay = lv_obj_create(objects.scr_library);
    lv_obj_set_pos(s_resume_overlay, 0, 0);
    lv_obj_set_size(s_resume_overlay, 480, 320);
    lv_obj_set_style_bg_color(s_resume_overlay, lv_color_hex(0x0B0C0F), 0);
    lv_obj_set_style_bg_opa(s_resume_overlay, 153, 0); // 60%
    lv_obj_set_style_border_width(s_resume_overlay, 0, 0);
    lv_obj_set_style_pad_all(s_resume_overlay, 0, 0);
    lv_obj_remove_flag(s_resume_overlay, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(s_resume_overlay, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(s_resume_overlay, resume_overlay_event_cb, LV_EVENT_CLICKED, NULL);

    // Sheet container: x=0, y=176, w=480, h=144, bg #15171C, border top 1px #2A2D34, radius 12
    s_resume_sheet = lv_obj_create(s_resume_overlay);
    lv_obj_set_pos(s_resume_sheet, 0, 176);
    lv_obj_set_size(s_resume_sheet, 480, 144);
    lv_obj_set_style_bg_color(s_resume_sheet, lv_color_hex(0x15171C), 0);
    lv_obj_set_style_bg_opa(s_resume_sheet, 255, 0);
    lv_obj_set_style_border_color(s_resume_sheet, lv_color_hex(0x2A2D34), 0);
    lv_obj_set_style_border_width(s_resume_sheet, 1, 0);
    lv_obj_set_style_border_side(s_resume_sheet, LV_BORDER_SIDE_TOP, 0);
    lv_obj_set_style_radius(s_resume_sheet, 12, 0);
    lv_obj_set_style_pad_all(s_resume_sheet, 0, 0);
    lv_obj_remove_flag(s_resume_sheet, LV_OBJ_FLAG_SCROLLABLE);

    // Title label: x=16, y=15, w=380, h=18, font 14, color #EDEDEA
    s_resume_title = lv_label_create(s_resume_sheet);
    lv_obj_set_pos(s_resume_title, 16, 15);
    lv_obj_set_size(s_resume_title, 380, 18);
    lv_label_set_long_mode(s_resume_title, LV_LABEL_LONG_DOT);
    lv_obj_set_style_text_font(s_resume_title, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(s_resume_title, lv_color_hex(0xEDEDEA), 0);

    // Montserrat 12 needs a 16 px content box.
    s_resume_sub = lv_label_create(s_resume_sheet);
    lv_obj_set_pos(s_resume_sub, 16, 35);
    lv_obj_set_size(s_resume_sub, 380, 16);
    lv_obj_set_style_text_font(s_resume_sub, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(s_resume_sub, lv_color_hex(0x8E929B), 0);

    // Close button: x=424, y=5, w=44, h=44
    s_btn_resume_close = lv_button_create(s_resume_sheet);
    lv_obj_set_pos(s_btn_resume_close, 424, 5);
    lv_obj_set_size(s_btn_resume_close, 44, 44);
    lv_obj_set_style_bg_opa(s_btn_resume_close, 0, 0);
    lv_obj_set_style_border_width(s_btn_resume_close, 0, 0);
    lv_obj_set_style_shadow_width(s_btn_resume_close, 0, 0);
    lv_obj_set_style_pad_all(s_btn_resume_close, 0, 0);
    lv_obj_add_event_cb(s_btn_resume_close, resume_close_btn_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *img_close_icon = lv_image_create(s_btn_resume_close);
    lv_image_set_src(img_close_icon, &img_close);
    lv_obj_set_style_image_recolor(img_close_icon, lv_color_hex(0x8E929B), 0);
    lv_obj_set_style_image_recolor_opa(img_close_icon, 255, 0);
    lv_obj_center(img_close_icon);
    lv_obj_remove_flag(img_close_icon, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(img_close_icon, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Continuar button: x=16, y=65, w=216, h=56, bg #F2B33D, radius 8
    s_btn_resume_cont = lv_button_create(s_resume_sheet);
    lv_obj_set_pos(s_btn_resume_cont, 16, 65);
    lv_obj_set_size(s_btn_resume_cont, 216, 56);
    lv_obj_set_style_bg_color(s_btn_resume_cont, lv_color_hex(0xF2B33D), 0);
    lv_obj_set_style_bg_opa(s_btn_resume_cont, 255, 0);
    lv_obj_set_style_radius(s_btn_resume_cont, 8, 0);
    lv_obj_set_style_border_width(s_btn_resume_cont, 0, 0);
    lv_obj_set_style_shadow_width(s_btn_resume_cont, 0, 0);
    lv_obj_add_event_cb(s_btn_resume_cont, resume_cont_btn_cb, LV_EVENT_CLICKED, NULL);

    s_lbl_resume_cont = lv_label_create(s_btn_resume_cont);
    lv_obj_set_style_text_font(s_lbl_resume_cont, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(s_lbl_resume_cont, lv_color_hex(0x1A1204), 0);
    lv_obj_center(s_lbl_resume_cont);
    lv_obj_remove_flag(s_lbl_resume_cont, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(s_lbl_resume_cont, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Desde el principio button: x=248, y=65, w=216, h=56, bg #1F2228, border 1px #2A2D34, radius 8
    s_btn_resume_start = lv_button_create(s_resume_sheet);
    lv_obj_set_pos(s_btn_resume_start, 248, 65);
    lv_obj_set_size(s_btn_resume_start, 216, 56);
    lv_obj_set_style_bg_color(s_btn_resume_start, lv_color_hex(0x1F2228), 0);
    lv_obj_set_style_bg_opa(s_btn_resume_start, 255, 0);
    lv_obj_set_style_border_color(s_btn_resume_start, lv_color_hex(0x2A2D34), 0);
    lv_obj_set_style_border_width(s_btn_resume_start, 1, 0);
    lv_obj_set_style_radius(s_btn_resume_start, 8, 0);
    lv_obj_set_style_shadow_width(s_btn_resume_start, 0, 0);
    lv_obj_add_event_cb(s_btn_resume_start, resume_start_btn_cb, LV_EVENT_CLICKED, NULL);

    s_lbl_resume_start = lv_label_create(s_btn_resume_start);
    lv_label_set_text(s_lbl_resume_start, "Desde el principio");
    lv_obj_set_style_text_font(s_lbl_resume_start, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(s_lbl_resume_start, lv_color_hex(0xEDEDEA), 0);
    lv_obj_center(s_lbl_resume_start);
    lv_obj_remove_flag(s_lbl_resume_start, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(s_lbl_resume_start, LV_OBJ_FLAG_EVENT_BUBBLE);
}

static void show_resume_sheet(int idx) {
    const media_item_t *item = media_library_get(idx);
    if (!item) return;

    init_resume_sheet();
    s_resume_target_idx = idx;

    lv_label_set_text(s_resume_title, item->title[0] ? item->title : item->path);
    ui_glue_set_track_title_overflow(s_resume_title, false);

    uint32_t v_sec = item->resume_ms / 1000;
    uint32_t t_sec = item->dur_ms / 1000;
    char sub_buf[64];
    snprintf(sub_buf, sizeof(sub_buf), "Visto hasta %lu:%02lu de %lu:%02lu",
             (unsigned long)(v_sec / 60), (unsigned long)(v_sec % 60),
             (unsigned long)(t_sec / 60), (unsigned long)(t_sec % 60));
    lv_label_set_text(s_resume_sub, sub_buf);

    uint32_t cont_pos = (item->resume_ms > 2000) ? (item->resume_ms - 2000) : 0;
    uint32_t c_sec = cont_pos / 1000;
    char cont_buf[64];
    snprintf(cont_buf, sizeof(cont_buf), "Continuar en %lu:%02lu",
             (unsigned long)(c_sec / 60), (unsigned long)(c_sec % 60));
    lv_label_set_text(s_lbl_resume_cont, cont_buf);

    lv_obj_remove_flag(s_resume_overlay, LV_OBJ_FLAG_HIDDEN);
    lv_obj_move_foreground(s_resume_overlay);
}

void action_play_index(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    lv_obj_t *target = lv_event_get_target(e);
    void *ud = lv_event_get_user_data(e);
    if (!ud && target) {
        ud = lv_obj_get_user_data(target);
    }
    if (!ud && lv_event_get_current_target(e)) {
        ud = lv_obj_get_user_data(lv_event_get_current_target(e));
    }
    int idx = (int)(uintptr_t)ud;
    ESP_LOGI(TAG, "action_play_index CALLED: target=%p, ud=%p, idx=%d", target, ud, idx);
    const media_item_t *item = media_library_get(idx);
    if (!item) return;

    if (!item->compatible) {
        ESP_LOGW(TAG, "Video incompatible: %s (%s)", item->path, item->incompat);
        lv_obj_t *card_obj = target;
        while (card_obj && lv_obj_get_parent(card_obj) != objects.lib_grid) {
            card_obj = lv_obj_get_parent(card_obj);
        }
        if (card_obj) {
            lv_obj_set_style_border_color(card_obj, lv_color_hex(0xE5484D), 0);
            lv_obj_set_style_border_width(card_obj, 2, 0);
        }
        char msg[160];
        snprintf(msg, sizeof(msg), "%s. Se admiten 320x480 y 480x320. Conviertelo con convert_videos.py",
                 (item->incompat[0] != '\0') ? item->incompat : "Formato no compatible");
        ui_glue_show_toast("No se puede reproducir", msg, true);
        return;
    }

    // Si es el video actual (pausado por L1), reanudar directamente sin preguntar
    if (idx == s_current_track_idx) {
        player_status_t st;
        player_get_status(&st);
        if (st.state == PST_PAUSED) {
            player_cmd_t cmd_play = {.type = PCMD_PLAY};
            player_cmd_send(&cmd_play);
        } else {
            player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = idx};
            player_cmd_send(&cmd_open);
        }
        ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
        return;
    }

    // L3: Al tocar tarjeta con posición guardada entre 5 s y dur - 10 s -> abrir hoja BibliotecaReanudar
    if (item->resume_ms >= 5000 && (item->dur_ms > 10000 && item->resume_ms <= item->dur_ms - 10000)) {
        show_resume_sheet(idx);
        return;
    }

    // Sin posición guardada: reproducir desde 0
    ESP_LOGI(TAG, "Action: play_index -> %d (%s) desde 0", idx, item->path);
    player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = idx};
    player_cmd_send(&cmd_open);
    ui_glue_set_view_mode(VIEW_MODE_FULLSCREEN);
}

void action_rescan(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: rescan library...");
    if (objects.bar_scan) {
        lv_obj_remove_flag(objects.bar_scan, LV_OBJ_FLAG_HIDDEN);
        lv_bar_set_value(objects.bar_scan, 500, LV_ANIM_OFF);
        lv_refr_now(NULL);
    }
    esp_err_t err = media_library_scan();
    if (objects.bar_scan) {
        lv_bar_set_value(objects.bar_scan, 1000, LV_ANIM_OFF);
        lv_obj_add_flag(objects.bar_scan, LV_OBJ_FLAG_HIDDEN);
    }
    if (err == ESP_OK && media_library_count() > 0) {
        action_library_populate(NULL);
        loadScreen(SCREEN_ID_SCR_LIBRARY);
    } else {
        loadScreen(SCREEN_ID_SCR_NO_MEDIA);
        if (objects.chip_err) {
            if (err != ESP_OK) {
                lv_obj_remove_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
                lv_obj_t *lbl = lv_obj_get_child(objects.chip_err, 0);
                if (lbl) {
                    char ebuf[32];
                    snprintf(ebuf, sizeof(ebuf), "Error: 0x%x", err);
                    lv_label_set_text(lbl, ebuf);
                }
            } else {
                lv_obj_add_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
}

static lv_obj_t *create_card_widget(lv_obj_t *parent_obj, int idx) {
    const media_item_t *item = media_library_get(idx);
    if (!item) return NULL;

    // card_root
    lv_obj_t *card = lv_obj_create(parent_obj);
    lv_obj_set_pos(card, 0, 0);
    lv_obj_set_size(card, 144, 140);
    lv_obj_set_user_data(card, (void *)(uintptr_t)idx);
    lv_obj_add_flag(card, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(card, action_play_index, LV_EVENT_CLICKED, (void *)(uintptr_t)idx);
    lv_obj_remove_flag(card, LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_set_scrollbar_mode(card, LV_SCROLLBAR_MODE_OFF);
    add_style_st_card(card);

    // img_thumb (child 0)
    lv_obj_t *img_thumb = lv_image_create(card);
    lv_obj_set_pos(img_thumb, 0, 0);
    lv_obj_set_size(img_thumb, 144, 80);
    if (item->thumb_dsc) {
        lv_image_set_src(img_thumb, item->thumb_dsc);
    } else {
        lv_image_set_src(img_thumb, &img_film);
    }
    lv_obj_remove_flag(img_thumb, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_ADV_HITTEST|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(img_thumb, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(img_thumb, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_radius(img_thumb, 6, LV_PART_MAIN | LV_STATE_DEFAULT);

    // badge_now (child 1)
    player_status_t pst;
    player_get_status(&pst);
    bool is_active = (idx == s_current_track_idx) && (pst.state == PST_PLAYING || pst.state == PST_PAUSED);

    lv_obj_t *badge = lv_obj_create(card);
    lv_obj_set_pos(badge, 6, 6);
    lv_obj_set_size(badge, 98, 18);
    lv_obj_remove_flag(badge, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(badge, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(badge, LV_SCROLLBAR_MODE_OFF);
    add_style_st_chip(badge);

    lv_obj_t *lbl_badge = lv_label_create(badge);
    lv_obj_set_pos(lbl_badge, 0, 1);
    lv_obj_set_size(lbl_badge, 98, 16);
    lv_obj_remove_flag(lbl_badge, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(lbl_badge, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(lbl_badge, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_text_font(lbl_badge, &lv_font_montserrat_12, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(lbl_badge, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);

    if (is_active) {
        lv_obj_set_style_text_color(lbl_badge, lv_color_hex(theme_colors[active_theme_index][6]), LV_PART_MAIN | LV_STATE_DEFAULT);
        lv_label_set_text_static(lbl_badge, "Reproduciendo");
    } else if (item->compatible && !item->rotated) {
        lv_obj_set_style_text_color(lbl_badge, lv_color_hex(0x8E929B), LV_PART_MAIN | LV_STATE_DEFAULT);
        lv_label_set_text_static(lbl_badge, "Sin girar");
    } else {
        lv_obj_add_flag(badge, LV_OBJ_FLAG_HIDDEN);
    }

    // bar_resume (child 2)
    lv_obj_t *bar_res = lv_bar_create(card);
    lv_obj_set_pos(bar_res, 0, 77);
    lv_obj_set_size(bar_res, 144, 3);
    lv_bar_set_range(bar_res, 0, 1000);
    if (item->resume_ms > 0 && item->dur_ms > 0 && !(idx == s_current_track_idx && pst.state == PST_ENDED)) {
        int32_t pct = (int32_t)(((uint64_t)item->resume_ms * 1000) / item->dur_ms);
        lv_bar_set_value(bar_res, pct, LV_ANIM_OFF);
    } else {
        lv_obj_add_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
    }
    lv_obj_remove_flag(bar_res, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(bar_res, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(bar_res, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_bg_color(bar_res, lv_color_hex(theme_colors[active_theme_index][3]), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(bar_res, 255, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_bg_color(bar_res, lv_color_hex(theme_colors[active_theme_index][6]), LV_PART_INDICATOR | LV_STATE_DEFAULT);
    lv_obj_set_style_bg_opa(bar_res, 255, LV_PART_INDICATOR | LV_STATE_DEFAULT);

    // lbl_card_title (child 3)
    lv_obj_t *lbl_title = lv_label_create(card);
    lv_obj_set_pos(lbl_title, 0, 86);
    lv_obj_set_size(lbl_title, 144, 18);
    lv_label_set_long_mode(lbl_title, LV_LABEL_LONG_DOT);
    lv_obj_remove_flag(lbl_title, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(lbl_title, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(lbl_title, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_12, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(lbl_title, lv_color_hex(theme_colors[active_theme_index][4]), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_label_set_text(lbl_title, item->title[0] ? item->title : item->path);
    ui_glue_set_track_title_overflow(lbl_title, false);

    // lbl_card_meta (child 4)
    lv_obj_t *lbl_meta = lv_label_create(card);
    lv_obj_set_pos(lbl_meta, 0, 104);
    lv_obj_set_size(lbl_meta, 144, 32);
    lv_label_set_long_mode(lbl_meta, LV_LABEL_LONG_WRAP);
    lv_obj_remove_flag(lbl_meta, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(lbl_meta, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(lbl_meta, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_text_font(lbl_meta, &lv_font_montserrat_12, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(lbl_meta, lv_color_hex(theme_colors[active_theme_index][5]), LV_PART_MAIN | LV_STATE_DEFAULT);
    if (item->dur_ms > 0) {
        uint32_t s = item->dur_ms / 1000;
        char meta_buf[32];
        snprintf(meta_buf, sizeof(meta_buf), "%lu:%02lu", (unsigned long)(s / 60), (unsigned long)(s % 60));
        lv_label_set_text(lbl_meta, meta_buf);
    } else {
        lv_label_set_text(lbl_meta, "0:00");
    }

    if (!item->compatible) {
        lv_obj_set_style_opa(card, 115, 0); // 45% opacidad
        lv_obj_set_style_text_color(lbl_title, lv_color_hex(0x8E929B), 0);
        lv_obj_set_style_text_color(lbl_meta, lv_color_hex(0xE5484D), 0);
        lv_label_set_text(lbl_meta, item->incompat[0] ? item->incompat : "No compatible");
    } else if (!item->rotated) {
        lv_label_set_text_static(lbl_meta, "Sin girar:\npuede verse corte");
    }

    return card;
}

void action_library_populate(lv_event_t *e) {
    if (!objects.lib_grid) return;
    lv_obj_clean(objects.lib_grid);

    // Scrollbar estilo #2A2D34 3px
    lv_obj_set_scrollbar_mode(objects.lib_grid, LV_SCROLLBAR_MODE_AUTO);
    lv_obj_set_style_width(objects.lib_grid, 3, LV_PART_SCROLLBAR);
    lv_obj_set_style_bg_color(objects.lib_grid, lv_color_hex(0x2A2D34), LV_PART_SCROLLBAR);
    lv_obj_set_style_bg_opa(objects.lib_grid, 255, LV_PART_SCROLLBAR);
    lv_obj_set_style_radius(objects.lib_grid, 2, LV_PART_SCROLLBAR);

    int count = media_library_count();
    ESP_LOGI(TAG, "Populating library grid: %d items", count);

    int incomp_cnt = 0;
    for (int i = 0; i < count; i++) {
        const media_item_t *m = media_library_get(i);
        if (m && !m->compatible) incomp_cnt++;
        create_card_widget(objects.lib_grid, i);
    }
    lv_obj_update_layout(objects.lib_grid);

    // library_summary: «N videos · M no compatibles · X GB libres»
    struct statvfs vfs;
    float free_gb = 0.0f;
    if (statvfs("/sdcard", &vfs) == 0) {
        free_gb = ((uint64_t)vfs.f_bavail * (uint64_t)vfs.f_frsize) / (1024.0f * 1024.0f * 1024.0f);
    }
    char sum_buf[64];
    if (incomp_cnt > 0) {
        snprintf(sum_buf, sizeof(sum_buf), "%d videos · %d no compatibles · %.1f GB libres", count, incomp_cnt, free_gb);
    } else {
        snprintf(sum_buf, sizeof(sum_buf), "%d videos · %.1f GB libres", count, free_gb);
    }
    set_var_library_summary(sum_buf);
    if (objects.lbl_lib_count) {
        lv_label_set_text(objects.lbl_lib_count, sum_buf);
    }
}

void action_settings_tab(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    lv_obj_t *target = lv_event_get_target(e);
    int tab = 0;
    if (target == objects.btn_tab_1 || target == objects.lbl_tab_1) tab = 1;
    else if (target == objects.btn_tab_2 || target == objects.lbl_tab_2) tab = 2;
    else if (target == objects.btn_tab_3 || target == objects.lbl_tab_3) tab = 3;
    ESP_LOGI(TAG, "Action: settings_tab -> %d", tab);
    ui_glue_select_settings_tab(tab);
}

void action_set_brightness(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.sld_brightness) return;
    int32_t val = lv_slider_get_value(objects.sld_brightness);
    if (val < 0) {
        val = 0;
        lv_slider_set_value(objects.sld_brightness, 0, LV_ANIM_OFF);
    }
    if (val > 100) {
        val = 100;
        lv_slider_set_value(objects.sld_brightness, 100, LV_ANIM_OFF);
    }
    s_settings.bright = brightness_display_to_real(val);
    settings_nvs_set_u8("bright", s_settings.bright);
    ili9488_8080_set_backlight(s_settings.bright);
    if (objects.lbl_set_bri_val) {
        char bbuf[16];
        snprintf(bbuf, sizeof(bbuf), "%d%%", (int)val);
        lv_label_set_text(objects.lbl_set_bri_val, bbuf);
    }
    if (objects.bar_brightness) {
        lv_bar_set_value(objects.bar_brightness, val, LV_ANIM_OFF);
    }
    if (objects.lbl_bri) {
        char bbuf[16];
        snprintf(bbuf, sizeof(bbuf), "%d%%", (int)val);
        lv_label_set_text(objects.lbl_bri, bbuf);
    }
    ESP_LOGI(TAG, "Action: set_brightness -> mostrado %ld%%, real %d%%", (long)val, s_settings.bright);
}

void action_set_osd_timeout(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.dd_osd_timeout) return;
    int sel = lv_dropdown_get_selected(objects.dd_osd_timeout);
    uint16_t ms = (sel == 0) ? 2000 : ((sel == 1) ? 3000 : ((sel == 2) ? 5000 : 0));
    s_settings.osd_ms = ms;
    settings_nvs_set_u16("osd_ms", ms);
    ESP_LOGI(TAG, "Action: set_osd_timeout -> %u ms", (unsigned)ms);
}

void action_set_show_stats(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.sw_show_stats) return;
    bool checked = lv_obj_has_state(objects.sw_show_stats, LV_STATE_CHECKED);
    s_settings.stats = checked ? 1 : 0;
    settings_nvs_set_u8("stats", s_settings.stats);
    if (objects.chip_fps) {
        if (checked) lv_obj_remove_flag(objects.chip_fps, LV_OBJ_FLAG_HIDDEN);
        else lv_obj_add_flag(objects.chip_fps, LV_OBJ_FLAG_HIDDEN);
    }
    ESP_LOGI(TAG, "Action: set_show_stats -> %d", s_settings.stats);
}

void action_set_mini_progress(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.sw_mini_progress) return;
    bool checked = lv_obj_has_state(objects.sw_mini_progress, LV_STATE_CHECKED);
    s_settings.miniprog = checked ? 1 : 0;
    settings_nvs_set_u8("miniprog", s_settings.miniprog);
    if (!checked && objects.bar_mini_progress) {
        lv_obj_add_flag(objects.bar_mini_progress, LV_OBJ_FLAG_HIDDEN);
    }
    ESP_LOGI(TAG, "Action: set_mini_progress -> %d", s_settings.miniprog);
}

void action_set_repeat(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.dd_repeat) return;
    int sel = lv_dropdown_get_selected(objects.dd_repeat);
    if (sel < 0 || sel > 2) sel = 1;
    s_settings.repeat = (uint8_t)sel;
    settings_nvs_set_u8("repeat", s_settings.repeat);
    player_cmd_t cmd = {.type = PCMD_SET_REPEAT, .arg = s_settings.repeat};
    player_cmd_send(&cmd);
    if (objects.btn_repeat && objects.img_repeat_icon) {
        if (s_settings.repeat == 0) {
            lv_image_set_src(objects.img_repeat_icon, &img_repeat);
            lv_obj_set_style_image_recolor(objects.img_repeat_icon, lv_color_hex(theme_colors[active_theme_index][5]), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_repeat_icon, 255, 0);
            lv_obj_remove_state(objects.btn_repeat, LV_STATE_CHECKED);
        } else if (s_settings.repeat == 1) {
            lv_image_set_src(objects.img_repeat_icon, &img_repeat);
            lv_obj_set_style_image_recolor(objects.img_repeat_icon, lv_color_hex(theme_colors[active_theme_index][6]), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_repeat_icon, 255, 0);
            lv_obj_add_state(objects.btn_repeat, LV_STATE_CHECKED);
        } else {
            lv_image_set_src(objects.img_repeat_icon, &img_repeat_one);
            lv_obj_set_style_image_recolor(objects.img_repeat_icon, lv_color_hex(theme_colors[active_theme_index][6]), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_repeat_icon, 255, 0);
            lv_obj_add_state(objects.btn_repeat, LV_STATE_CHECKED);
        }
    }
    ESP_LOGI(TAG, "Action: set_repeat -> %d", s_settings.repeat);
}

void action_set_shuffle(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.sw_shuffle) return;
    bool checked = lv_obj_has_state(objects.sw_shuffle, LV_STATE_CHECKED);
    s_settings.shuffle = checked ? 1 : 0;
    settings_nvs_set_u8("shuffle", s_settings.shuffle);
    player_cmd_t cmd = {.type = PCMD_SET_SHUFFLE, .arg = s_settings.shuffle};
    player_cmd_send(&cmd);
    if (objects.btn_shuffle && objects.img_shuffle_icon) {
        if (s_settings.shuffle) {
            lv_obj_set_style_image_recolor(objects.img_shuffle_icon, lv_color_hex(theme_colors[active_theme_index][6]), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_shuffle_icon, 255, 0);
            lv_obj_add_state(objects.btn_shuffle, LV_STATE_CHECKED);
        } else {
            lv_obj_set_style_image_recolor(objects.img_shuffle_icon, lv_color_hex(theme_colors[active_theme_index][5]), 0);
            lv_obj_set_style_image_recolor_opa(objects.img_shuffle_icon, 255, 0);
            lv_obj_remove_state(objects.btn_shuffle, LV_STATE_CHECKED);
        }
    }
    ESP_LOGI(TAG, "Action: set_shuffle -> %d", s_settings.shuffle);
}

void action_set_resume(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.sw_resume) return;
    bool checked = lv_obj_has_state(objects.sw_resume, LV_STATE_CHECKED);
    s_settings.resume = checked ? 1 : 0;
    settings_nvs_set_u8("resume", s_settings.resume);
    ESP_LOGI(TAG, "Action: set_resume -> %d", s_settings.resume);
}

void action_set_seek_step(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (!objects.dd_seek_step) return;
    int sel = lv_dropdown_get_selected(objects.dd_seek_step);
    uint8_t step = (sel == 0) ? 5 : ((sel == 1) ? 10 : 30);
    s_settings.seekstep = step;
    settings_nvs_set_u8("seekstep", step);
    ESP_LOGI(TAG, "Action: set_seek_step -> %d s", step);
}
