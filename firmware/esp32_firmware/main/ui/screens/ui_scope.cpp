#include "ui_scope.h"
#include "ui_common.h"
#include "ui_view.h"
#include "comm_spi_master.h"
#include <esp_log.h>
#include <lvgl.h>

static const char *TAG = "ui_scope";

LV_FONT_DECLARE(lv_font_montserrat_14);
LV_FONT_DECLARE(lv_font_montserrat_24);

// UI Layout / Widget Pointers & States
static lv_obj_t *floating_win = NULL;
static lv_obj_t *sidebar = NULL;
static bool sidebar_visible = false;

typedef enum { MENU_NONE, MENU_MEAS, MENU_TRIG, MENU_TIMEBASE, MENU_VOLT_DIV } eActiveMenu;
static eActiveMenu active_menu = MENU_NONE;
static int active_menu_channel = 0;
static lv_obj_t *meas_overlay_panel = NULL;
static bool scope_is_running = true;

static const char *timebase_names[] = {
    "50ns", "100ns", "200ns", "500ns", "1us", "2us", "5us", "10us", "20us", "50us", "100us", "200us", "500us", "1ms", "2ms", "5ms", "10ms", "20ms", "50ms", "100ms", "200ms", "500ms", "1s"
};

static const char *volt_div_names[] = {
    "50mV", "100mV", "200mV", "500mV", "1V", "2V", "5V"
};

static uint32_t wave_colors[] = {0xFFB700, 0x3FB950, 0x00EEFF, 0xE85AAD, 0xEEEEEE}; // Yellow, Lime, Cyan, Pink, White

// Helper to disable touch propagation inside buttons (useful for labels inside buttons)
static void make_descendants_click_through(lv_obj_t *obj) {
    if (!obj) return;
    uint32_t cnt = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(obj, i);
        lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
        make_descendants_click_through(child);
    }
}

