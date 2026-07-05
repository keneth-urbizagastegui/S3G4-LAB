#include "ui_person.h"
#include "ui_common.h"
#include "hal_display.h"
#include <lvgl.h>

static void make_descendants_click_through(lv_obj_t *obj) {
    if (!obj) return;
    uint32_t cnt = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(obj, i);
        lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
        make_descendants_click_through(child);
    }
}

static void opt_grid_type_cb(lv_event_t *e) {
    int val = (int)(uintptr_t)lv_event_get_user_data(e);
    opt_grid_type = val;
    transition_to_screen(SCREEN_PERSON);
}

static void opt_grid_intensity_cb(lv_event_t *e) {
    int val = (int)(uintptr_t)lv_event_get_user_data(e);
    opt_grid_intensity = val;
    transition_to_screen(SCREEN_PERSON);
}

static void opt_ch_color_cb(lv_event_t *e) {
    int ch = (int)(uintptr_t)lv_event_get_user_data(e);
    if (ch == 0) opt_ch1_color = (opt_ch1_color + 1) % 5;
    else if (ch == 1) opt_ch2_color = (opt_ch2_color + 1) % 5;
    else if (ch == 2) opt_ch3_color = (opt_ch3_color + 1) % 5;
    else if (ch == 3) opt_ch4_color = (opt_ch4_color + 1) % 5;
    transition_to_screen(SCREEN_PERSON);
}

static void opt_dmm_mode_cb(lv_event_t *e) {
    int val = (int)(uintptr_t)lv_event_get_user_data(e);
    opt_dmm_mode = val;
    transition_to_screen(SCREEN_PERSON);
}

static void opt_disp_inver_cb(lv_event_t *e) {
    int val = (int)(uintptr_t)lv_event_get_user_data(e);
    opt_disp_inver = (val != 0);
    update_display_inversion();
    transition_to_screen(SCREEN_PERSON);
}

static void opt_theme_cb(lv_event_t *e) {
    int idx = (int)(uintptr_t)lv_event_get_user_data(e);
    opt_theme_idx = idx;
    transition_to_screen(SCREEN_PERSON);
}

