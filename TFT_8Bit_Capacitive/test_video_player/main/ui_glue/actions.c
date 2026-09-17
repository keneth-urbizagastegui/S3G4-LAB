#include "ui/actions.h"
#include "ui/screens.h"
#include "ui/images.h"
#include "ui/ui.h"
#include "ui/styles.h"
#include "ui_glue.h"
#include "player.h"
#include "settings_nvs.h"
#include "media_library.h"
#include "lcd_bus.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>

static const char *TAG = "UI_ACTIONS";

static bool s_osd_visible = true;
static int s_hud_forced_mode = 0; // 0=auto, 1=forced hidden, 2=forced visible
static int64_t s_last_touch_time = 0;
static bool s_seeking = false;
static int s_current_track_idx = 0;
static view_mode_t s_view_mode = VIEW_MODE_FULLSCREEN;
static app_settings_t s_settings;

static bool s_locked = false;
static lv_obj_t *s_ovl_lock = NULL;
static lv_obj_t *s_lock_card = NULL;
static lv_obj_t *s_arc_unlock = NULL;
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

extern void touch_inject_synthetic(uint16_t x, uint16_t y, bool pressed);

static lv_obj_t *s_toast_box = NULL;
static lv_obj_t *s_toast_icon = NULL;
static lv_obj_t *s_toast_title = NULL;
static lv_obj_t *s_toast_desc = NULL;
static lv_timer_t *s_toast_timer = NULL;

static void toast_timer_cb(lv_timer_t *t) {
    if (s_toast_box) {
        lv_obj_add_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN);
    }
    if (s_toast_timer) {
        lv_timer_delete(s_toast_timer);
        s_toast_timer = NULL;
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
}

