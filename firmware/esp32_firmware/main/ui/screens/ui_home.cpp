#include "ui_home.h"
#include "ui_common.h"
#include <lvgl.h>
#include <string.h>

extern "C" {
  LV_FONT_DECLARE(lv_font_montserrat_28);
  LV_FONT_DECLARE(lv_font_montserrat_14);
}

struct sHomeBtn {
    const char *label;
    const char *icon_type;
    eScreen target_screen;
};

static void home_card_click_cb(lv_event_t *e) {
    eScreen target = (eScreen)(uintptr_t)lv_event_get_user_data(e);
    transition_to_screen(target);
}

static void make_descendants_click_through(lv_obj_t *obj) {
    if (!obj) return;
    uint32_t cnt = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(obj, i);
        lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
        make_descendants_click_through(child);
    }
}

static void create_home_card(sHomeBtn btn_info, int x, int y) {
    lv_obj_t *card = lv_obj_create(active_screen_container);
    lv_obj_set_size(card, 80, 80);
    lv_obj_set_pos(card, x, y);
    lv_obj_set_style_bg_color(card, get_current_panel_color(), 0);
    lv_obj_set_style_bg_color(card, get_current_accent_color(), LV_STATE_PRESSED);
    lv_obj_set_style_border_color(card, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(card, 2, 0);
    lv_obj_set_style_radius(card, 12, 0);
    lv_obj_set_style_pad_all(card, 0, 0);
    lv_obj_remove_flag(card, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(card, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(card, home_card_click_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)btn_info.target_screen);

    const char *type = btn_info.icon_type;
    if (strcmp(type, "oscope") == 0) {
        // 1. Oscilloscope Frame
        lv_obj_t *osc_body = lv_obj_create(card);
        lv_obj_set_size(osc_body, 64, 46);
        lv_obj_align(osc_body, LV_ALIGN_CENTER, 0, -6);
        lv_obj_set_style_bg_color(osc_body, lv_color_hex(0x94A3B8), 0);
        lv_obj_set_style_border_color(osc_body, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(osc_body, 2, 0);
        lv_obj_set_style_radius(osc_body, 6, 0);
        lv_obj_set_style_pad_all(osc_body, 0, 0);
        lv_obj_remove_flag(osc_body, LV_OBJ_FLAG_SCROLLABLE);

        // 2. Screen
        lv_obj_t *osc_screen = lv_obj_create(osc_body);
        lv_obj_set_size(osc_screen, 42, 32);
        lv_obj_align(osc_screen, LV_ALIGN_LEFT_MID, 4, 0);
        lv_obj_set_style_bg_color(osc_screen, lv_color_hex(0x0F172A), 0);
        lv_obj_set_style_border_color(osc_screen, lv_color_hex(0x1E293B), 0);
        lv_obj_set_style_border_width(osc_screen, 1, 0);
        lv_obj_set_style_radius(osc_screen, 2, 0);
        lv_obj_set_style_pad_all(osc_screen, 0, 0);
        lv_obj_remove_flag(osc_screen, LV_OBJ_FLAG_SCROLLABLE);

        // 3. Grid Lines
        lv_obj_t *grid_h = lv_obj_create(osc_screen);
        lv_obj_set_size(grid_h, 42, 1);
        lv_obj_align(grid_h, LV_ALIGN_CENTER, 0, 0);
        lv_obj_set_style_bg_color(grid_h, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(grid_h, 0, 0);

        lv_obj_t *grid_v = lv_obj_create(osc_screen);
        lv_obj_set_size(grid_v, 1, 32);
        lv_obj_align(grid_v, LV_ALIGN_CENTER, 0, 0);
        lv_obj_set_style_bg_color(grid_v, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(grid_v, 0, 0);

        // 4. Wave points (Sine wave)
        static lv_point_precise_t osc_points[] = {
            {2, 16}, {8, 7}, {14, 16}, {20, 25}, {26, 16}, {32, 7}, {38, 16}
        };
        lv_obj_t *osc_wave = lv_line_create(osc_screen);
        lv_line_set_points(osc_wave, osc_points, 7);
        lv_obj_set_style_line_color(osc_wave, lv_color_hex(0xEAB308), 0);
        lv_obj_set_style_line_width(osc_wave, 2, 0);

        // 5. Knobs and buttons on panel
        lv_obj_t *osc_knob1 = lv_obj_create(osc_body);
        lv_obj_set_size(osc_knob1, 6, 6);
        lv_obj_align(osc_knob1, LV_ALIGN_TOP_RIGHT, -4, 6);
        lv_obj_set_style_bg_color(osc_knob1, lv_color_hex(0xE2E8F0), 0);
        lv_obj_set_style_border_width(osc_knob1, 0, 0);
        lv_obj_set_style_radius(osc_knob1, LV_RADIUS_CIRCLE, 0);

        lv_obj_t *osc_knob2 = lv_obj_create(osc_body);
        lv_obj_set_size(osc_knob2, 6, 6);
        lv_obj_align(osc_knob2, LV_ALIGN_TOP_RIGHT, -4, 16);
        lv_obj_set_style_bg_color(osc_knob2, lv_color_hex(0xE2E8F0), 0);
        lv_obj_set_style_border_width(osc_knob2, 0, 0);
        lv_obj_set_style_radius(osc_knob2, LV_RADIUS_CIRCLE, 0);

        lv_obj_t *osc_dot1 = lv_obj_create(osc_body);
        lv_obj_set_size(osc_dot1, 3, 3);
        lv_obj_align(osc_dot1, LV_ALIGN_BOTTOM_RIGHT, -6, -8);
        lv_obj_set_style_bg_color(osc_dot1, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(osc_dot1, 0, 0);
        lv_obj_set_style_radius(osc_dot1, LV_RADIUS_CIRCLE, 0);

        lv_obj_t *osc_dot2 = lv_obj_create(osc_body);
        lv_obj_set_size(osc_dot2, 3, 3);
        lv_obj_align(osc_dot2, LV_ALIGN_BOTTOM_RIGHT, -2, -8);
        lv_obj_set_style_bg_color(osc_dot2, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(osc_dot2, 0, 0);
        lv_obj_set_style_radius(osc_dot2, LV_RADIUS_CIRCLE, 0);

    } else if (strcmp(type, "dmm") == 0) {
        // 1. DMM Body (vertical)
        lv_obj_t *dmm_body = lv_obj_create(card);
        lv_obj_set_size(dmm_body, 42, 58);
        lv_obj_align(dmm_body, LV_ALIGN_CENTER, 0, -6);
        lv_obj_set_style_bg_color(dmm_body, lv_color_hex(0x94A3B8), 0);
        lv_obj_set_style_border_color(dmm_body, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(dmm_body, 2, 0);
        lv_obj_set_style_radius(dmm_body, 6, 0);
        lv_obj_set_style_pad_all(dmm_body, 0, 0);
        lv_obj_remove_flag(dmm_body, LV_OBJ_FLAG_SCROLLABLE);

        // 2. DMM Display (upper half)
        lv_obj_t *dmm_disp = lv_obj_create(dmm_body);
        lv_obj_set_size(dmm_disp, 32, 18);
        lv_obj_align(dmm_disp, LV_ALIGN_TOP_MID, 0, 4);
        lv_obj_set_style_bg_color(dmm_disp, lv_color_hex(0x0F172A), 0);
        lv_obj_set_style_border_color(dmm_disp, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(dmm_disp, 1, 0);
        lv_obj_set_style_radius(dmm_disp, 2, 0);
        lv_obj_set_style_pad_all(dmm_disp, 0, 0);
        lv_obj_remove_flag(dmm_disp, LV_OBJ_FLAG_SCROLLABLE);

        // 3. Mini bar at top of LCD display
        lv_obj_t *dmm_topbar = lv_obj_create(dmm_disp);
        lv_obj_set_size(dmm_topbar, 32, 3);
        lv_obj_align(dmm_topbar, LV_ALIGN_TOP_MID, 0, 0);
        lv_obj_set_style_bg_color(dmm_topbar, lv_color_hex(0x38BDF8), 0);
        lv_obj_set_style_border_width(dmm_topbar, 0, 0);

        // 4. "12.4" value in LCD display
        lv_obj_t *dmm_lbl = lv_label_create(dmm_disp);
        lv_label_set_text(dmm_lbl, "12.4");
        lv_obj_set_style_text_color(dmm_lbl, lv_color_hex(0xF8FAFC), 0);
        lv_obj_set_style_text_font(dmm_lbl, &lv_font_montserrat_14, 0);
        lv_obj_align(dmm_lbl, LV_ALIGN_CENTER, 0, 2);

        // 5. Rotary Dial (lower half)
        lv_obj_t *dmm_dial = lv_obj_create(dmm_body);
        lv_obj_set_size(dmm_dial, 18, 18);
        lv_obj_align(dmm_dial, LV_ALIGN_CENTER, 0, 10);
        lv_obj_set_style_bg_color(dmm_dial, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_color(dmm_dial, lv_color_hex(0x1E293B), 0);
        lv_obj_set_style_border_width(dmm_dial, 2, 0);
        lv_obj_set_style_radius(dmm_dial, LV_RADIUS_CIRCLE, 0);
        lv_obj_set_style_pad_all(dmm_dial, 0, 0);
        lv_obj_remove_flag(dmm_dial, LV_OBJ_FLAG_SCROLLABLE);

        // Dial pointer
        lv_obj_t *dmm_pointer = lv_obj_create(dmm_dial);
        lv_obj_set_size(dmm_pointer, 2, 6);
        lv_obj_align(dmm_pointer, LV_ALIGN_TOP_MID, 0, 1);
        lv_obj_set_style_bg_color(dmm_pointer, lv_color_hex(0xF8FAFC), 0);
        lv_obj_set_style_border_width(dmm_pointer, 0, 0);

        // 6. Plugs at the bottom
        lv_obj_t *plug_red = lv_obj_create(dmm_body);
        lv_obj_set_size(plug_red, 4, 4);
        lv_obj_align(plug_red, LV_ALIGN_BOTTOM_RIGHT, -8, -4);
        lv_obj_set_style_bg_color(plug_red, lv_color_hex(0xEF4444), 0);
        lv_obj_set_style_border_width(plug_red, 0, 0);
        lv_obj_set_style_radius(plug_red, LV_RADIUS_CIRCLE, 0);

        lv_obj_t *plug_black = lv_obj_create(dmm_body);
        lv_obj_set_size(plug_black, 4, 4);
        lv_obj_align(plug_black, LV_ALIGN_BOTTOM_LEFT, 8, -4);
        lv_obj_set_style_bg_color(plug_black, lv_color_hex(0x1E293B), 0);
        lv_obj_set_style_border_width(plug_black, 0, 0);
        lv_obj_set_style_radius(plug_black, LV_RADIUS_CIRCLE, 0);

    } else if (strcmp(type, "gen") == 0) {
        // 1. GEN Chassis
        lv_obj_t *gen_body = lv_obj_create(card);
        lv_obj_set_size(gen_body, 64, 46);
        lv_obj_align(gen_body, LV_ALIGN_CENTER, 0, -6);
        lv_obj_set_style_bg_color(gen_body, lv_color_hex(0x94A3B8), 0);
        lv_obj_set_style_border_color(gen_body, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(gen_body, 2, 0);
        lv_obj_set_style_radius(gen_body, 6, 0);
        lv_obj_set_style_pad_all(gen_body, 0, 0);
        lv_obj_remove_flag(gen_body, LV_OBJ_FLAG_SCROLLABLE);

        // 2. Screen (left side)
        lv_obj_t *gen_screen = lv_obj_create(gen_body);
        lv_obj_set_size(gen_screen, 32, 24);
        lv_obj_align(gen_screen, LV_ALIGN_LEFT_MID, 4, -4);
        lv_obj_set_style_bg_color(gen_screen, lv_color_hex(0x0F172A), 0);
        lv_obj_set_style_border_color(gen_screen, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(gen_screen, 1, 0);
        lv_obj_set_style_radius(gen_screen, 2, 0);
        lv_obj_set_style_pad_all(gen_screen, 0, 0);
        lv_obj_remove_flag(gen_screen, LV_OBJ_FLAG_SCROLLABLE);

        // Wave points (Cyan wave)
        static lv_point_precise_t gen_points[] = {
            {2, 12}, {7, 5}, {12, 12}, {17, 19}, {22, 12}, {27, 5}, {30, 12}
        };
        lv_obj_t *gen_wave = lv_line_create(gen_screen);
        lv_line_set_points(gen_wave, gen_points, 7);
        lv_obj_set_style_line_color(gen_wave, lv_color_hex(0x06B6D4), 0);
        lv_obj_set_style_line_width(gen_wave, 2, 0);

        // 3. Keyboard buttons
        lv_obj_t *gen_key1 = lv_obj_create(gen_body);
        lv_obj_set_size(gen_key1, 8, 4);
        lv_obj_align(gen_key1, LV_ALIGN_BOTTOM_LEFT, 4, -6);
        lv_obj_set_style_bg_color(gen_key1, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(gen_key1, 0, 0);

        lv_obj_t *gen_key2 = lv_obj_create(gen_body);
        lv_obj_set_size(gen_key2, 8, 4);
        lv_obj_align(gen_key2, LV_ALIGN_BOTTOM_LEFT, 14, -6);
        lv_obj_set_style_bg_color(gen_key2, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(gen_key2, 0, 0);

        lv_obj_t *gen_key3 = lv_obj_create(gen_body);
        lv_obj_set_size(gen_key3, 8, 4);
        lv_obj_align(gen_key3, LV_ALIGN_BOTTOM_LEFT, 24, -6);
        lv_obj_set_style_bg_color(gen_key3, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(gen_key3, 0, 0);

        // 4. Large Knob
        lv_obj_t *gen_knob = lv_obj_create(gen_body);
        lv_obj_set_size(gen_knob, 16, 16);
        lv_obj_align(gen_knob, LV_ALIGN_RIGHT_MID, -6, -4);
        lv_obj_set_style_bg_color(gen_knob, lv_color_hex(0x64748B), 0);
        lv_obj_set_style_border_color(gen_knob, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(gen_knob, 2, 0);
        lv_obj_set_style_radius(gen_knob, LV_RADIUS_CIRCLE, 0);
        lv_obj_set_style_pad_all(gen_knob, 0, 0);
        lv_obj_remove_flag(gen_knob, LV_OBJ_FLAG_SCROLLABLE);

        lv_obj_t *gen_knob_dot = lv_obj_create(gen_knob);
        lv_obj_set_size(gen_knob_dot, 3, 3);
        lv_obj_align(gen_knob_dot, LV_ALIGN_TOP_MID, 0, 1);
        lv_obj_set_style_bg_color(gen_knob_dot, lv_color_hex(0xF8FAFC), 0);
        lv_obj_set_style_border_width(gen_knob_dot, 0, 0);
        lv_obj_set_style_radius(gen_knob_dot, LV_RADIUS_CIRCLE, 0);

        // numeric pad
        lv_obj_t *gen_numpad = lv_obj_create(gen_body);
        lv_obj_set_size(gen_numpad, 16, 10);
        lv_obj_align(gen_numpad, LV_ALIGN_BOTTOM_RIGHT, -6, -6);
        lv_obj_set_style_bg_color(gen_numpad, lv_color_hex(0x475569), 0);
        lv_obj_set_style_border_width(gen_numpad, 0, 0);
        lv_obj_set_style_radius(gen_numpad, 2, 0);

    } else if (strcmp(type, "view") == 0) {
        // 1. Grid screen frame
        lv_obj_t *view_screen = lv_obj_create(card);
        lv_obj_set_size(view_screen, 54, 46);
        lv_obj_align(view_screen, LV_ALIGN_CENTER, 0, -6);
        lv_obj_set_style_bg_color(view_screen, lv_color_hex(0x0F172A), 0);
        lv_obj_set_style_border_color(view_screen, lv_color_hex(0x94A3B8), 0);
        lv_obj_set_style_border_width(view_screen, 2, 0);
        lv_obj_set_style_radius(view_screen, 4, 0);
        lv_obj_set_style_pad_all(view_screen, 0, 0);
        lv_obj_remove_flag(view_screen, LV_OBJ_FLAG_SCROLLABLE);

        // 2. Division lines
        lv_obj_t *div_h = lv_obj_create(view_screen);
        lv_obj_set_size(div_h, 54, 1);
        lv_obj_align(div_h, LV_ALIGN_CENTER, 0, 0);
        lv_obj_set_style_bg_color(div_h, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(div_h, 0, 0);

        lv_obj_t *div_v = lv_obj_create(view_screen);
        lv_obj_set_size(div_v, 1, 46);
        lv_obj_align(div_v, LV_ALIGN_CENTER, 0, 0);
        lv_obj_set_style_bg_color(div_v, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(div_v, 0, 0);

        // Q1: Sine wave (Yellow)
        static lv_point_precise_t q1_pts[] = {
            {2, 11}, {6, 4}, {11, 11}, {16, 18}, {20, 11}, {24, 11}
        };
        lv_obj_t *q1_wave = lv_line_create(view_screen);
        lv_line_set_points(q1_wave, q1_pts, 6);
        lv_obj_set_style_line_color(q1_wave, lv_color_hex(0xEAB308), 0);
        lv_obj_set_style_line_width(q1_wave, 2, 0);
        lv_obj_align(q1_wave, LV_ALIGN_TOP_LEFT, 0, 0);

        // Q2: Square wave (Cyan)
        static lv_point_precise_t q2_pts[] = {
            {2, 15}, {2, 5}, {12, 5}, {12, 15}, {22, 15}, {22, 5}
        };
        lv_obj_t *q2_wave = lv_line_create(view_screen);
        lv_line_set_points(q2_wave, q2_pts, 6);
        lv_obj_set_style_line_color(q2_wave, lv_color_hex(0x06B6D4), 0);
        lv_obj_set_style_line_width(q2_wave, 2, 0);
        lv_obj_align(q2_wave, LV_ALIGN_TOP_RIGHT, 0, 0);

        // Q3: Triangle wave (Green)
        static lv_point_precise_t q3_pts[] = {
            {2, 18}, {8, 4}, {14, 18}, {20, 4}, {24, 18}
        };
        lv_obj_t *q3_wave = lv_line_create(view_screen);
        lv_line_set_points(q3_wave, q3_pts, 5);
        lv_obj_set_style_line_color(q3_wave, lv_color_hex(0x10B981), 0);
        lv_obj_set_style_line_width(q3_wave, 2, 0);
        lv_obj_align(q3_wave, LV_ALIGN_BOTTOM_LEFT, 0, 0);

        // Q4: Sawtooth/Noise (Rose)
        static lv_point_precise_t q4_pts[] = {
            {2, 18}, {10, 4}, {10, 18}, {18, 4}, {18, 18}, {22, 10}
        };
        lv_obj_t *q4_wave = lv_line_create(view_screen);
        lv_line_set_points(q4_wave, q4_pts, 6);
        lv_obj_set_style_line_color(q4_wave, lv_color_hex(0xF43F5E), 0);
        lv_obj_set_style_line_width(q4_wave, 2, 0);
        lv_obj_align(q4_wave, LV_ALIGN_BOTTOM_RIGHT, 0, 0);

    } else if (strcmp(type, "person") == 0) {
        // Container
        lv_obj_t *p_container = lv_obj_create(card);
        lv_obj_set_size(p_container, 50, 50);
        lv_obj_align(p_container, LV_ALIGN_CENTER, 0, -6);
        lv_obj_set_style_bg_opa(p_container, LV_OPA_TRANSP, 0);
        lv_obj_set_style_border_width(p_container, 0, 0);
        lv_obj_set_style_pad_all(p_container, 0, 0);
        lv_obj_remove_flag(p_container, LV_OBJ_FLAG_SCROLLABLE);

        // Head
        lv_obj_t *head = lv_obj_create(p_container);
        lv_obj_set_size(head, 18, 18);
        lv_obj_align(head, LV_ALIGN_TOP_MID, 0, 4);
        lv_obj_set_style_bg_color(head, lv_color_hex(0xE2E8F0), 0);
        lv_obj_set_style_border_width(head, 0, 0);
        lv_obj_set_style_radius(head, LV_RADIUS_CIRCLE, 0);

        // Shoulders
        lv_obj_t *shoulders = lv_obj_create(p_container);
        lv_obj_set_size(shoulders, 34, 18);
        lv_obj_align(shoulders, LV_ALIGN_BOTTOM_MID, 0, -4);
        lv_obj_set_style_bg_color(shoulders, lv_color_hex(0xE2E8F0), 0);
        lv_obj_set_style_border_width(shoulders, 0, 0);
        lv_obj_set_style_radius(shoulders, 8, 0);
    } else if (strcmp(type, "connectivity") == 0) {
        // Router body
        lv_obj_t *router_body = lv_obj_create(card);
        lv_obj_set_size(router_body, 48, 16);
        lv_obj_align(router_body, LV_ALIGN_CENTER, 0, 8);
        lv_obj_set_style_bg_color(router_body, lv_color_hex(0x94A3B8), 0);
        lv_obj_set_style_border_color(router_body, lv_color_hex(0x334155), 0);
        lv_obj_set_style_border_width(router_body, 2, 0);
        lv_obj_set_style_radius(router_body, 4, 0);
        lv_obj_set_style_pad_all(router_body, 0, 0);
        lv_obj_remove_flag(router_body, LV_OBJ_FLAG_SCROLLABLE);

        // Router LEDs (3 tiny dots)
        for (int i = 0; i < 3; i++) {
            lv_obj_t *led = lv_obj_create(router_body);
            lv_obj_set_size(led, 4, 4);
            lv_obj_align(led, LV_ALIGN_LEFT_MID, 6 + i * 8, 0);
            lv_obj_set_style_bg_color(led, lv_color_hex(0x06B6D4), 0);
            lv_obj_set_style_border_width(led, 0, 0);
            lv_obj_set_style_radius(led, LV_RADIUS_CIRCLE, 0);
        }

        // Antennas (2 lines going up)
        static lv_point_precise_t ant1_pts[] = {{0, 0}, {0, -18}};
        lv_obj_t *ant1 = lv_line_create(card);
        lv_line_set_points(ant1, ant1_pts, 2);
        lv_obj_set_style_line_color(ant1, lv_color_hex(0x475569), 0);
        lv_obj_set_style_line_width(ant1, 3, 0);
        lv_obj_align(ant1, LV_ALIGN_CENTER, -14, -6);

        static lv_point_precise_t ant2_pts[] = {{0, 0}, {0, -18}};
        lv_obj_t *ant2 = lv_line_create(card);
        lv_line_set_points(ant2, ant2_pts, 2);
        lv_obj_set_style_line_color(ant2, lv_color_hex(0x475569), 0);
        lv_obj_set_style_line_width(ant2, 3, 0);
        lv_obj_align(ant2, LV_ALIGN_CENTER, 14, -6);

        // Wi-Fi signal waves at the top
        static lv_point_precise_t wave_pts[] = {{0, 8}, {8, 0}, {16, 8}};
        lv_obj_t *wave1 = lv_line_create(card);
        lv_line_set_points(wave1, wave_pts, 3);
        lv_obj_set_style_line_color(wave1, lv_color_hex(0x38BDF8), 0);
        lv_obj_set_style_line_width(wave1, 2, 0);
        lv_obj_align(wave1, LV_ALIGN_CENTER, 0, -14);
    }

    // Label outside the button
    lv_obj_t *txt_lbl = lv_label_create(active_screen_container);
    lv_label_set_text(txt_lbl, btn_info.label);
    lv_obj_set_style_text_color(txt_lbl, get_current_text_color(), 0);
    lv_obj_set_style_text_font(txt_lbl, &lv_font_montserrat_14, 0);
    lv_obj_align_to(txt_lbl, card, LV_ALIGN_OUT_BOTTOM_MID, 0, 8);

    // Make all children of card click-through so the card handles the click event
    make_descendants_click_through(card);
}

void populate_home_ui(void) {
  // Remove scrollable flag from active container
  lv_obj_remove_flag(active_screen_container, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *title_bar = lv_obj_create(active_screen_container);
  lv_obj_set_size(title_bar, 480, 32);
  lv_obj_set_pos(title_bar, 0, 0);
  lv_obj_set_style_bg_color(title_bar, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(title_bar, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(title_bar, 1, 0);
  lv_obj_set_style_border_side(title_bar, LV_BORDER_SIDE_BOTTOM, 0);
  lv_obj_set_style_radius(title_bar, 0, 0);
  lv_obj_set_style_pad_all(title_bar, 0, 0);
  lv_obj_remove_flag(title_bar, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *title_lbl = lv_label_create(title_bar);
  lv_label_set_text(title_lbl, "HOME");
  lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(title_lbl, &lv_font_montserrat_14, 0);
  lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

  sHomeBtn buttons[] = {
      {"OSCOPE", "oscope", SCREEN_OSCOPE},
      {"DMM", "dmm", SCREEN_DMM},
      {"GEN", "gen", SCREEN_GEN},
      {"View", "view", SCREEN_VIEW},
      {"Person", "person", SCREEN_PERSON},
      {"CONECT", "connectivity", SCREEN_CONNECTIVITY}
  };

  // Row 1: OSCOPE, DMM, GEN
  create_home_card(buttons[0], 60, 55);
  create_home_card(buttons[1], 200, 55);
  create_home_card(buttons[2], 340, 55);

  // Row 2: View, Person, Conectivity
  create_home_card(buttons[3], 60, 175);
  create_home_card(buttons[4], 200, 175);
  create_home_card(buttons[5], 340, 175);
}
