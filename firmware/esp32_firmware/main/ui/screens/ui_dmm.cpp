#include "ui_dmm.h"
#include "ui_common.h"
#include <lvgl.h>
#include <stdlib.h>

lv_timer_t *dmm_update_timer = NULL;

static void make_descendants_click_through(lv_obj_t *obj) {
    if (!obj) return;
    uint32_t cnt = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(obj, i);
        lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
        make_descendants_click_through(child);
    }
}

static void dmm_timer_cb(lv_timer_t *timer) {
    if (lbl_dmm_val) {
        static float base_volts = 1.652f;
        float fluctuation = ((float)(rand() % 20) - 10) / 1000.0f;
        float current_val = base_volts + fluctuation;
        lv_label_set_text_fmt(lbl_dmm_val, "%d.%03d V", (int)current_val, (int)((current_val - (int)current_val) * 1000));
    }
}

void populate_dmm_ui(void) {
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

  lv_obj_t *btn_home = lv_button_create(title_bar);
  lv_obj_set_size(btn_home, 46, 26);
  lv_obj_align(btn_home, LV_ALIGN_LEFT_MID, 8, 0);
  lv_obj_set_style_bg_color(btn_home, get_current_panel_color(), 0);
  lv_obj_set_style_bg_color(btn_home, get_current_accent_color(), LV_STATE_PRESSED);
  lv_obj_set_style_border_color(btn_home, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(btn_home, 1, 0);
  lv_obj_set_style_radius(btn_home, 6, 0);
  lv_obj_set_style_pad_all(btn_home, 0, 0);
  lv_obj_remove_flag(btn_home, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_add_event_cb(btn_home, [](lv_event_t *e){ transition_to_screen(SCREEN_HOME); }, LV_EVENT_CLICKED, NULL);

  lv_obj_t *lbl_home_icon = lv_label_create(btn_home);
  lv_label_set_text(lbl_home_icon, LV_SYMBOL_HOME);
  lv_obj_set_style_text_color(lbl_home_icon, lv_color_white(), 0);
  lv_obj_set_style_text_font(lbl_home_icon, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_home_icon);

  make_descendants_click_through(btn_home);

  lv_obj_t *title_lbl = lv_label_create(title_bar);
  lv_label_set_text(title_lbl, "DMM MULTIMETER");
  lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
  lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

  lv_obj_t *dmm_panel = lv_obj_create(active_screen_container);
  if (opt_dmm_mode == 0) {
      lv_obj_set_size(dmm_panel, 340, 230);
      lv_obj_align(dmm_panel, LV_ALIGN_CENTER, 0, 20);
  } else {
      lv_obj_set_size(dmm_panel, 460, 260);
      lv_obj_align(dmm_panel, LV_ALIGN_CENTER, 0, 20);
  }
  lv_obj_set_style_bg_color(dmm_panel, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(dmm_panel, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(dmm_panel, 2, 0);
  lv_obj_set_style_radius(dmm_panel, 12, 0);
  lv_obj_set_style_pad_all(dmm_panel, 15, 0);

  lv_obj_t *display_box = lv_obj_create(dmm_panel);
  lv_obj_set_size(display_box, opt_dmm_mode == 0 ? 300 : 400, 80);
  lv_obj_align(display_box, LV_ALIGN_TOP_MID, 0, 0);
  lv_obj_set_style_bg_color(display_box, get_current_bg_color(), 0);
  lv_obj_set_style_border_color(display_box, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(display_box, 1, 0);
  lv_obj_set_style_radius(display_box, 8, 0);

  lbl_dmm_val = lv_label_create(display_box);
  lv_label_set_text(lbl_dmm_val, "1.652 V");
  lv_obj_set_style_text_color(lbl_dmm_val, lv_color_hex(0xFFB700), 0);
  lv_obj_set_style_text_font(lbl_dmm_val, &lv_font_montserrat_28, 0);
  lv_obj_align(lbl_dmm_val, LV_ALIGN_CENTER, 0, -5);

  lv_obj_t *lbl_unit = lv_label_create(display_box);
  lv_label_set_text(lbl_unit, "DC  Auto-Range");
  lv_obj_set_style_text_color(lbl_unit, lv_color_hex(0x8B949E), 0);
  lv_obj_set_style_text_font(lbl_unit, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_unit, LV_ALIGN_BOTTOM_MID, 0, -2);

  lv_obj_t *funny_box = lv_obj_create(dmm_panel);
  lv_obj_set_size(funny_box, opt_dmm_mode == 0 ? 300 : 400, 80);
  lv_obj_align(funny_box, LV_ALIGN_BOTTOM_MID, 0, 0);
  lv_obj_set_style_bg_color(funny_box, get_current_panel_color(), 0);
  lv_obj_set_style_border_width(funny_box, 0, 0);
  lv_obj_set_style_pad_all(funny_box, 0, 0);

  lv_obj_t *spinner = lv_spinner_create(funny_box);
  lv_obj_set_size(spinner, 40, 40);
  lv_obj_align(spinner, LV_ALIGN_LEFT_MID, 10, 0);
  lv_obj_set_style_arc_color(spinner, get_current_accent_color(), LV_PART_INDICATOR);
  lv_obj_set_style_arc_color(spinner, lv_color_hex(0x30363D), LV_PART_MAIN);

  lv_obj_t *lbl_funny_msg = lv_label_create(funny_box);
  lv_label_set_text(lbl_funny_msg, "DMM Auto-Calibration Running...\n(G473 Coprocessor Integration)");
  lv_obj_set_style_text_color(lbl_funny_msg, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_funny_msg, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_funny_msg, LV_ALIGN_LEFT_MID, 65, 0);

  dmm_update_timer = lv_timer_create(dmm_timer_cb, 500, NULL);
}