void ui_glue_dump_all(void) {
    ui_glue_fix_all_button_flags();
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
            lv_obj_remove_flag(s_lock_card, LV_OBJ_FLAG_HIDDEN);
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

    // Card: x=140, y=104, w=200, h=116, bg #0B0C0F, radius 8, border 1px #2A2D34
    s_lock_card = lv_obj_create(s_ovl_lock);
    lv_obj_set_pos(s_lock_card, 140, 104);
    lv_obj_set_size(s_lock_card, 200, 116);
    lv_obj_set_style_bg_color(s_lock_card, lv_color_hex(0x0B0C0F), 0);
    lv_obj_set_style_bg_opa(s_lock_card, 255, 0);
    lv_obj_set_style_border_color(s_lock_card, lv_color_hex(0x2A2D34), 0);
    lv_obj_set_style_border_width(s_lock_card, 1, 0);
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

    // Title: x=0, y=84, w=200, h=16
    lv_obj_t *lbl_title = lv_label_create(s_lock_card);
    lv_obj_set_pos(lbl_title, 0, 84);
    lv_obj_set_size(lbl_title, 200, 16);
    lv_label_set_text(lbl_title, "Pantalla bloqueada");
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_title, lv_color_hex(0xEDEDEA), 0);
    lv_obj_set_style_text_align(lbl_title, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_remove_flag(lbl_title, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(lbl_title, LV_OBJ_FLAG_EVENT_BUBBLE);

    // Subtitle / hint: x=0, y=100, w=200, h=14
    lv_obj_t *lbl_hint = lv_label_create(s_lock_card);
    lv_obj_set_pos(lbl_hint, 0, 100);
    lv_obj_set_size(lbl_hint, 200, 14);
    lv_label_set_text(lbl_hint, "Mantén pulsado para desbloquear");
    lv_obj_set_style_text_font(lbl_hint, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(lbl_hint, lv_color_hex(0x8E929B), 0);
    lv_obj_set_style_text_align(lbl_hint, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_remove_flag(lbl_hint, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(lbl_hint, LV_OBJ_FLAG_EVENT_BUBBLE);
}

void ui_glue_unlock(void) {
    s_locked = false;
    s_lock_touch_start_us = 0;
    if (s_ovl_lock) {
        lv_obj_add_flag(s_ovl_lock, LV_OBJ_FLAG_HIDDEN);
    }
    if (s_arc_unlock) {
        lv_arc_set_value(s_arc_unlock, 0);
    }
    ui_glue_set_osd_visible(true);
    printf("UINAV,btn=unlock,result=PASS\n");
    fflush(stdout);
    ESP_LOGI(TAG, "Action: unlock -> pantalla desbloqueada");
}

void ui_glue_init(void) {
    settings_nvs_load(&s_settings);
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
            if (objects.bar_mini_progress) lv_obj_remove_flag(objects.bar_mini_progress, LV_OBJ_FLAG_HIDDEN);
            player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
            player_cmd_send(&cmd);
            lcd_bus_set_video_rect(0, 0, 480, 320);
        }
    } else {
        // Fuera de scr_player el video nunca se pinta (rectangulo siempre {0,0,0,0})
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
            if (idx == s_current_track_idx) {
                lv_obj_remove_flag(badge, LV_OBJ_FLAG_HIDDEN);
            } else {
                lv_obj_add_flag(badge, LV_OBJ_FLAG_HIDDEN);
            }
        }

        if (bar_res) {
            if (item->resume_ms > 0 && item->dur_ms > 0) {
                lv_obj_remove_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
                int32_t pct = (int32_t)(((uint64_t)item->resume_ms * 1000) / item->dur_ms);
                lv_bar_set_value(bar_res, pct, LV_ANIM_OFF);
            } else {
                lv_obj_add_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
}

void ui_glue_set_view_mode(view_mode_t mode) {
    view_mode_t old_mode = s_view_mode;
    s_view_mode = mode;
    printf("VIEW,mode=%s,track=%d\n", (mode == VIEW_MODE_FULLSCREEN) ? "player" : "library", s_current_track_idx);
    fflush(stdout);

    if (mode == VIEW_MODE_FULLSCREEN) {
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
    } else {
        // Al salir de scr_player el video se pausa y se guarda la posicion
        if (old_mode == VIEW_MODE_FULLSCREEN) {
            player_status_t st;
            player_get_status(&st);
            if (st.state == PST_PLAYING) {
                player_cmd_t cmd_pause = {.type = PCMD_PAUSE};
                player_cmd_send(&cmd_pause);
            }
            const media_item_t *cur = media_library_get(s_current_track_idx);
            if (cur && cur->compatible) {
                media_library_set_resume(cur->path, (uint32_t)st.pos_ms);
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

void ui_glue_tick(void) {
    player_status_t st;
    player_get_status(&st);
    s_current_track_idx = st.track_index;

    // Si la reproduccion termino (transicion PLAYING -> ENDED) y estamos en modo fullscreen -> volver a biblioteca
    static player_state_t s_prev_player_state = PST_IDLE;
    if (s_prev_player_state == PST_PLAYING && st.state == PST_ENDED && s_view_mode == VIEW_MODE_FULLSCREEN) {
        ESP_LOGI(TAG, "Reproduccion finalizada en modo fullscreen -> retornando a biblioteca");
        action_open_library(NULL);
        s_prev_player_state = st.state;
        return;
    }
    s_prev_player_state = st.state;

    // Update play icon
    if (objects.lbl_play_icon) {
        lv_image_set_src(objects.lbl_play_icon, (st.state == PST_PLAYING) ? &img_pause : &img_play);
    }

    // Auto-hide OSD (solo en scr_player / modo fullscreen)
    if (s_view_mode == VIEW_MODE_FULLSCREEN && s_hud_forced_mode == 0 && s_osd_visible && st.state == PST_PLAYING && !s_seeking) {
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
            lv_obj_add_flag(s_lock_card, LV_OBJ_FLAG_HIDDEN);
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
        lv_obj_remove_flag(s_lock_card, LV_OBJ_FLAG_HIDDEN);
    }
    if (s_arc_unlock) {
        lv_arc_set_value(s_arc_unlock, 0);
    }
    s_lock_show_time = esp_timer_get_time() / 1000;
    s_lock_touch_start_us = 0;

    printf("UINAV,btn=lock,result=PASS\n");
    fflush(stdout);
    ESP_LOGI(TAG, "Action: lock -> pantalla bloqueada");
}

void action_toggle_osd(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    if (s_hud_forced_mode != 0) return;
    ui_glue_set_osd_visible(!s_osd_visible);
    ESP_LOGI(TAG, "Action: toggle_osd -> visible=%d", s_osd_visible);
}

void action_open_library(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    action_library_populate(NULL);
    ui_glue_set_view_mode(VIEW_MODE_STUDIO);
    ESP_LOGI(TAG, "Action: open_library");
}

void action_open_queue(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    ESP_LOGI(TAG, "Action: open_queue -> mostrando aviso");
    ui_glue_show_toast("Próximamente", "Esta opción llega en la próxima versión.", false);
}

void action_close_queue(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_open_settings(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_locked) return;
    ESP_LOGI(TAG, "Action: open_settings -> mostrando aviso");
    ui_glue_show_toast("Próximamente", "Esta opción llega en la próxima versión.", false);
}

static void wait_gui_ms(uint32_t ms) {
    uint32_t count = (ms + 14) / 15;
    for (uint32_t i = 0; i < count; i++) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(15));
    }
}

static void sim_touch_click(uint16_t x, uint16_t y) {
    touch_inject_synthetic(x, y, true);
    for (int i = 0; i < 6; i++) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(15));
    }
    touch_inject_synthetic(x, y, false);
    for (int i = 0; i < 6; i++) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(15));
    }
}

static void sim_touch_hold(uint16_t x, uint16_t y, uint32_t hold_ms) {
    touch_inject_synthetic(x, y, true);
    uint32_t elapsed = 0;
    while (elapsed < hold_ms) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(20));
        elapsed += 20;
    }
    touch_inject_synthetic(x, y, false);
    for (int i = 0; i < 6; i++) {
        lv_timer_handler();
        vTaskDelay(pdMS_TO_TICKS(15));
    }
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

    // 3. btn=queue (x=458, y=20) -> muestra aviso toast (L2)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(200);
    sim_touch_click(458, 20);
    wait_gui_ms(300);
    bool queue_ok = (s_toast_box != NULL && !lv_obj_has_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN));
    printf("UINAV,btn=queue,result=%s\n", queue_ok ? "PASS" : "FAIL");
    if (s_toast_box) lv_obj_add_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN);
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

    // 11. btn=settings (x=450, y=295)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    sim_touch_click(450, 295);
    wait_gui_ms(150);
    bool set_ok = (s_toast_box != NULL && !lv_obj_has_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN));
    printf("UINAV,btn=settings,result=%s\n", set_ok ? "PASS" : "FAIL");
    if (s_toast_box) lv_obj_add_flag(s_toast_box, LV_OBJ_FLAG_HIDDEN);
    wait_gui_ms(50);

    // 12. btn=seek (x=340, y=249) -> barra de seek
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    player_status_t st_b_seek;
    player_get_status(&st_b_seek);
    sim_touch_click(340, 249);
    wait_gui_ms(350);
    player_status_t st_a_seek;
    player_get_status(&st_a_seek);
    bool seek_ok = (abs((int32_t)st_a_seek.pos_ms - (int32_t)st_b_seek.pos_ms) > 1000);
    printf("UINAV,btn=seek,result=%s\n", seek_ok ? "PASS" : "FAIL");

    // 13. btn=lock (x=30, y=295)
    ui_glue_set_osd_visible(true);
    wait_gui_ms(100);
    sim_touch_click(30, 295);
    wait_gui_ms(150);
    bool lock_ok = s_locked;
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

    fflush(stdout);
    ESP_LOGI(TAG, "=== FIN PRUEBA UINAV ===");
    s_uinav_running = false;
}