void populate_person_ui(void) {
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

  // Home Button as a Rectangular Button (46x26) with standard LVGL Home Symbol
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

  // Centered LVGL Font Awesome Home Symbol inside the button
  lv_obj_t *lbl_home_icon = lv_label_create(btn_home);
  lv_label_set_text(lbl_home_icon, LV_SYMBOL_HOME);
  lv_obj_set_style_text_color(lbl_home_icon, lv_color_white(), 0);
  lv_obj_set_style_text_font(lbl_home_icon, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_home_icon);

  make_descendants_click_through(btn_home);

  lv_obj_t *title_lbl = lv_label_create(title_bar);
  lv_label_set_text(title_lbl, "PERSONALIZATION");
  lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(title_lbl, &lv_font_montserrat_14, 0);
  lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

  // Left Panel: Grid & Wave Colors (Height 210px)
  lv_obj_t *left_panel = lv_obj_create(active_screen_container);
  lv_obj_set_size(left_panel, 225, 210);
  lv_obj_set_pos(left_panel, 10, 42);
  lv_obj_set_style_bg_color(left_panel, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(left_panel, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(left_panel, 1, 0);
  lv_obj_set_style_radius(left_panel, 8, 0);
  lv_obj_set_style_pad_all(left_panel, 10, 0);
  lv_obj_remove_flag(left_panel, LV_OBJ_FLAG_SCROLLABLE);

  // 1. Grid Type
  lv_obj_t *lbl_gtype = lv_label_create(left_panel);
  lv_label_set_text(lbl_gtype, "Grid Type:");
  lv_obj_set_style_text_color(lbl_gtype, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_gtype, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_gtype, LV_ALIGN_TOP_LEFT, 0, 10);

  const char *gtypes[] = {"Dot", "Line", "None"};
  for (int i = 0; i < 3; i++) {
      lv_obj_t *cb = lv_checkbox_create(left_panel);
      lv_checkbox_set_text(cb, gtypes[i]);
      // Use LV_SIZE_CONTENT to dynamically size and prevent any text cut-offs
      lv_obj_set_size(cb, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
      lv_obj_align(cb, LV_ALIGN_TOP_LEFT, i * 70, 28);
      lv_obj_set_style_text_color(cb, get_current_text_color(), 0);
      lv_obj_set_style_text_font(cb, &lv_font_montserrat_14, 0);
      if (opt_grid_type == i) {
          lv_obj_add_state(cb, LV_STATE_CHECKED);
      }
      lv_obj_add_event_cb(cb, opt_grid_type_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
  }

  // 2. Grid Intensity
  lv_obj_t *lbl_gint = lv_label_create(left_panel);
  lv_label_set_text(lbl_gint, "Grid Intensity:");
  lv_obj_set_style_text_color(lbl_gint, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_gint, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_gint, LV_ALIGN_TOP_LEFT, 0, 75);

  const char *gints[] = {"Low", "Med", "High"};
  for (int i = 0; i < 3; i++) {
      lv_obj_t *cb = lv_checkbox_create(left_panel);
      lv_checkbox_set_text(cb, gints[i]);
      lv_obj_set_size(cb, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
      lv_obj_align(cb, LV_ALIGN_TOP_LEFT, i * 70, 93);
      lv_obj_set_style_text_color(cb, get_current_text_color(), 0);
      lv_obj_set_style_text_font(cb, &lv_font_montserrat_14, 0);
      if (opt_grid_intensity == i) {
          lv_obj_add_state(cb, LV_STATE_CHECKED);
      }
      lv_obj_add_event_cb(cb, opt_grid_intensity_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
  }

  // 3. Multi-Channel Wave Colors
  lv_obj_t *lbl_wave_colors = lv_label_create(left_panel);
  lv_label_set_text(lbl_wave_colors, "Wave Colors:");
  lv_obj_set_style_text_color(lbl_wave_colors, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_wave_colors, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_wave_colors, LV_ALIGN_TOP_LEFT, 0, 140);

  uint32_t wave_colors[] = {0xFFB700, 0x3FB950, 0x00EEFF, 0xE85AAD, 0xEEEEEE};
  int current_ch_colors[] = {opt_ch1_color, opt_ch2_color, opt_ch3_color, opt_ch4_color};
  const char *ch_labels[] = {"CH1", "CH2", "CH3", "CH4"};

  for (int i = 0; i < 4; i++) {
      int col_x = i * 51;
      lv_obj_t *lbl_ch = lv_label_create(left_panel);
      lv_label_set_text(lbl_ch, ch_labels[i]);
      lv_obj_set_style_text_color(lbl_ch, get_current_text_color(), 0);
      lv_obj_set_style_text_font(lbl_ch, &lv_font_montserrat_14, 0);
      lv_obj_align(lbl_ch, LV_ALIGN_TOP_LEFT, col_x, 155);

      lv_obj_t *btn_color = lv_button_create(left_panel);
      lv_obj_set_size(btn_color, 42, 22);
      lv_obj_align(btn_color, LV_ALIGN_TOP_LEFT, col_x, 172);
      lv_obj_set_style_bg_color(btn_color, lv_color_hex(wave_colors[current_ch_colors[i]]), 0);
      lv_obj_set_style_border_color(btn_color, lv_color_white(), 0);
      lv_obj_set_style_border_width(btn_color, 1, 0);
      lv_obj_set_style_radius(btn_color, 4, 0);
      lv_obj_remove_flag(btn_color, LV_OBJ_FLAG_SCROLLABLE);
      lv_obj_add_event_cb(btn_color, opt_ch_color_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
  }

  // Right Panel: Theme Selector, DMM & Inversion (Height 210px)
  lv_obj_t *right_panel = lv_obj_create(active_screen_container);
  lv_obj_set_size(right_panel, 225, 210);
  lv_obj_set_pos(right_panel, 245, 42);
  lv_obj_set_style_bg_color(right_panel, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(right_panel, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(right_panel, 1, 0);
  lv_obj_set_style_radius(right_panel, 8, 0);
  lv_obj_set_style_pad_all(right_panel, 10, 0);
  lv_obj_remove_flag(right_panel, LV_OBJ_FLAG_SCROLLABLE);

  // 1. Select Theme Palette (1x4 color circle picker)
  lv_obj_t *lbl_theme = lv_label_create(right_panel);
  lv_label_set_text(lbl_theme, "Select Color Theme:");
  lv_obj_set_style_text_color(lbl_theme, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_theme, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_theme, LV_ALIGN_TOP_LEFT, 0, 10);

  for (int i = 0; i < 4; i++) {
      lv_obj_t *btn = lv_button_create(right_panel);
      lv_obj_set_size(btn, 32, 32);
      lv_obj_set_pos(btn, i * 48, 28);
      lv_obj_set_style_bg_color(btn, lv_color_hex(themes[i].bg_color), 0);
      lv_obj_set_style_radius(btn, LV_RADIUS_CIRCLE, 0);
      lv_obj_remove_flag(btn, LV_OBJ_FLAG_SCROLLABLE);
      lv_obj_add_event_cb(btn, opt_theme_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
      
      if (opt_theme_idx == i) {
          lv_obj_set_style_border_color(btn, lv_color_hex(themes[i].accent_color), 0);
          lv_obj_set_style_border_width(btn, 3, 0);
          
          lv_obj_t *dot = lv_obj_create(btn);
          lv_obj_set_size(dot, 8, 8);
          lv_obj_align(dot, LV_ALIGN_CENTER, 0, 0);
          lv_obj_set_style_bg_color(dot, lv_color_hex(themes[i].accent_color), 0);
          lv_obj_set_style_border_width(dot, 0, 0);
          lv_obj_set_style_radius(dot, LV_RADIUS_CIRCLE, 0);
          lv_obj_remove_flag(dot, LV_OBJ_FLAG_SCROLLABLE);
      } else {
          lv_obj_set_style_border_color(btn, lv_color_hex(themes[i].accent_color), 0);
          lv_obj_set_style_border_width(btn, 1, 0);
      }
      
      make_descendants_click_through(btn);
  }

  // 2. DMM Window Mode
  lv_obj_t *lbl_dmm = lv_label_create(right_panel);
  lv_label_set_text(lbl_dmm, "DMM Window Mode:");
  lv_obj_set_style_text_color(lbl_dmm, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_dmm, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_dmm, LV_ALIGN_TOP_LEFT, 0, 75);

  const char *dmm_modes[] = {"Small Win", "Full Screen"};
  for (int i = 0; i < 2; i++) {
      lv_obj_t *cb = lv_checkbox_create(right_panel);
      lv_checkbox_set_text(cb, dmm_modes[i]);
      lv_obj_set_size(cb, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
      lv_obj_align(cb, LV_ALIGN_TOP_LEFT, i * 105, 93);
      lv_obj_set_style_text_color(cb, get_current_text_color(), 0);
      lv_obj_set_style_text_font(cb, &lv_font_montserrat_14, 0);
      if (opt_dmm_mode == i) {
          lv_obj_add_state(cb, LV_STATE_CHECKED);
      }
      lv_obj_add_event_cb(cb, opt_dmm_mode_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
  }

  // 3. Display Inversion
  lv_obj_t *lbl_inver = lv_label_create(right_panel);
  lv_label_set_text(lbl_inver, "Display Inversion:");
  lv_obj_set_style_text_color(lbl_inver, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_inver, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_inver, LV_ALIGN_TOP_LEFT, 0, 140);

  const char *inver_modes[] = {"OFF", "ON"};
  for (int i = 0; i < 2; i++) {
      lv_obj_t *cb = lv_checkbox_create(right_panel);
      lv_checkbox_set_text(cb, inver_modes[i]);
      lv_obj_set_size(cb, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
      lv_obj_align(cb, LV_ALIGN_TOP_LEFT, i * 90, 158);
      lv_obj_set_style_text_color(cb, get_current_text_color(), 0);
      lv_obj_set_style_text_font(cb, &lv_font_montserrat_14, 0);
      if (opt_disp_inver == (i != 0)) {
          lv_obj_add_state(cb, LV_STATE_CHECKED);
      }
      lv_obj_add_event_cb(cb, opt_disp_inver_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
  }
}