static void update_meas_layout(void) {
    if (meas_overlay_panel) {
        lv_obj_clean(meas_overlay_panel);
    } else {
        meas_overlay_panel = lv_obj_create(active_screen_container);
        lv_obj_set_size(meas_overlay_panel, 440, 236);
        lv_obj_set_pos(meas_overlay_panel, 20, 44);
        lv_obj_set_style_bg_opa(meas_overlay_panel, LV_OPA_TRANSP, 0);
        lv_obj_set_style_border_width(meas_overlay_panel, 0, 0);
        lv_obj_set_style_pad_all(meas_overlay_panel, 0, 0);
        lv_obj_remove_flag(meas_overlay_panel, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_remove_flag(meas_overlay_panel, LV_OBJ_FLAG_CLICKABLE);
    }

    for (int ch = 0; ch < 4; ch++) {
        for (int m = 0; m < 14; m++) {
            scope_meas_labels[ch][m] = NULL;
        }
    }

    struct MeasPair {
        int ch;
        int m;
    } active_pairs[56];
    int pair_cnt = 0;

    for (int ch = 0; ch < 4; ch++) {
        if (!scope_ch_active[ch]) continue;
        for (int m = 0; m < 14; m++) {
            if (scope_meas_active[ch][m]) {
                active_pairs[pair_cnt++] = {ch, m};
            }
        }
    }

    for (int i = 0; i < pair_cnt; i++) {
        int col = i % 3;
        int row = i / 3;
        int ch = active_pairs[i].ch;
        int m = active_pairs[i].m;

        int x = 10 + col * 145;
        int y = 202 - row * 26; // Stacks upwards from bottom

        if (y < 0) continue;

        lv_obj_t *card = lv_obj_create(meas_overlay_panel);
        lv_obj_set_size(card, 130, 22);
        lv_obj_set_pos(card, x, y);
        lv_obj_remove_flag(card, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_remove_flag(card, LV_OBJ_FLAG_CLICKABLE);

        lv_color_t border_col = lv_color_hex(wave_colors[ch]);
        lv_obj_set_style_bg_color(card, get_current_panel_color(), 0);
        lv_obj_set_style_bg_opa(card, LV_OPA_60, 0);
        lv_obj_set_style_border_color(card, border_col, 0);
        lv_obj_set_style_border_width(card, 1, 0);
        lv_obj_set_style_radius(card, 6, 0);
        lv_obj_set_style_pad_all(card, 0, 0);

        lv_obj_t *lbl = lv_label_create(card);
        lv_obj_center(lbl);
        lv_obj_set_style_text_color(lbl, border_col, 0);
        lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
        lv_label_set_text(lbl, "--");

        scope_meas_labels[ch][m] = lbl;
    }
}

static void close_floating_win(void) {
    if (floating_win) {
        lv_obj_delete(floating_win);
        floating_win = NULL;
    }
    active_menu = MENU_NONE;
}

static lv_obj_t *open_floating_win(const char *title, int w, int h) {
    close_floating_win();

    floating_win = lv_obj_create(active_screen_container);
    lv_obj_set_size(floating_win, w, h);
    lv_obj_set_pos(floating_win, 40, 60);
    lv_obj_remove_flag(floating_win, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_set_style_bg_color(floating_win, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(floating_win, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(floating_win, 2, 0);
    lv_obj_set_style_radius(floating_win, 8, 0);
    lv_obj_set_style_pad_all(floating_win, 0, 0);

    lv_obj_t *hdr = lv_obj_create(floating_win);
    lv_obj_set_size(hdr, w - 4, 28);
    lv_obj_set_pos(hdr, 0, 0);
    lv_obj_set_style_bg_color(hdr, get_current_accent_color(), 0);
    lv_obj_set_style_radius(hdr, 0, 0);
    lv_obj_set_style_border_width(hdr, 0, 0);
    lv_obj_set_style_pad_all(hdr, 0, 0);
    lv_obj_remove_flag(hdr, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_title = lv_label_create(hdr);
    lv_label_set_text(lbl_title, title);
    lv_obj_set_style_text_color(lbl_title, lv_color_black(), 0);
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_title, LV_ALIGN_LEFT_MID, 8, 0);

    lv_obj_t *btn_close = lv_button_create(hdr);
    lv_obj_set_size(btn_close, 22, 22);
    lv_obj_align(btn_close, LV_ALIGN_RIGHT_MID, -3, 0);
    lv_obj_set_style_bg_color(btn_close, lv_color_hex(0xDA3637), 0);
    lv_obj_set_style_radius(btn_close, 4, 0);
    lv_obj_set_style_pad_all(btn_close, 0, 0);
    lv_obj_add_event_cb(btn_close, [](lv_event_t *e){ close_floating_win(); transition_to_screen(SCREEN_OSCOPE); }, LV_EVENT_CLICKED, NULL);

    lv_obj_t *lbl_x = lv_label_create(btn_close);
    lv_label_set_text(lbl_x, "X");
    lv_obj_set_style_text_color(lbl_x, lv_color_white(), 0);
    lv_obj_center(lbl_x);

    lv_obj_t *content = lv_obj_create(floating_win);
    lv_obj_set_size(content, w - 4, h - 32);
    lv_obj_set_pos(content, 0, 30);
    lv_obj_set_style_bg_opa(content, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(content, 0, 0);
    lv_obj_set_style_pad_all(content, 6, 0);
    lv_obj_remove_flag(content, LV_OBJ_FLAG_SCROLLABLE);

    return content;
}

static void build_meas_menu(int ch);
static void build_trig_menu(void);
static void build_sidebar(void);
static void build_timebase_menu(void);
static void build_volt_div_menu(void);

static void build_meas_menu(int ch) {
    active_menu = MENU_MEAS;
    active_menu_channel = ch;

    char title[32];
    snprintf(title, sizeof(title), "CH%d MEASUREMENTS", ch + 1);
    lv_obj_t *content = open_floating_win(title, 292, 175);

    const char *meas_names[] = {
        "Freq", "PKPK", "Mean", "RMS", "Amp", "Duty", "Wid+", "Wid-", "Perd", "Max", "Min", "Top", "Base", "Duty-", "All"
    };

    for (int i = 0; i < 15; i++) {
        int col = i % 4;
        int row = i / 4;

        lv_obj_t *btn = lv_button_create(content);
        lv_obj_set_size(btn, 62, 26);
        lv_obj_set_pos(btn, col * 68, row * 32);
        lv_obj_remove_flag(btn, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_pad_all(btn, 0, 0);
        lv_obj_set_style_radius(btn, 4, 0);

        bool is_active = (i == 14) ? false : scope_meas_active[ch][i];
        if (i == 14) {
            bool all_act = true;
            for (int m = 0; m < 14; m++) {
                if (!scope_meas_active[ch][m]) { all_act = false; break; }
            }
            is_active = all_act;
        }

        if (is_active) {
            lv_obj_set_style_bg_color(btn, lv_color_hex(wave_colors[ch]), 0);
            lv_obj_set_style_border_width(btn, 0, 0);
        } else {
            lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
            lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
            lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
            lv_obj_set_style_border_width(btn, 1, 0);
        }

        lv_obj_t *lbl = lv_label_create(btn);
        lv_label_set_text(lbl, meas_names[i]);
        lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
        if (is_active) {
            lv_obj_set_style_text_color(lbl, lv_color_black(), 0);
        } else {
            lv_obj_set_style_text_color(lbl, get_current_text_color(), 0);
        }
        lv_obj_center(lbl);

        lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
            int idx = (int)(uintptr_t)lv_event_get_user_data(ev);
            int ch = active_menu_channel;
            if (idx == 14) {
                bool any_off = false;
                for (int m = 0; m < 14; m++) {
                    if (!scope_meas_active[ch][m]) { any_off = true; break; }
                }
                for (int m = 0; m < 14; m++) {
                    scope_meas_active[ch][m] = any_off;
                }
            } else {
                scope_meas_active[ch][idx] = !scope_meas_active[ch][idx];
            }
            update_meas_layout();
            build_meas_menu(ch);
        }, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
        make_descendants_click_through(btn);
    }
}

static void build_trig_menu(void) {
    active_menu = MENU_TRIG;
    lv_obj_t *content = open_floating_win("TRIGGER CONFIG", 280, 180);

    const char *rows[] = {"Trig mode", "Trig level", "Trig edge", "Source"};

    for (int r = 0; r < 4; r++) {
        lv_obj_t *lbl = lv_label_create(content);
        lv_label_set_text(lbl, rows[r]);
        lv_obj_set_style_text_color(lbl, get_current_text_color(), 0);
        lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
        lv_obj_set_pos(lbl, 10, r * 34 + 8);

        if (r == 0) {
            const char *opts[] = {"Auto", "Normal"};
            for (int o = 0; o < 2; o++) {
                lv_obj_t *btn = lv_button_create(content);
                lv_obj_set_size(btn, 70, 26);
                lv_obj_set_pos(btn, 100 + o * 76, r * 34 + 2);
                lv_obj_set_style_pad_all(btn, 0, 0);
                lv_obj_set_style_radius(btn, 4, 0);

                bool act = (scope_trig_mode == o);
                if (act) {
                    lv_obj_set_style_bg_color(btn, get_current_accent_color(), 0);
                } else {
                    lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
                    lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
                    lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
                    lv_obj_set_style_border_width(btn, 1, 0);
                }

                lv_obj_t *lbl_opt = lv_label_create(btn);
                lv_label_set_text(lbl_opt, opts[o]);
                lv_obj_set_style_text_font(lbl_opt, &lv_font_montserrat_14, 0);
                lv_obj_set_style_text_color(lbl_opt, act ? lv_color_black() : get_current_text_color(), 0);
                lv_obj_center(lbl_opt);

                lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
                    scope_trig_mode = (int)(uintptr_t)lv_event_get_user_data(ev);
                    build_trig_menu();
                }, LV_EVENT_CLICKED, (void*)(uintptr_t)o);
                make_descendants_click_through(btn);
            }
        } else if (r == 1) {
            const char *opts[] = {"Auto", "Manual"};
            for (int o = 0; o < 2; o++) {
                lv_obj_t *btn = lv_button_create(content);
                lv_obj_set_size(btn, 70, 26);
                lv_obj_set_pos(btn, 100 + o * 76, r * 34 + 2);
                lv_obj_set_style_pad_all(btn, 0, 0);
                lv_obj_set_style_radius(btn, 4, 0);

                bool act = (scope_trig_level_mode == o);
                if (act) {
                    lv_obj_set_style_bg_color(btn, get_current_accent_color(), 0);
                } else {
                    lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
                    lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
                    lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
                    lv_obj_set_style_border_width(btn, 1, 0);
                }

                lv_obj_t *lbl_opt = lv_label_create(btn);
                lv_label_set_text(lbl_opt, opts[o]);
                lv_obj_set_style_text_font(lbl_opt, &lv_font_montserrat_14, 0);
                lv_obj_set_style_text_color(lbl_opt, act ? lv_color_black() : get_current_text_color(), 0);
                lv_obj_center(lbl_opt);

                lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
                    scope_trig_level_mode = (int)(uintptr_t)lv_event_get_user_data(ev);
                    build_trig_menu();
                }, LV_EVENT_CLICKED, (void*)(uintptr_t)o);
                make_descendants_click_through(btn);
            }
        } else if (r == 2) {
            const char *opts[] = {"Rise", "Fall"};
            for (int o = 0; o < 2; o++) {
                lv_obj_t *btn = lv_button_create(content);
                lv_obj_set_size(btn, 70, 26);
                lv_obj_set_pos(btn, 100 + o * 76, r * 34 + 2);
                lv_obj_set_style_pad_all(btn, 0, 0);
                lv_obj_set_style_radius(btn, 4, 0);

                bool act = (scope_trig_edge == o);
                if (act) {
                    lv_obj_set_style_bg_color(btn, get_current_accent_color(), 0);
                } else {
                    lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
                    lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
                    lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
                    lv_obj_set_style_border_width(btn, 1, 0);
                }

                lv_obj_t *lbl_opt = lv_label_create(btn);
                lv_label_set_text(lbl_opt, opts[o]);
                lv_obj_set_style_text_font(lbl_opt, &lv_font_montserrat_14, 0);
                lv_obj_set_style_text_color(lbl_opt, act ? lv_color_black() : get_current_text_color(), 0);
                lv_obj_center(lbl_opt);

                lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
                    scope_trig_edge = (int)(uintptr_t)lv_event_get_user_data(ev);
                    build_trig_menu();
                }, LV_EVENT_CLICKED, (void*)(uintptr_t)o);
                make_descendants_click_through(btn);
            }
        } else if (r == 3) {
            const char *opts[] = {"CH1", "CH2", "CH3", "CH4"};
            for (int o = 0; o < 4; o++) {
                lv_obj_t *btn = lv_button_create(content);
                lv_obj_set_size(btn, 36, 26);
                lv_obj_set_pos(btn, 100 + o * 40, r * 34 + 2);
                lv_obj_set_style_pad_all(btn, 0, 0);
                lv_obj_set_style_radius(btn, 4, 0);

                bool act = (scope_trig_source == o);
                if (act) {
                    lv_obj_set_style_bg_color(btn, lv_color_hex(wave_colors[o]), 0);
                } else {
                    lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
                    lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
                    lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
                    lv_obj_set_style_border_width(btn, 1, 0);
                }

                lv_obj_t *lbl_opt = lv_label_create(btn);
                lv_label_set_text(lbl_opt, opts[o]);
                lv_obj_set_style_text_font(lbl_opt, &lv_font_montserrat_14, 0);
                lv_obj_set_style_text_color(lbl_opt, act ? lv_color_black() : get_current_text_color(), 0);
                lv_obj_center(lbl_opt);

                lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
                    scope_trig_source = (int)(uintptr_t)lv_event_get_user_data(ev);
                    build_trig_menu();
                }, LV_EVENT_CLICKED, (void*)(uintptr_t)o);
                make_descendants_click_through(btn);
            }
        }
    }
}