void action_settings_tab(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_open_stats(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
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

    // Subtitle label: x=16, y=35, w=380, h=14, font 12, color #8E929B
    s_resume_sub = lv_label_create(s_resume_sheet);
    lv_obj_set_pos(s_resume_sub, 16, 35);
    lv_obj_set_size(s_resume_sub, 380, 14);
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
        char msg[128];
        snprintf(msg, sizeof(msg), "%s", (item->incompat[0] != '\0') ? item->incompat : "Formato o resolución incompatible.");
        ui_glue_show_toast("Video incompatible", msg, true);
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
    esp_err_t err = media_library_scan();
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
    lv_obj_set_size(card, 144, 124);
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
    lv_obj_t *badge = lv_obj_create(card);
    lv_obj_set_pos(badge, 6, 6);
    lv_obj_set_size(badge, 90, 18);
    if (idx != s_current_track_idx) {
        lv_obj_add_flag(badge, LV_OBJ_FLAG_HIDDEN);
    }
    lv_obj_remove_flag(badge, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(badge, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(badge, LV_SCROLLBAR_MODE_OFF);
    add_style_st_chip(badge);

    lv_obj_t *lbl_badge = lv_label_create(badge);
    lv_obj_set_pos(lbl_badge, 0, 1);
    lv_obj_set_size(lbl_badge, 90, 16);
    lv_obj_remove_flag(lbl_badge, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ELASTIC|LV_OBJ_FLAG_SCROLL_MOMENTUM|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
    lv_obj_add_flag(lbl_badge, LV_OBJ_FLAG_EVENT_BUBBLE);
    lv_obj_set_scrollbar_mode(lbl_badge, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_text_font(lbl_badge, &lv_font_montserrat_12, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(lbl_badge, lv_color_hex(theme_colors[active_theme_index][6]), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_text_align(lbl_badge, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_label_set_text_static(lbl_badge, "Reproduciendo");

    // bar_resume (child 2)
    lv_obj_t *bar_res = lv_bar_create(card);
    lv_obj_set_pos(bar_res, 0, 77);
    lv_obj_set_size(bar_res, 144, 3);
    lv_bar_set_range(bar_res, 0, 1000);
    if (item->resume_ms > 0 && item->dur_ms > 0) {
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
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_14, LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_obj_set_style_text_color(lbl_title, lv_color_hex(theme_colors[active_theme_index][4]), LV_PART_MAIN | LV_STATE_DEFAULT);
    lv_label_set_text(lbl_title, item->title[0] ? item->title : item->path);

    // lbl_card_meta (child 4)
    lv_obj_t *lbl_meta = lv_label_create(card);
    lv_obj_set_pos(lbl_meta, 0, 104);
    lv_obj_set_size(lbl_meta, 144, 14);
    lv_label_set_long_mode(lbl_meta, LV_LABEL_LONG_DOT);
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
        lv_obj_set_style_opa(card, LV_OPA_50, 0);
        if (item->incompat[0]) {
            lv_label_set_text(lbl_meta, item->incompat);
        }
    } else if (!item->rotated) {
        lv_label_set_text(lbl_meta, "Sin girar");
    }

    return card;
}

void action_library_populate(lv_event_t *e) {
    if (!objects.lib_grid) return;
    lv_obj_clean(objects.lib_grid);

    int count = media_library_count();
    ESP_LOGI(TAG, "Populating library grid: %d items", count);

    for (int i = 0; i < count; i++) {
        create_card_widget(objects.lib_grid, i);
    }
    lv_obj_update_layout(objects.lib_grid);
}

void action_set_brightness(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_osd_timeout(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_show_stats(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_mini_progress(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_repeat(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_shuffle(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_resume(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_seek_step(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}