static void build_timebase_menu(void) {
    active_menu = MENU_TIMEBASE;
    lv_obj_t *content = open_floating_win("TIMEBASE SELECT", 262, 170);

    for (int i = 0; i < 12; i++) {
        int col = i % 4;
        int row = i / 4;
        int actual_idx = i + 6; // Indices 6 to 17: "5us" to "20ms"

        lv_obj_t *btn = lv_button_create(content);
        lv_obj_set_size(btn, 54, 28);
        lv_obj_set_pos(btn, col * 60, row * 34 + 10);
        lv_obj_remove_flag(btn, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_pad_all(btn, 0, 0);
        lv_obj_set_style_radius(btn, 4, 0);

        bool act = (scope_timebase_idx == actual_idx);
        if (act) {
            lv_obj_set_style_bg_color(btn, get_current_accent_color(), 0);
        } else {
            lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
            lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
            lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
            lv_obj_set_style_border_width(btn, 1, 0);
        }

        lv_obj_t *lbl = lv_label_create(btn);
        lv_label_set_text(lbl, timebase_names[actual_idx]);
        lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(lbl, act ? lv_color_black() : get_current_text_color(), 0);
        lv_obj_center(lbl);

        lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
            scope_timebase_idx = (int)(uintptr_t)lv_event_get_user_data(ev);
            close_floating_win();
            transition_to_screen(SCREEN_OSCOPE);
        }, LV_EVENT_CLICKED, (void*)(uintptr_t)actual_idx);
        make_descendants_click_through(btn);
    }
}

static void build_volt_div_menu(void) {
    active_menu = MENU_VOLT_DIV;
    lv_obj_t *content = open_floating_win("VOLT/DIV SELECT", 260, 140);

    int ch = scope_trig_source;

    for (int i = 0; i < 7; i++) {
        int col = i % 4;
        int row = i / 4;

        lv_obj_t *btn = lv_button_create(content);
        lv_obj_set_size(btn, 54, 30);
        lv_obj_set_pos(btn, col * 60, row * 36 + 10);
        lv_obj_remove_flag(btn, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_pad_all(btn, 0, 0);
        lv_obj_set_style_radius(btn, 4, 0);

        bool act = (scope_volt_div_idx[ch] == i);
        if (act) {
            lv_obj_set_style_bg_color(btn, get_current_accent_color(), 0);
        } else {
            lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
            lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
            lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
            lv_obj_set_style_border_width(btn, 1, 0);
        }

        lv_obj_t *lbl = lv_label_create(btn);
        lv_label_set_text(lbl, volt_div_names[i]);
        lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(lbl, act ? lv_color_black() : get_current_text_color(), 0);
        lv_obj_center(lbl);

        lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
            int i_val = (int)(uintptr_t)lv_event_get_user_data(ev);
            int ch = scope_trig_source;
            scope_volt_div_idx[ch] = i_val;
            close_floating_win();
            transition_to_screen(SCREEN_OSCOPE);
        }, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
        make_descendants_click_through(btn);
    }
}

static void build_sidebar(void) {
    if (sidebar) {
        lv_obj_delete(sidebar);
        sidebar = NULL;
    }

    if (!sidebar_visible) return;

    sidebar = lv_obj_create(active_screen_container);
    lv_obj_set_size(sidebar, 100, 260);
    lv_obj_set_pos(sidebar, 380, 30);
    lv_obj_remove_flag(sidebar, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_set_style_bg_color(sidebar, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(sidebar, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(sidebar, 1, 0);
    lv_obj_set_style_border_side(sidebar, (lv_border_side_t)(LV_BORDER_SIDE_LEFT | LV_BORDER_SIDE_TOP | LV_BORDER_SIDE_BOTTOM), 0);
    lv_obj_set_style_radius(sidebar, 0, 0);
    lv_obj_set_style_pad_all(sidebar, 4, 0);

    const char *sidebar_names[] = {
        "Meas ch1", "Meas ch2", "Meas ch3", "Meas ch4", "Trig"
    };

    for (int i = 0; i < 5; i++) {
        lv_obj_t *btn = lv_button_create(sidebar);
        lv_obj_set_size(btn, 88, 38);
        lv_obj_set_pos(btn, 2, i * 46 + 10);
        lv_obj_remove_flag(btn, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_pad_all(btn, 0, 0);
        lv_obj_set_style_radius(btn, 4, 0);

        bool is_act_btn = false;
        if (i < 4 && active_menu == MENU_MEAS && active_menu_channel == i) is_act_btn = true;
        if (i == 4 && active_menu == MENU_TRIG) is_act_btn = true;

        if (is_act_btn) {
            lv_obj_set_style_bg_color(btn, get_current_accent_color(), 0);
        } else {
            lv_obj_set_style_bg_color(btn, get_current_panel_color(), 0);
            lv_obj_set_style_border_color(btn, get_current_text_color(), 0);
            lv_obj_set_style_border_opa(btn, LV_OPA_30, 0);
            lv_obj_set_style_border_width(btn, 1, 0);
        }

        lv_obj_t *lbl = lv_label_create(btn);
        lv_label_set_text(lbl, sidebar_names[i]);
        lv_obj_set_style_text_font(lbl, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(lbl, is_act_btn ? lv_color_black() : get_current_text_color(), 0);
        lv_obj_center(lbl);

        lv_obj_add_event_cb(btn, [](lv_event_t *ev) {
            int idx = (int)(uintptr_t)lv_event_get_user_data(ev);
            if (idx < 4) {
                if (active_menu == MENU_MEAS && active_menu_channel == idx) {
                    close_floating_win();
                    transition_to_screen(SCREEN_OSCOPE);
                } else {
                    build_meas_menu(idx);
                }
            } else {
                if (active_menu == MENU_TRIG) {
                    close_floating_win();
                    transition_to_screen(SCREEN_OSCOPE);
                } else {
                    build_trig_menu();
                }
            }
            build_sidebar();
        }, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
        make_descendants_click_through(btn);
    }
}

static void menu_click_cb(lv_event_t *e) {
    sidebar_visible = !sidebar_visible;
    if (!sidebar_visible) {
        close_floating_win();
    }
    build_sidebar();
}

static lv_obj_t *limit_box = NULL;
static lv_timer_t *limit_timer = NULL;

void cleanup_scope_ui(void) {
    if (limit_timer) {
        lv_timer_delete(limit_timer);
        limit_timer = NULL;
    }
    limit_box = NULL;

    // Reset all measurement label pointers to prevent dangling pointer crashes
    for (int ch = 0; ch < 4; ch++) {
        for (int m = 0; m < 14; m++) {
            scope_meas_labels[ch][m] = NULL;
        }
    }
}

static void sync_scope_settings(void) {
    // 1. Send Horizontal settings (Timebase)
    static const uint32_t timebase_sampling_freq_khz[] = {
        1024000, 512000, 256000, 102400, 51200, 25600, 10240, 5120, 2560, 1024,
        512, 256, 102, 51, 26, 10, 5, 3, 1, 1, 1, 1, 1
    };
    uint32_t scale = timebase_sampling_freq_khz[scope_timebase_idx];
    uint32_t horiz_data = 0 | (scale << 16); // offset = 0, scale = sampling rate in kHz
    comm_spi_master_send_cmd(CMD_SCOPE_CONFIG_HORIZ, 0, horiz_data);

    // 2. Send Vertical settings for all 4 channels
    static const uint8_t volt_div_gain_mapping[] = { 4, 3, 2, 1, 0, 0, 0 };
    for (int ch = 0; ch < 4; ch++) {
        uint8_t enable = scope_ch_active[ch] ? 1 : 0;
        uint8_t gain = volt_div_gain_mapping[scope_volt_div_idx[ch]];
        uint32_t vert_data = (enable & 0xFF) | ((gain & 0xFF) << 8) | ((2048 & 0xFFFF) << 16);
        comm_spi_master_send_cmd(CMD_SCOPE_CONFIG_VERT, ch, vert_data);
    }

    // 3. Send Trigger settings
    int trig_level = 2048;
    if (scope_trig_level_mode == 1) { // Manual
        trig_level = (int)(((280.0f - (float)scope_trig_arrow_y) / 236.0f) * 4095.0f);
    }
    if (trig_level < 0) trig_level = 0;
    if (trig_level > 4095) trig_level = 4095;
    uint32_t trig_data = (scope_trig_mode | (scope_trig_edge << 8) | (trig_level << 16));
    comm_spi_master_send_cmd(CMD_SCOPE_CONFIG_TRIG, scope_trig_source, trig_data);

    // 4. Send Run/Stop state
    if (scope_is_running) {
        comm_spi_master_send_cmd(CMD_SCOPE_START, 1, 0);
    } else {
        comm_spi_master_send_cmd(CMD_SCOPE_STOP, 0, 0);
    }
}

void populate_scope_ui(void) {
    cleanup_scope_ui();
    sync_scope_settings();
    floating_win = NULL;
    sidebar = NULL;
    meas_overlay_panel = NULL;

    // Grid occupying the whole center (440x236 at y=44, centered, separated)
    chart_obj = lv_chart_create(active_screen_container);
    lv_obj_set_size(chart_obj, 440, 236);
    lv_obj_set_pos(chart_obj, 20, 44);
    lv_obj_set_style_bg_color(chart_obj, lv_color_hex(0x000000), 0);
    lv_obj_set_style_border_color(chart_obj, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(chart_obj, 0, 0);
    lv_obj_set_style_pad_all(chart_obj, 0, 0);

    lv_chart_set_type(chart_obj, LV_CHART_TYPE_LINE);
    lv_chart_set_point_count(chart_obj, 256);
    lv_chart_set_range(chart_obj, LV_CHART_AXIS_PRIMARY_Y, 0, 255);
    lv_chart_set_update_mode(chart_obj, LV_CHART_UPDATE_MODE_SHIFT);

    if (opt_grid_type == 2) {
        lv_chart_set_div_line_count(chart_obj, 0, 0);
        lv_obj_set_style_border_width(chart_obj, 0, 0);
    } else {
        lv_chart_set_div_line_count(chart_obj, 9, 11);
        lv_opa_t opas[] = {LV_OPA_20, LV_OPA_50, LV_OPA_80};
        lv_opa_t grid_opa = opas[opt_grid_intensity];
        
        lv_obj_set_style_line_color(chart_obj, get_current_text_color(), LV_PART_MAIN);
        lv_obj_set_style_line_opa(chart_obj, grid_opa, LV_PART_MAIN);

        // Closes the grid on the bottom and right by styling the border like the grid lines
        lv_obj_set_style_border_color(chart_obj, get_current_text_color(), 0);
        lv_obj_set_style_border_width(chart_obj, 1, 0);
        lv_obj_set_style_border_opa(chart_obj, grid_opa, 0);
        
        if (opt_grid_type == 0) {
            lv_obj_set_style_line_dash_width(chart_obj, 1, LV_PART_MAIN);
            lv_obj_set_style_line_dash_gap(chart_obj, 4, LV_PART_MAIN);
        } else {
            lv_obj_set_style_line_dash_width(chart_obj, 0, LV_PART_MAIN);
        }
    }

    // Allocate series (Colors matching opt_chX_color settings)
    uint32_t ch_color_indices[] = {(uint32_t)opt_ch1_color, (uint32_t)opt_ch2_color, (uint32_t)opt_ch3_color, (uint32_t)opt_ch4_color};
    ser_ch1 = lv_chart_add_series(chart_obj, lv_color_hex(wave_colors[ch_color_indices[0]]), LV_CHART_AXIS_PRIMARY_Y);
    ser_ch2 = lv_chart_add_series(chart_obj, lv_color_hex(wave_colors[ch_color_indices[1]]), LV_CHART_AXIS_PRIMARY_Y);
    ser_ch3 = lv_chart_add_series(chart_obj, lv_color_hex(wave_colors[ch_color_indices[2]]), LV_CHART_AXIS_PRIMARY_Y);
    ser_ch4 = lv_chart_add_series(chart_obj, lv_color_hex(wave_colors[ch_color_indices[3]]), LV_CHART_AXIS_PRIMARY_Y);

    // Rebuild the overlay cards container
    update_meas_layout();

    // Top control overlay bar
    lv_obj_t *top_bar = lv_obj_create(active_screen_container);
    lv_obj_set_size(top_bar, 480, 30);
    lv_obj_set_pos(top_bar, 0, 0);
    lv_obj_set_style_bg_color(top_bar, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(top_bar, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(top_bar, 1, 0);
    lv_obj_set_style_border_side(top_bar, LV_BORDER_SIDE_BOTTOM, 0);
    lv_obj_set_style_radius(top_bar, 0, 0);
    lv_obj_set_style_pad_all(top_bar, 0, 0);
    lv_obj_remove_flag(top_bar, LV_OBJ_FLAG_SCROLLABLE);

    // Standardized Home button
    lv_obj_t *btn_home = lv_button_create(top_bar);
    lv_obj_set_size(btn_home, 46, 26);
    lv_obj_align(btn_home, LV_ALIGN_LEFT_MID, 8, 0);
    lv_obj_set_style_bg_color(btn_home, get_current_panel_color(), 0);
    lv_obj_set_style_bg_color(btn_home, get_current_accent_color(), LV_STATE_PRESSED);
    lv_obj_set_style_border_color(btn_home, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(btn_home, 1, 0);
    lv_obj_set_style_radius(btn_home, 6, 0);
    lv_obj_set_style_pad_all(btn_home, 0, 0);
    lv_obj_remove_flag(btn_home, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(btn_home, [](lv_event_t *e){ close_floating_win(); transition_to_screen(SCREEN_HOME); }, LV_EVENT_CLICKED, NULL);

    lv_obj_t *lbl_home_icon = lv_label_create(btn_home);
    lv_label_set_text(lbl_home_icon, LV_SYMBOL_HOME);
    lv_obj_set_style_text_color(lbl_home_icon, lv_color_white(), 0);
    lv_obj_set_style_text_font(lbl_home_icon, &lv_font_montserrat_14, 0);
    lv_obj_center(lbl_home_icon);
    make_descendants_click_through(btn_home);

    // RUN/STOP button
    lv_obj_t *btn_run = lv_button_create(top_bar);
    lv_obj_set_size(btn_run, 60, 24);
    lv_obj_align(btn_run, LV_ALIGN_LEFT_MID, 58, 0);
    lv_obj_set_style_radius(btn_run, 4, 0);
    lv_obj_set_style_pad_all(btn_run, 0, 0);

    lv_color_t run_color = scope_is_running ? lv_color_hex(0x238636) : lv_color_hex(0xDA3637);
    lv_obj_set_style_bg_color(btn_run, run_color, 0);

    lv_obj_t *lbl_run = lv_label_create(btn_run);
    lv_label_set_text(lbl_run, scope_is_running ? "RUN" : "STOP");
    lv_obj_set_style_text_font(lbl_run, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_run, lv_color_white(), 0);
    lv_obj_center(lbl_run);
    make_descendants_click_through(btn_run);

    lv_obj_add_event_cb(btn_run, [](lv_event_t *e) {
        scope_is_running = !scope_is_running;
        if (!scope_is_running) {
            for (int i = 0; i < 18; i++) {
                if (!view_box_has_data[i]) {
                    view_box_has_data[i] = true;
                    ESP_LOGI(TAG, "Screenshot saved at index %d", i);
                    break;
                }
            }
        }
        transition_to_screen(SCREEN_OSCOPE);
    }, LV_EVENT_CLICKED, NULL);

    // Pulse Waveform shape icon (drawn as a vector line)
    static const lv_point_precise_t pts_pulse[] = { {0, 10}, {5, 10}, {5, 2}, {11, 2}, {11, 10}, {16, 10} };
    lv_obj_t *pulse_line = lv_line_create(top_bar);
    lv_line_set_points(pulse_line, pts_pulse, 6);
    lv_obj_set_style_line_color(pulse_line, get_current_accent_color(), 0);
    lv_obj_set_style_line_width(pulse_line, 2, 0);
    lv_obj_align(pulse_line, LV_ALIGN_LEFT_MID, 124, 0);

    // Bracketed Trigger position bar: [ ── T ── ] (Dynamic container)
    lv_obj_t *trig_pos_container = lv_obj_create(top_bar);
    lv_obj_set_size(trig_pos_container, 120, 26);
    lv_obj_align(trig_pos_container, LV_ALIGN_CENTER, -10, 0);
    lv_obj_set_style_bg_opa(trig_pos_container, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(trig_pos_container, 0, 0);
    lv_obj_set_style_pad_all(trig_pos_container, 0, 0);
    lv_obj_remove_flag(trig_pos_container, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_bracket_left = lv_label_create(trig_pos_container);
    lv_label_set_text(lbl_bracket_left, "[");
    lv_obj_set_style_text_color(lbl_bracket_left, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_bracket_left, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_bracket_left, LV_ALIGN_LEFT_MID, 0, 0);

    lv_obj_t *lbl_bracket_right = lv_label_create(trig_pos_container);
    lv_label_set_text(lbl_bracket_right, "]");
    lv_obj_set_style_text_color(lbl_bracket_right, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_bracket_right, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_bracket_right, LV_ALIGN_RIGHT_MID, 0, 0);

    static const lv_point_precise_t pts_bracket_line[] = { {8, 13}, {112, 13} };
    lv_obj_t *bracket_line = lv_line_create(trig_pos_container);
    lv_line_set_points(bracket_line, pts_bracket_line, 2);
    lv_obj_set_style_line_color(bracket_line, get_current_text_color(), 0);
    lv_obj_set_style_line_width(bracket_line, 1, 0);
    lv_obj_set_style_line_opa(bracket_line, LV_OPA_40, 0);

    lv_obj_t *lbl_trig_t = lv_label_create(trig_pos_container);
    lv_label_set_text(lbl_trig_t, LV_SYMBOL_DOWN);
    lv_obj_set_style_text_color(lbl_trig_t, lv_color_hex(0x00EEFF), 0);
    lv_obj_set_style_text_font(lbl_trig_t, &lv_font_montserrat_14, 0);

    // Cyan trigger position arrow below the bracketed bar (Larger font and LVGL Symbols)
    lv_obj_t *lbl_trig_arrow = lv_label_create(active_screen_container);
    lv_obj_set_style_text_color(lbl_trig_arrow, lv_color_hex(0x00EEFF), 0);
    lv_obj_set_style_text_font(lbl_trig_arrow, &lv_font_montserrat_24, 0);

    if (scope_trig_level_mode == 1) { // Manual
        lv_obj_add_flag(lbl_trig_arrow, LV_OBJ_FLAG_CLICKABLE);
        
        // Initial arrow text direction
        if (scope_trig_arrow_x <= 20) {
            scope_trig_arrow_x = 20;
            lv_label_set_text(lbl_trig_arrow, LV_SYMBOL_RIGHT);
        } else if (scope_trig_arrow_x >= 460) {
            scope_trig_arrow_x = 460;
            lv_label_set_text(lbl_trig_arrow, LV_SYMBOL_LEFT);
        } else {
            lv_label_set_text(lbl_trig_arrow, LV_SYMBOL_DOWN);
        }
        lv_obj_set_pos(lbl_trig_arrow, scope_trig_arrow_x - 12, 30);
        
        float pct = (float)(scope_trig_arrow_x - 20) / 440.0f;
        int t_x_pos = 8 + (int)(pct * 92.0f);
        lv_obj_set_pos(lbl_trig_t, t_x_pos, 2);

        lv_obj_add_event_cb(lbl_trig_arrow, [](lv_event_t *e) {
            lv_obj_t *obj = (lv_obj_t *)lv_event_get_target(e);
            lv_obj_t *t_label = (lv_obj_t *)lv_event_get_user_data(e);
            
            lv_indev_t *indev = lv_indev_active();
            if (indev == NULL) return;

            lv_point_t vect;
            lv_indev_get_vect(indev, &vect);

            int x = lv_obj_get_x(obj) + vect.x + 12; // Center X (24px width)
            bool reached_limit = false;

            if (x <= 20) {
                x = 20;
                lv_label_set_text(obj, LV_SYMBOL_RIGHT);
                reached_limit = true;
            } else if (x >= 460) {
                x = 460;
                lv_label_set_text(obj, LV_SYMBOL_LEFT);
                reached_limit = true;
            } else {
                lv_label_set_text(obj, LV_SYMBOL_DOWN);
            }
            
            scope_trig_arrow_x = x;
            lv_obj_set_pos(obj, x - 12, 30);
            
            float pct = (float)(scope_trig_arrow_x - 20) / 440.0f;
            int t_x_pos = 8 + (int)(pct * 92.0f);
            lv_obj_set_pos(t_label, t_x_pos, 2);
            
            // Maintain the vertical trigger level (which is determined by scope_trig_arrow_y)
            int mapped_val = 2048;
            if (scope_trig_level_mode == 1) { // Manual
                mapped_val = (int)(((280.0f - (float)scope_trig_arrow_y) / 236.0f) * 4095.0f);
            }
            if (mapped_val < 0) mapped_val = 0;
            if (mapped_val > 4095) mapped_val = 4095;
            comm_spi_master_send_cmd(CMD_SCOPE_CONFIG_TRIG, scope_trig_source, 
                (scope_trig_mode | (scope_trig_edge << 8) | (mapped_val << 16)));

            // LIMIT warning overlay logic
            if (reached_limit) {
                if (limit_box == NULL) {
                    limit_box = lv_obj_create(active_screen_container);
                    lv_obj_set_size(limit_box, 72, 26);
                    lv_obj_center(limit_box);
                    lv_obj_set_style_bg_color(limit_box, lv_color_hex(0xDA3637), 0); // Red
                    lv_obj_set_style_border_width(limit_box, 0, 0);
                    lv_obj_set_style_radius(limit_box, 4, 0);
                    lv_obj_set_style_pad_all(limit_box, 0, 0);
                    lv_obj_remove_flag(limit_box, LV_OBJ_FLAG_SCROLLABLE);

                    lv_obj_t *lbl_limit = lv_label_create(limit_box);
                    lv_label_set_text(lbl_limit, "LIMIT");
                    lv_obj_set_style_text_color(lbl_limit, lv_color_white(), 0);
                    lv_obj_set_style_text_font(lbl_limit, &lv_font_montserrat_14, 0);
                    lv_obj_center(lbl_limit);
                    
                    limit_timer = lv_timer_create([](lv_timer_t *t) {
                        lv_obj_t *box = (lv_obj_t *)lv_timer_get_user_data(t);
                        if (box) {
                            lv_obj_delete(box);
                        }
                        limit_box = NULL;
                        limit_timer = NULL;
                        lv_timer_delete(t);
                    }, 1000, limit_box);
                } else {
                    if (limit_timer) {
                        lv_timer_reset(limit_timer);
                    }
                }
            }
        }, LV_EVENT_PRESSING, lbl_trig_t);
    } else { // Auto (Fixed to center)
        scope_trig_arrow_x = 240;
        lv_label_set_text(lbl_trig_arrow, LV_SYMBOL_DOWN);
        lv_obj_remove_flag(lbl_trig_arrow, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_set_pos(lbl_trig_arrow, 240 - 12, 30);
        
        float pct = (float)(scope_trig_arrow_x - 20) / 440.0f;
        int t_x_pos = 8 + (int)(pct * 92.0f);
        lv_obj_set_pos(lbl_trig_t, t_x_pos, 2);
    }

    // ── Left Lateral Arrow (Voltage Reference 0 V / GND) ────────────────────
    lv_obj_t *lbl_zero_v_arrow = lv_label_create(active_screen_container);
    lv_label_set_text(lbl_zero_v_arrow, LV_SYMBOL_RIGHT);
    lv_obj_set_style_text_color(lbl_zero_v_arrow, lv_color_hex(0xFFB700), 0); // Yellow
    lv_obj_set_style_text_font(lbl_zero_v_arrow, &lv_font_montserrat_24, 0);
    
    int y_zero_v = get_y_coord_for_zero_v(scope_trig_source);
    lv_obj_set_pos(lbl_zero_v_arrow, 2, y_zero_v - 12);

    // ── Right Lateral Arrow (Trigger Level Threshold) ───────────────────────
    lv_obj_t *lbl_trig_v_arrow = lv_label_create(active_screen_container);
    lv_label_set_text(lbl_trig_v_arrow, LV_SYMBOL_LEFT);
    lv_obj_set_style_text_color(lbl_trig_v_arrow, lv_color_hex(0xFFB700), 0); // Yellow
    lv_obj_set_style_text_font(lbl_trig_v_arrow, &lv_font_montserrat_24, 0);
    
    if (scope_trig_level_mode == 1) { // Manual
        lv_obj_add_flag(lbl_trig_v_arrow, LV_OBJ_FLAG_CLICKABLE);
        if (scope_trig_arrow_y < 44) scope_trig_arrow_y = 44;
        if (scope_trig_arrow_y > 280) scope_trig_arrow_y = 280;
        lv_obj_set_pos(lbl_trig_v_arrow, 458, scope_trig_arrow_y - 12);
        
        lv_obj_add_event_cb(lbl_trig_v_arrow, [](lv_event_t *ev) {
            lv_obj_t *obj = (lv_obj_t *)lv_event_get_target(ev);
            lv_indev_t *indev = lv_indev_active();
            if (indev == NULL) return;
            
            lv_point_t vect;
            lv_indev_get_vect(indev, &vect);
            
            int y = lv_obj_get_y(obj) + vect.y + 12; // Center Y
            bool reached_limit = false;
            
            if (y <= 44) {
                y = 44;
                reached_limit = true;
            } else if (y >= 280) {
                y = 280;
                reached_limit = true;
            }
            
            scope_trig_arrow_y = y;
            lv_obj_set_pos(obj, 458, y - 12);
            
            int mapped_val = (int)(((280.0f - (float)y) / 236.0f) * 4095.0f);
            if (mapped_val < 0) mapped_val = 0;
            if (mapped_val > 4095) mapped_val = 4095;
            
            comm_spi_master_send_cmd(CMD_SCOPE_CONFIG_TRIG, scope_trig_source,
                (scope_trig_mode | (scope_trig_edge << 8) | (mapped_val << 16)));
                
            if (reached_limit) {
                if (limit_box == NULL) {
                    limit_box = lv_obj_create(active_screen_container);
                    lv_obj_set_size(limit_box, 72, 26);
                    lv_obj_center(limit_box);
                    lv_obj_set_style_bg_color(limit_box, lv_color_hex(0xDA3637), 0); // Red
                    lv_obj_set_style_border_width(limit_box, 0, 0);
                    lv_obj_set_style_radius(limit_box, 4, 0);
                    lv_obj_set_style_pad_all(limit_box, 0, 0);
                    lv_obj_remove_flag(limit_box, LV_OBJ_FLAG_SCROLLABLE);

                    lv_obj_t *lbl_limit = lv_label_create(limit_box);
                    lv_label_set_text(lbl_limit, "LIMIT");
                    lv_obj_set_style_text_color(lbl_limit, lv_color_white(), 0);
                    lv_obj_set_style_text_font(lbl_limit, &lv_font_montserrat_14, 0);
                    lv_obj_center(lbl_limit);
                    
                    limit_timer = lv_timer_create([](lv_timer_t *t) {
                        lv_obj_t *box = (lv_obj_t *)lv_timer_get_user_data(t);
                        if (box) {
                            lv_obj_delete(box);
                        }
                        limit_box = NULL;
                        limit_timer = NULL;
                        lv_timer_delete(t);
                    }, 1000, limit_box);
                } else {
                    if (limit_timer) {
                        lv_timer_reset(limit_timer);
                    }
                }
            }
        }, LV_EVENT_PRESSING, NULL);
    } else { // Auto (Fixed to center Y=162)
        scope_trig_arrow_y = 162;
        lv_obj_remove_flag(lbl_trig_v_arrow, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_set_pos(lbl_trig_v_arrow, 458, 162 - 12);
    }

    // Trigger Mode Status Badge (Auto / Normal text and color changing)
    lv_obj_t *trig_badge = lv_obj_create(top_bar);
    lv_obj_set_size(trig_badge, 64, 20);
    lv_obj_align(trig_badge, LV_ALIGN_RIGHT_MID, -90, 0);
    uint32_t badge_color = (scope_trig_mode == 0) ? 0x892CA0 : 0x1F6FEB;
    lv_obj_set_style_bg_color(trig_badge, lv_color_hex(badge_color), 0);
    lv_obj_set_style_radius(trig_badge, 3, 0);
    lv_obj_set_style_border_width(trig_badge, 0, 0);
    lv_obj_set_style_pad_all(trig_badge, 0, 0);
    lv_obj_remove_flag(trig_badge, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_trig_badge = lv_label_create(trig_badge);
    lv_label_set_text(lbl_trig_badge, scope_trig_mode == 0 ? "Auto" : "Normal");
    lv_obj_set_style_text_color(lbl_trig_badge, lv_color_white(), 0);
    lv_obj_set_style_text_font(lbl_trig_badge, &lv_font_montserrat_14, 0);
    lv_obj_center(lbl_trig_badge);

    // Trigger Edge slope icon (drawn as a vector line)
    lv_obj_t *edge_line = lv_line_create(top_bar);
    static const lv_point_precise_t pts_rise[] = { {0, 10}, {6, 10}, {12, 2}, {18, 2} };
    static const lv_point_precise_t pts_fall[] = { {0, 2}, {6, 2}, {12, 10}, {18, 10} };

    if (scope_trig_edge == 0) {
        lv_line_set_points(edge_line, pts_rise, 4);
    } else {
        lv_line_set_points(edge_line, pts_fall, 4);
    }
    lv_obj_set_style_line_color(edge_line, lv_color_hex(0xFFB700), 0); // Yellow
    lv_obj_set_style_line_width(edge_line, 2, 0);
    lv_obj_align(edge_line, LV_ALIGN_RIGHT_MID, -64, 0);

    // MENU button
    lv_obj_t *btn_menu = lv_button_create(top_bar);
    lv_obj_set_size(btn_menu, 48, 24);
    lv_obj_align(btn_menu, LV_ALIGN_RIGHT_MID, -4, 0);
    lv_obj_set_style_bg_color(btn_menu, sidebar_visible ? get_current_accent_color() : get_current_panel_color(), 0);
    lv_obj_set_style_border_color(btn_menu, get_current_text_color(), 0);
    lv_obj_set_style_border_opa(btn_menu, LV_OPA_30, 0);
    lv_obj_set_style_border_width(btn_menu, 1, 0);
    lv_obj_set_style_radius(btn_menu, 4, 0);
    lv_obj_set_style_pad_all(btn_menu, 0, 0);
    lv_obj_add_event_cb(btn_menu, menu_click_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *lbl_menu = lv_label_create(btn_menu);
    lv_label_set_text(lbl_menu, "MENU");
    lv_obj_set_style_text_font(lbl_menu, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_menu, sidebar_visible ? lv_color_black() : get_current_text_color(), 0);
    lv_obj_center(lbl_menu);
    make_descendants_click_through(btn_menu);

    // Bottom Control panel (height 30 at y=290)
    lv_obj_t *bot_bar = lv_obj_create(active_screen_container);
    lv_obj_set_size(bot_bar, 480, 30);
    lv_obj_set_pos(bot_bar, 0, 290);
    lv_obj_set_style_bg_color(bot_bar, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(bot_bar, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(bot_bar, 1, 0);
    lv_obj_set_style_border_side(bot_bar, LV_BORDER_SIDE_TOP, 0);
    lv_obj_set_style_radius(bot_bar, 0, 0);
    lv_obj_set_style_pad_all(bot_bar, 0, 0);
    lv_obj_remove_flag(bot_bar, LV_OBJ_FLAG_SCROLLABLE);

    // 4 Channel selection toggles
    for (int i = 0; i < 4; i++) {
        lv_obj_t *btn_ch = lv_button_create(bot_bar);
        lv_obj_set_size(btn_ch, 44, 24);
        lv_obj_set_pos(btn_ch, 10 + i * 48, 2);
        lv_obj_remove_flag(btn_ch, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_pad_all(btn_ch, 0, 0);
        lv_obj_set_style_radius(btn_ch, 4, 0);

        bool active = scope_ch_active[i];
        if (active) {
            lv_obj_set_style_bg_color(btn_ch, lv_color_hex(wave_colors[i]), 0);
        } else {
            lv_obj_set_style_bg_color(btn_ch, get_current_panel_color(), 0);
            lv_obj_set_style_border_color(btn_ch, lv_color_hex(wave_colors[i]), 0);
            lv_obj_set_style_border_opa(btn_ch, LV_OPA_30, 0);
            lv_obj_set_style_border_width(btn_ch, 1, 0);
        }

        lv_obj_t *lbl_ch = lv_label_create(btn_ch);
        lv_label_set_text_fmt(lbl_ch, "CH%d", i + 1);
        lv_obj_set_style_text_font(lbl_ch, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(lbl_ch, active ? lv_color_black() : get_current_text_color(), 0);
        lv_obj_center(lbl_ch);

        lv_obj_add_event_cb(btn_ch, [](lv_event_t *ev) {
            int idx = (int)(uintptr_t)lv_event_get_user_data(ev);
            scope_ch_active[idx] = !scope_ch_active[idx];
            update_meas_layout();
            transition_to_screen(SCREEN_OSCOPE);
        }, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
        make_descendants_click_through(btn_ch);
    }

    // Timebase button
    lv_obj_t *btn_tb = lv_button_create(bot_bar);
    lv_obj_set_size(btn_tb, 90, 24);
    lv_obj_set_pos(btn_tb, 204, 2);
    lv_obj_remove_flag(btn_tb, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_pad_all(btn_tb, 0, 0);
    lv_obj_set_style_radius(btn_tb, 4, 0);
    
    lv_obj_set_style_bg_color(btn_tb, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(btn_tb, get_current_text_color(), 0);
    lv_obj_set_style_border_opa(btn_tb, LV_OPA_30, 0);
    lv_obj_set_style_border_width(btn_tb, 1, 0);

    lv_obj_t *lbl_tb = lv_label_create(btn_tb);
    lv_label_set_text_fmt(lbl_tb, "Time: %s", timebase_names[scope_timebase_idx]);
    lv_obj_set_style_text_font(lbl_tb, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_tb, get_current_accent_color(), 0);
    lv_obj_center(lbl_tb);

    lv_obj_add_event_cb(btn_tb, [](lv_event_t *e) {
        if (active_menu == MENU_TIMEBASE) close_floating_win();
        else build_timebase_menu();
    }, LV_EVENT_CLICKED, NULL);
    make_descendants_click_through(btn_tb);

    // Volt/Div button
    int active_trig_ch = scope_trig_source;
    lv_obj_t *btn_vd = lv_button_create(bot_bar);
    lv_obj_set_size(btn_vd, 100, 24);
    lv_obj_set_pos(btn_vd, 304, 2);
    lv_obj_remove_flag(btn_vd, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_pad_all(btn_vd, 0, 0);
    lv_obj_set_style_radius(btn_vd, 4, 0);

    lv_obj_set_style_bg_color(btn_vd, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(btn_vd, get_current_text_color(), 0);
    lv_obj_set_style_border_opa(btn_vd, LV_OPA_30, 0);
    lv_obj_set_style_border_width(btn_vd, 1, 0);

    lv_obj_t *lbl_vd = lv_label_create(btn_vd);
    lv_label_set_text_fmt(lbl_vd, "CH%d V: %s", active_trig_ch + 1, volt_div_names[scope_volt_div_idx[active_trig_ch]]);
    lv_obj_set_style_text_font(lbl_vd, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_vd, lv_color_hex(wave_colors[active_trig_ch]), 0);
    lv_obj_center(lbl_vd);

    lv_obj_add_event_cb(btn_vd, [](lv_event_t *e) {
        if (active_menu == MENU_VOLT_DIV) close_floating_win();
        else build_volt_div_menu();
    }, LV_EVENT_CLICKED, NULL);
    make_descendants_click_through(btn_vd);

    // Auto Scale button
    lv_obj_t *btn_auto = lv_button_create(bot_bar);
    lv_obj_set_size(btn_auto, 58, 24);
    lv_obj_set_pos(btn_auto, 412, 2);
    lv_obj_remove_flag(btn_auto, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_pad_all(btn_auto, 0, 0);
    lv_obj_set_style_radius(btn_auto, 4, 0);

    lv_obj_set_style_bg_color(btn_auto, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(btn_auto, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(btn_auto, 1, 0);

    lv_obj_t *lbl_auto = lv_label_create(btn_auto);
    lv_label_set_text(lbl_auto, "Auto");
    lv_obj_set_style_text_font(lbl_auto, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_auto, get_current_accent_color(), 0);
    lv_obj_center(lbl_auto);

    lv_obj_add_event_cb(btn_auto, [](lv_event_t *e) {
        tSpiTxPayload local_telemetry;
        if (comm_spi_master_get_latest_telemetry(&local_telemetry)) {
            uint16_t vpp = local_telemetry.header.vpp;
            uint32_t freq = local_telemetry.header.frequency;
            int ch = scope_trig_source;

            // 1. Optimize Volt/Div to fit signal within 4-6 divisions
            int opt_volt = 6; // Default to 5V/div (index 6)
            if (vpp < 300) opt_volt = 0;      // 50mV
            else if (vpp < 600) opt_volt = 1; // 100mV
            else if (vpp < 1200) opt_volt = 2; // 200mV
            else if (vpp < 3000) opt_volt = 3; // 500mV
            else if (vpp < 6000) opt_volt = 4; // 1V
            else if (vpp < 12000) opt_volt = 5; // 2V
            scope_volt_div_idx[ch] = opt_volt;

            // 2. Optimize Timebase to show ~2-4 cycles
            int opt_tb = 11; // Default to 200us (index 11)
            if (freq > 0) {
                float t_div = 300000.0f / (float)freq; // target division time in microseconds
                if (t_div < 7.5f) opt_tb = 6;        // 5us
                else if (t_div < 15.0f) opt_tb = 7;  // 10us
                else if (t_div < 35.0f) opt_tb = 8;  // 20us
                else if (t_div < 75.0f) opt_tb = 9;  // 50us
                else if (t_div < 150.0f) opt_tb = 10; // 100us
                else if (t_div < 350.0f) opt_tb = 11; // 200us
                else if (t_div < 750.0f) opt_tb = 12; // 500us
                else if (t_div < 1500.0f) opt_tb = 13; // 1ms
                else if (t_div < 3500.0f) opt_tb = 14; // 2ms
                else if (t_div < 7500.0f) opt_tb = 15; // 5ms
                else if (t_div < 15000.0f) opt_tb = 16; // 10ms
                else opt_tb = 17; // 20ms
            }
            scope_timebase_idx = opt_tb;

            // 3. Reset Trigger to Auto to center it automatically
            scope_trig_mode = 0; // Auto
            scope_trig_level_mode = 0; // Auto
            scope_trig_arrow_y = 162; // Center Y

            transition_to_screen(SCREEN_OSCOPE);
        }
    }, LV_EVENT_CLICKED, NULL);
    make_descendants_click_through(btn_auto);

    // Rebuild sidebar if visible
    if (sidebar_visible) {
        build_sidebar();
    }
    // Rebuild active floating menus
    if (active_menu == MENU_TRIG) {
        build_trig_menu();
    } else if (active_menu == MENU_MEAS) {
        build_meas_menu(active_menu_channel);
    } else if (active_menu == MENU_TIMEBASE) {
        build_timebase_menu();
    } else if (active_menu == MENU_VOLT_DIV) {
        build_volt_div_menu();
    }
}
