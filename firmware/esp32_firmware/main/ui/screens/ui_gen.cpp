#include "ui_gen.h"
#include "ui_common.h"
#include "comm_spi_master.h"
#include <lvgl.h>

LV_FONT_DECLARE(lv_font_montserrat_28);

static int gen_active_channel = 0; // 0 = CH1, 1 = CH2
static int gen_wave_type[2] = {0, 0}; // 0=Sine, 1=PWM, 2=Triangle, 3=Sawtooth, 4=Pulse, 5=FullRect, 6=Sinc, 7=Noise
static int gen_frequency[2] = {1000, 1000};
static int gen_amplitude[2] = {1551, 1551}; // Fixed at 1551 counts (2.5 V)
static int gen_duty_cycle[2] = {50, 50};
static bool gen_is_running[2] = {false, false};
static bool gen_is_khz[2] = {true, true}; // Default true since 1000Hz is 1.00kHz

static lv_obj_t *lbl_gen_freq = NULL;
static lv_obj_t *lbl_gen_amp = NULL;
static lv_obj_t *lbl_gen_duty = NULL;

static void make_descendants_click_through(lv_obj_t *obj) {
    if (!obj) return;
    uint32_t cnt = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(obj, i);
        lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
        make_descendants_click_through(child);
    }
}

static void sync_generator_settings(int channel) {
    if (gen_is_running[channel]) {
        comm_spi_master_send_cmd(CMD_WAVEGEN_CONFIG_HORIZ, channel, gen_frequency[channel]);
        uint32_t vert_data = (gen_wave_type[channel] & 0xFF) | 
                             ((gen_duty_cycle[channel] & 0xFF) << 8) | 
                             ((gen_amplitude[channel] & 0xFFFF) << 16);
        comm_spi_master_send_cmd(CMD_WAVEGEN_CONFIG_VERT, channel, vert_data);
        comm_spi_master_send_cmd(CMD_WAVEGEN_START, channel, 0);
    } else {
        comm_spi_master_send_cmd(CMD_WAVEGEN_STOP, channel, 0);
    }
}

static void gen_channel_change_cb(lv_event_t *e) {
    int ch = (int)(uintptr_t)lv_event_get_user_data(e);
    gen_active_channel = ch;
    transition_to_screen(SCREEN_GEN);
}

static void gen_toggle_cb(lv_event_t *e) {
    lv_obj_t *btn = (lv_obj_t *)lv_event_get_target(e);
    bool state = lv_obj_has_state(btn, LV_STATE_CHECKED);
    gen_is_running[gen_active_channel] = state;
    sync_generator_settings(gen_active_channel);
    transition_to_screen(SCREEN_GEN);
}

static int gen_selected_digit = 2; // 0=100k, 1=10k, 2=1k, 3=100h, 4=10h (in kHz) or 0=100, 1=10, 2=1 (in Hz)
static int gen_selected_duty_digit = 1; // 0=Tens, 1=Ones
static lv_obj_t *lbl_digits[5] = {NULL, NULL, NULL, NULL, NULL};

static void gen_unit_hz_cb(lv_event_t *e) {
    int channel = gen_active_channel;
    if (gen_is_khz[channel]) {
        gen_is_khz[channel] = false;
        if (gen_frequency[channel] >= 1000) {
            gen_frequency[channel] = 999;
        }
        if (gen_selected_digit > 2) {
            gen_selected_digit = 2;
        }
        sync_generator_settings(channel);
        transition_to_screen(SCREEN_GEN);
    }
}

static void gen_unit_khz_cb(lv_event_t *e) {
    int channel = gen_active_channel;
    if (!gen_is_khz[channel]) {
        gen_is_khz[channel] = true;
        if (gen_frequency[channel] < 1000) {
            gen_frequency[channel] = 1000;
        }
        sync_generator_settings(channel);
        transition_to_screen(SCREEN_GEN);
    }
}

static void gen_freq_step_cb(lv_event_t *e) {
    int direction = (int)(uintptr_t)lv_event_get_user_data(e); // -1 or +1
    int weight = 0;
    bool is_khz = gen_is_khz[gen_active_channel];
    if (is_khz) {
        if (gen_selected_digit == 0) weight = 100000;
        else if (gen_selected_digit == 1) weight = 10000;
        else if (gen_selected_digit == 2) weight = 1000;
        else if (gen_selected_digit == 3) weight = 100;
        else if (gen_selected_digit == 4) weight = 10;
    } else {
        if (gen_selected_digit == 0) weight = 100;
        else if (gen_selected_digit == 1) weight = 10;
        else if (gen_selected_digit == 2) weight = 1;
    }
    
    if (weight == 0) return;

    int new_val = gen_frequency[gen_active_channel] + direction * weight;
    if (!is_khz) {
        if (new_val > 999) {
            gen_is_khz[gen_active_channel] = true;
            new_val = 1000;
        } else if (new_val < 10) {
            new_val = 10;
        }
    } else {
        if (new_val < 1000) {
            gen_is_khz[gen_active_channel] = false;
            if (new_val < 10) new_val = 10;
            if (gen_selected_digit > 2) gen_selected_digit = 2;
        } else if (new_val > 50000) {
            new_val = 50000;
        }
    }
    
    gen_frequency[gen_active_channel] = new_val;
    sync_generator_settings(gen_active_channel);
    transition_to_screen(SCREEN_GEN);
}

static void gen_duty_step_cb(lv_event_t *e) {
    int direction = (int)(uintptr_t)lv_event_get_user_data(e); // -1 or +1
    int weight = (gen_selected_duty_digit == 0) ? 10 : 1;
    int new_val = gen_duty_cycle[gen_active_channel] + direction * weight;
    if (new_val < 10) new_val = 10;
    if (new_val > 90) new_val = 90;
    gen_duty_cycle[gen_active_channel] = new_val;
    sync_generator_settings(gen_active_channel);
    transition_to_screen(SCREEN_GEN);
}

void populate_gen_ui(void) {
  // Clear local dynamic pointers
  lbl_gen_freq = NULL;
  lbl_gen_amp = NULL;
  lbl_gen_duty = NULL;
  for (int d = 0; d < 5; d++) {
      lbl_digits[d] = NULL;
  }

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
  lv_label_set_text(title_lbl, "SIGNAL GENERATOR");
  lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(title_lbl, &lv_font_montserrat_14, 0);
  lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

  lv_obj_t *tab_panel = lv_obj_create(active_screen_container);
  lv_obj_set_size(tab_panel, 200, 36);
  lv_obj_align(tab_panel, LV_ALIGN_TOP_MID, 0, 38);
  lv_obj_set_style_bg_color(tab_panel, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(tab_panel, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(tab_panel, 1, 0);
  lv_obj_set_style_radius(tab_panel, 6, 0);
  lv_obj_set_style_pad_all(tab_panel, 0, 0);

  for (int i = 0; i < 2; i++) {
      lv_obj_t *btn_tab = lv_button_create(tab_panel);
      lv_obj_set_size(btn_tab, 95, 30);
      lv_obj_align(btn_tab, i == 0 ? LV_ALIGN_LEFT_MID : LV_ALIGN_RIGHT_MID, i == 0 ? 2 : -2, 0);
      
      if (gen_active_channel == i) {
          lv_obj_set_style_bg_color(btn_tab, get_current_accent_color(), 0);
      } else {
          lv_obj_set_style_bg_color(btn_tab, get_current_panel_color(), 0);
          lv_obj_set_style_border_width(btn_tab, 0, 0);
      }
      lv_obj_set_style_radius(btn_tab, 4, 0);
      lv_obj_add_event_cb(btn_tab, gen_channel_change_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);

      lv_obj_t *lbl_tab = lv_label_create(btn_tab);
      lv_label_set_text_fmt(lbl_tab, "CH %d", i + 1);
      if (gen_active_channel == i) {
          lv_obj_set_style_text_color(lbl_tab, lv_color_hex(0x000000), 0);
      } else {
          lv_obj_set_style_text_color(lbl_tab, get_current_text_color(), 0);
      }
      lv_obj_center(lbl_tab);
      make_descendants_click_through(btn_tab);
  }

  lv_obj_t *left_col = lv_obj_create(active_screen_container);
  lv_obj_set_size(left_col, 160, 220);
  lv_obj_set_pos(left_col, 10, 85);
  lv_obj_set_style_bg_color(left_col, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(left_col, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(left_col, 1, 0);
  lv_obj_set_style_radius(left_col, 8, 0);
  lv_obj_set_style_pad_all(left_col, 0, 0);
  lv_obj_remove_flag(left_col, LV_OBJ_FLAG_SCROLLABLE);

  // 2x4 Grid of Waveform Selector Buttons
  for (int i = 0; i < 8; i++) {
      int row = i / 2;
      int col = i % 2;
      
      lv_obj_t *btn_type = lv_button_create(left_col);
      lv_obj_set_size(btn_type, 66, 32);
      lv_obj_set_pos(btn_type, 10 + col * 74, 10 + row * 36);
      lv_obj_remove_flag(btn_type, LV_OBJ_FLAG_SCROLLABLE);
      
      // Highlight if active
      if (gen_wave_type[gen_active_channel] == i) {
          lv_obj_set_style_bg_color(btn_type, get_current_accent_color(), 0);
      } else {
          lv_obj_set_style_bg_color(btn_type, get_current_panel_color(), 0);
          lv_obj_set_style_border_color(btn_type, get_current_text_color(), 0);
          lv_obj_set_style_border_opa(btn_type, LV_OPA_30, 0);
          lv_obj_set_style_border_width(btn_type, 1, 0);
      }
      lv_obj_set_style_radius(btn_type, 6, 0);
      lv_obj_set_style_pad_all(btn_type, 0, 0);
      
      // Add event callback
      lv_obj_add_event_cb(btn_type, [](lv_event_t *e) {
          int index = (int)(uintptr_t)lv_event_get_user_data(e);
          gen_wave_type[gen_active_channel] = index;
          sync_generator_settings(gen_active_channel);
          transition_to_screen(SCREEN_GEN);
      }, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
      
      // Draw the vector icon inside the button
      lv_obj_t *icon_line = lv_line_create(btn_type);
      
      static const lv_point_precise_t pts_sine[] = {
          {15, 16}, {20, 10}, {24, 7}, {28, 10}, {33, 16}, {38, 22}, {42, 25}, {46, 22}, {51, 16}
      };
      static const lv_point_precise_t pts_pwm[] = {
          {15, 22}, {24, 22}, {24, 10}, {34, 10}, {34, 22}, {44, 22}, {44, 10}, {51, 10}
      };
      static const lv_point_precise_t pts_tri[] = {
          {15, 22}, {24, 10}, {33, 22}, {42, 10}, {51, 22}
      };
      static const lv_point_precise_t pts_saw[] = {
          {15, 22}, {33, 10}, {33, 22}, {51, 10}, {51, 22}
      };
      static const lv_point_precise_t pts_pulse[] = {
          {15, 22}, {19, 14}, {24, 10}, {29, 14}, {33, 22}, {51, 22}
      };
      static const lv_point_precise_t pts_full_rect[] = {
          {15, 22}, {19, 14}, {24, 10}, {29, 14}, {33, 22}, {37, 14}, {42, 10}, {47, 14}, {51, 22}
      };
      static const lv_point_precise_t pts_sinc[] = {
          {15, 22}, {22, 22}, {24, 24}, {27, 20}, {29, 24}, {33, 10}, {37, 24}, {39, 20}, {42, 24}, {44, 22}, {51, 22}
      };
      static const lv_point_precise_t pts_noise[] = {
          {15, 22}, {17, 12}, {19, 24}, {21, 14}, {23, 20}, {25, 10}, {27, 22}, {29, 12}, {31, 25}, {33, 15}, {35, 20}, {37, 10}, {39, 24}, {41, 12}, {43, 22}, {45, 14}, {47, 20}, {49, 10}, {51, 22}
      };
      
      switch (i) {
          case 0: lv_line_set_points(icon_line, pts_sine, 9); break;
          case 1: lv_line_set_points(icon_line, pts_pwm, 8); break;
          case 2: lv_line_set_points(icon_line, pts_tri, 5); break;
          case 3: lv_line_set_points(icon_line, pts_saw, 5); break;
          case 4: lv_line_set_points(icon_line, pts_pulse, 6); break;
          case 5: lv_line_set_points(icon_line, pts_full_rect, 9); break;
          case 6: lv_line_set_points(icon_line, pts_sinc, 11); break;
          case 7: lv_line_set_points(icon_line, pts_noise, 19); break;
      }
      
      // Styling line colors (Sinc icon color matches the others now)
      if (gen_wave_type[gen_active_channel] == i) {
          lv_obj_set_style_line_color(icon_line, lv_color_black(), 0);
      } else {
          lv_obj_set_style_line_color(icon_line, get_current_accent_color(), 0);
      }
      lv_obj_set_style_line_width(icon_line, 2, 0);
      
      // Click through
      lv_obj_remove_flag(icon_line, LV_OBJ_FLAG_CLICKABLE);
      make_descendants_click_through(btn_type);
  }

  // Simplified Toggle Button (only ON/OFF text)
  lv_obj_t *btn_toggle = lv_button_create(left_col);
  lv_obj_set_size(btn_toggle, 140, 42);
  lv_obj_set_pos(btn_toggle, 10, 168);
  lv_obj_add_flag(btn_toggle, LV_OBJ_FLAG_CHECKABLE);
  
  lv_color_t toggle_color = gen_is_running[gen_active_channel] ? lv_color_hex(0x238636) : lv_color_hex(0xDA3637);
  if (gen_is_running[gen_active_channel]) {
      lv_obj_add_state(btn_toggle, LV_STATE_CHECKED);
  }
  
  lv_obj_set_style_bg_color(btn_toggle, toggle_color, LV_STATE_DEFAULT);
  lv_obj_set_style_bg_color(btn_toggle, toggle_color, LV_STATE_CHECKED);
  lv_obj_set_style_bg_color(btn_toggle, toggle_color, LV_STATE_PRESSED);
  lv_obj_set_style_bg_color(btn_toggle, toggle_color, LV_STATE_CHECKED | LV_STATE_PRESSED);
  
  lv_obj_set_style_radius(btn_toggle, 8, 0);
  lv_obj_add_event_cb(btn_toggle, gen_toggle_cb, LV_EVENT_CLICKED, NULL);

  lv_obj_t *lbl_toggle = lv_label_create(btn_toggle);
  lv_label_set_text(lbl_toggle, gen_is_running[gen_active_channel] ? "ON" : "OFF");
  lv_obj_set_style_text_color(lbl_toggle, lv_color_hex(0xFFFFFF), 0);
  lv_obj_set_style_text_font(lbl_toggle, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_toggle);

  make_descendants_click_through(btn_toggle);

  lv_obj_t *right_col = lv_obj_create(active_screen_container);
  lv_obj_set_size(right_col, 290, 220);
  lv_obj_set_pos(right_col, 180, 85);
  lv_obj_set_style_bg_color(right_col, get_current_panel_color(), 0);
  lv_obj_remove_flag(right_col, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_border_color(right_col, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(right_col, 1, 0);
  lv_obj_set_style_radius(right_col, 8, 0);
  lv_obj_set_style_pad_all(right_col, 10, 0);

  // Large Interactive Digit Selector for Frequency
  int freq = gen_frequency[gen_active_channel];
  bool is_khz = gen_is_khz[gen_active_channel];
  char digit_chars[5];
  
  if (is_khz) {
      digit_chars[0] = '0' + ((freq / 100000) % 10);
      digit_chars[1] = '0' + ((freq / 10000) % 10);
      digit_chars[2] = '0' + ((freq / 1000) % 10);
      digit_chars[3] = '0' + ((freq / 100) % 10);
      digit_chars[4] = '0' + ((freq / 10) % 10);
  } else {
      digit_chars[0] = '0' + ((freq / 100) % 10);
      digit_chars[1] = '0' + ((freq / 10) % 10);
      digit_chars[2] = '0' + (freq % 10);
      digit_chars[3] = '0';
      digit_chars[4] = '0';
  }

  for (int d = 0; d < 5; d++) {
      lv_obj_t *btn_digit = lv_button_create(right_col);
      int x_pos = 10 + d * 32;
      if (d >= 3) x_pos += 12; // Extra gap for dot
      lv_obj_set_pos(btn_digit, x_pos, 16);
      lv_obj_set_size(btn_digit, 32, 40);
      lv_obj_remove_flag(btn_digit, LV_OBJ_FLAG_SCROLLABLE);

      if (!is_khz && d >= 3) {
          lv_obj_add_state(btn_digit, LV_STATE_DISABLED);
          lv_obj_set_style_bg_color(btn_digit, get_current_panel_color(), 0);
          lv_obj_set_style_border_color(btn_digit, get_current_text_color(), 0);
          lv_obj_set_style_border_opa(btn_digit, LV_OPA_30, 0);
          lv_obj_set_style_border_width(btn_digit, 1, 0);
      } else {
          if (gen_selected_digit == d) {
              lv_obj_set_style_bg_color(btn_digit, get_current_accent_color(), 0);
              lv_obj_set_style_border_width(btn_digit, 0, 0);
          } else {
              lv_obj_set_style_bg_color(btn_digit, get_current_panel_color(), 0);
              lv_obj_set_style_border_color(btn_digit, get_current_text_color(), 0);
              lv_obj_set_style_border_opa(btn_digit, LV_OPA_30, 0);
              lv_obj_set_style_border_width(btn_digit, 1, 0);
          }
      }
      lv_obj_set_style_radius(btn_digit, 6, 0);
      lv_obj_set_style_pad_all(btn_digit, 0, 0);

      lbl_digits[d] = lv_label_create(btn_digit);
      char buf[2] = {digit_chars[d], '\0'};
      lv_label_set_text(lbl_digits[d], buf);

      if (!is_khz && d >= 3) {
          lv_obj_set_style_text_color(lbl_digits[d], get_current_text_color(), 0);
          lv_obj_set_style_text_opa(lbl_digits[d], LV_OPA_30, 0); // Faded unselected locked decimals
      } else {
          lv_obj_set_style_text_opa(lbl_digits[d], LV_OPA_100, 0);
          if (gen_selected_digit == d) {
              lv_obj_set_style_text_color(lbl_digits[d], lv_color_black(), 0); // Black text on active background
          } else {
              lv_obj_set_style_text_color(lbl_digits[d], get_current_text_color(), 0); // Adapts to theme
          }
      }
      lv_obj_set_style_text_font(lbl_digits[d], &lv_font_montserrat_28, 0);
      lv_obj_center(lbl_digits[d]);

      if (is_khz || d < 3) {
          lv_obj_add_event_cb(btn_digit, [](lv_event_t *ev) {
              int digit_idx = (int)(uintptr_t)lv_event_get_user_data(ev);
              gen_selected_digit = digit_idx;
              transition_to_screen(SCREEN_GEN);
          }, LV_EVENT_CLICKED, (void*)(uintptr_t)d);
      }

      make_descendants_click_through(btn_digit);
  }

  // Decimal separator dot
  lv_obj_t *lbl_dot = lv_label_create(right_col);
  lv_label_set_text(lbl_dot, ".");
  lv_obj_set_style_text_color(lbl_dot, get_current_text_color(), 0);
  if (is_khz) {
      lv_obj_set_style_text_opa(lbl_dot, LV_OPA_100, 0);
  } else {
      lv_obj_set_style_text_opa(lbl_dot, LV_OPA_30, 0);
  }
  lv_obj_set_style_text_font(lbl_dot, &lv_font_montserrat_28, 0);
  lv_obj_set_pos(lbl_dot, 106, 16);

  // Unit Hz Button
  lv_obj_t *btn_unit_hz = lv_button_create(right_col);
  lv_obj_set_size(btn_unit_hz, 48, 26);
  lv_obj_set_pos(btn_unit_hz, 220, 16);
  lv_obj_remove_flag(btn_unit_hz, LV_OBJ_FLAG_SCROLLABLE);

  // Unit kHz Button
  lv_obj_t *btn_unit_khz = lv_button_create(right_col);
  lv_obj_set_size(btn_unit_khz, 48, 26);
  lv_obj_set_pos(btn_unit_khz, 220, 46);
  lv_obj_remove_flag(btn_unit_khz, LV_OBJ_FLAG_SCROLLABLE);

  if (!is_khz) {
      lv_obj_set_style_bg_color(btn_unit_hz, get_current_accent_color(), 0);
      lv_obj_set_style_bg_color(btn_unit_khz, get_current_panel_color(), 0);
      lv_obj_set_style_border_color(btn_unit_khz, get_current_text_color(), 0);
      lv_obj_set_style_border_opa(btn_unit_khz, LV_OPA_30, 0);
      lv_obj_set_style_border_width(btn_unit_khz, 1, 0);
  } else {
      lv_obj_set_style_bg_color(btn_unit_khz, get_current_accent_color(), 0);
      lv_obj_set_style_bg_color(btn_unit_hz, get_current_panel_color(), 0);
      lv_obj_set_style_border_color(btn_unit_hz, get_current_text_color(), 0);
      lv_obj_set_style_border_opa(btn_unit_hz, LV_OPA_30, 0);
      lv_obj_set_style_border_width(btn_unit_hz, 1, 0);
  }
  lv_obj_set_style_radius(btn_unit_hz, 4, 0);
  lv_obj_set_style_radius(btn_unit_khz, 4, 0);
  lv_obj_set_style_pad_all(btn_unit_hz, 0, 0);
  lv_obj_set_style_pad_all(btn_unit_khz, 0, 0);

  lv_obj_t *lbl_unit_hz = lv_label_create(btn_unit_hz);
  lv_label_set_text(lbl_unit_hz, "Hz");
  lv_obj_set_style_text_font(lbl_unit_hz, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_color(lbl_unit_hz, !is_khz ? lv_color_black() : get_current_text_color(), 0);
  lv_obj_center(lbl_unit_hz);

  lv_obj_t *lbl_unit_khz = lv_label_create(btn_unit_khz);
  lv_label_set_text(lbl_unit_khz, "kHz");
  lv_obj_set_style_text_font(lbl_unit_khz, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_color(lbl_unit_khz, is_khz ? lv_color_black() : get_current_text_color(), 0);
  lv_obj_center(lbl_unit_khz);

  lv_obj_add_event_cb(btn_unit_hz, gen_unit_hz_cb, LV_EVENT_CLICKED, NULL);
  lv_obj_add_event_cb(btn_unit_khz, gen_unit_khz_cb, LV_EVENT_CLICKED, NULL);

  make_descendants_click_through(btn_unit_hz);
  make_descendants_click_through(btn_unit_khz);

  // Large Frequency + and - Step Buttons (size: 48x32px, located below digits)
  lv_obj_t *btn_freq_dec = lv_button_create(right_col);
  lv_obj_set_size(btn_freq_dec, 48, 32);
  lv_obj_set_pos(btn_freq_dec, 10, 64);
  lv_obj_remove_flag(btn_freq_dec, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_bg_color(btn_freq_dec, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(btn_freq_dec, get_current_text_color(), 0);
  lv_obj_set_style_border_opa(btn_freq_dec, LV_OPA_30, 0);
  lv_obj_set_style_border_width(btn_freq_dec, 1, 0);
  lv_obj_set_style_radius(btn_freq_dec, 6, 0);
  lv_obj_set_style_pad_all(btn_freq_dec, 0, 0);

  lv_obj_t *lbl_freq_dec = lv_label_create(btn_freq_dec);
  lv_label_set_text(lbl_freq_dec, "-");
  lv_obj_set_style_text_font(lbl_freq_dec, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_color(lbl_freq_dec, get_current_text_color(), 0);
  lv_obj_center(lbl_freq_dec);

  lv_obj_t *btn_freq_inc = lv_button_create(right_col);
  lv_obj_set_size(btn_freq_inc, 48, 32);
  lv_obj_set_pos(btn_freq_inc, 66, 64);
  lv_obj_remove_flag(btn_freq_inc, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_bg_color(btn_freq_inc, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(btn_freq_inc, get_current_text_color(), 0);
  lv_obj_set_style_border_opa(btn_freq_inc, LV_OPA_30, 0);
  lv_obj_set_style_border_width(btn_freq_inc, 1, 0);
  lv_obj_set_style_radius(btn_freq_inc, 6, 0);
  lv_obj_set_style_pad_all(btn_freq_inc, 0, 0);

  lv_obj_t *lbl_freq_inc = lv_label_create(btn_freq_inc);
  lv_label_set_text(lbl_freq_inc, "+");
  lv_obj_set_style_text_font(lbl_freq_inc, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_color(lbl_freq_inc, get_current_text_color(), 0);
  lv_obj_center(lbl_freq_inc);

  lv_obj_add_event_cb(btn_freq_dec, gen_freq_step_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)-1);
  lv_obj_add_event_cb(btn_freq_inc, gen_freq_step_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)1);

  make_descendants_click_through(btn_freq_dec);
  make_descendants_click_through(btn_freq_inc);

  // Duty Cycle controls (with + and - buttons for step adjustment)
  int duty = gen_duty_cycle[gen_active_channel];
  int duty_tens = (duty / 10) % 10;
  int duty_ones = duty % 10;

  LV_FONT_DECLARE(lv_font_montserrat_24);

  // Duty Tens digit (rounded container with selection-based highlight)
  lv_obj_t *btn_duty_d0 = lv_button_create(right_col);
  lv_obj_set_size(btn_duty_d0, 28, 38);
  lv_obj_set_pos(btn_duty_d0, 10, 120);
  lv_obj_remove_flag(btn_duty_d0, LV_OBJ_FLAG_SCROLLABLE);
  
  if (gen_selected_duty_digit == 0) {
      lv_obj_set_style_bg_color(btn_duty_d0, get_current_accent_color(), 0);
      lv_obj_set_style_border_width(btn_duty_d0, 0, 0);
  } else {
      lv_obj_set_style_bg_color(btn_duty_d0, get_current_panel_color(), 0);
      lv_obj_set_style_border_color(btn_duty_d0, get_current_text_color(), 0);
      lv_obj_set_style_border_opa(btn_duty_d0, LV_OPA_30, 0);
      lv_obj_set_style_border_width(btn_duty_d0, 1, 0);
  }
  lv_obj_set_style_radius(btn_duty_d0, 6, 0);
  lv_obj_set_style_pad_all(btn_duty_d0, 0, 0);

  lv_obj_t *lbl_duty_d0 = lv_label_create(btn_duty_d0);
  char buf_dt[2] = {(char)('0' + duty_tens), '\0'};
  lv_label_set_text(lbl_duty_d0, buf_dt);
  if (gen_selected_duty_digit == 0) {
      lv_obj_set_style_text_color(lbl_duty_d0, lv_color_black(), 0);
  } else {
      lv_obj_set_style_text_color(lbl_duty_d0, get_current_text_color(), 0);
  }
  lv_obj_set_style_text_font(lbl_duty_d0, &lv_font_montserrat_24, 0);
  lv_obj_center(lbl_duty_d0);
  
  lv_obj_add_event_cb(btn_duty_d0, [](lv_event_t *ev) {
      gen_selected_duty_digit = 0;
      transition_to_screen(SCREEN_GEN);
  }, LV_EVENT_CLICKED, NULL);
  make_descendants_click_through(btn_duty_d0);

  // Duty Ones digit (rounded container with selection-based highlight)
  lv_obj_t *btn_duty_d1 = lv_button_create(right_col);
  lv_obj_set_size(btn_duty_d1, 28, 38);
  lv_obj_set_pos(btn_duty_d1, 38, 120);
  lv_obj_remove_flag(btn_duty_d1, LV_OBJ_FLAG_SCROLLABLE);
  
  if (gen_selected_duty_digit == 1) {
      lv_obj_set_style_bg_color(btn_duty_d1, get_current_accent_color(), 0);
      lv_obj_set_style_border_width(btn_duty_d1, 0, 0);
  } else {
      lv_obj_set_style_bg_color(btn_duty_d1, get_current_panel_color(), 0);
      lv_obj_set_style_border_color(btn_duty_d1, get_current_text_color(), 0);
      lv_obj_set_style_border_opa(btn_duty_d1, LV_OPA_30, 0);
      lv_obj_set_style_border_width(btn_duty_d1, 1, 0);
  }
  lv_obj_set_style_radius(btn_duty_d1, 6, 0);
  lv_obj_set_style_pad_all(btn_duty_d1, 0, 0);

  lv_obj_t *lbl_duty_d1 = lv_label_create(btn_duty_d1);
  char buf_do[2] = {(char)('0' + duty_ones), '\0'};
  lv_label_set_text(lbl_duty_d1, buf_do);
  if (gen_selected_duty_digit == 1) {
      lv_obj_set_style_text_color(lbl_duty_d1, lv_color_black(), 0);
  } else {
      lv_obj_set_style_text_color(lbl_duty_d1, get_current_text_color(), 0);
  }
  lv_obj_set_style_text_font(lbl_duty_d1, &lv_font_montserrat_24, 0);
  lv_obj_center(lbl_duty_d1);
  
  lv_obj_add_event_cb(btn_duty_d1, [](lv_event_t *ev) {
      gen_selected_duty_digit = 1;
      transition_to_screen(SCREEN_GEN);
  }, LV_EVENT_CLICKED, NULL);
  make_descendants_click_through(btn_duty_d1);

  // % label
  lv_obj_t *lbl_duty_percent = lv_label_create(right_col);
  lv_label_set_text(lbl_duty_percent, "%");
  lv_obj_set_style_text_color(lbl_duty_percent, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_duty_percent, &lv_font_montserrat_24, 0);
  lv_obj_set_pos(lbl_duty_percent, 70, 126);

  // Step buttons for duty cycle (size: 48x32px, located below digits)
  lv_obj_t *btn_duty_dec = lv_button_create(right_col);
  lv_obj_set_size(btn_duty_dec, 48, 32);
  lv_obj_set_pos(btn_duty_dec, 10, 168);
  lv_obj_remove_flag(btn_duty_dec, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_bg_color(btn_duty_dec, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(btn_duty_dec, get_current_text_color(), 0);
  lv_obj_set_style_border_opa(btn_duty_dec, LV_OPA_30, 0);
  lv_obj_set_style_border_width(btn_duty_dec, 1, 0);
  lv_obj_set_style_radius(btn_duty_dec, 6, 0);
  lv_obj_set_style_pad_all(btn_duty_dec, 0, 0);

  lv_obj_t *lbl_duty_dec = lv_label_create(btn_duty_dec);
  lv_label_set_text(lbl_duty_dec, "-");
  lv_obj_set_style_text_font(lbl_duty_dec, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_color(lbl_duty_dec, get_current_text_color(), 0);
  lv_obj_center(lbl_duty_dec);
  make_descendants_click_through(btn_duty_dec);

  lv_obj_t *btn_duty_inc = lv_button_create(right_col);
  lv_obj_set_size(btn_duty_inc, 48, 32);
  lv_obj_set_pos(btn_duty_inc, 66, 168);
  lv_obj_remove_flag(btn_duty_inc, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_bg_color(btn_duty_inc, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(btn_duty_inc, get_current_text_color(), 0);
  lv_obj_set_style_border_opa(btn_duty_inc, LV_OPA_30, 0);
  lv_obj_set_style_border_width(btn_duty_inc, 1, 0);
  lv_obj_set_style_radius(btn_duty_inc, 6, 0);
  lv_obj_set_style_pad_all(btn_duty_inc, 0, 0);

  lv_obj_t *lbl_duty_inc = lv_label_create(btn_duty_inc);
  lv_label_set_text(lbl_duty_inc, "+");
  lv_obj_set_style_text_font(lbl_duty_inc, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_color(lbl_duty_inc, get_current_text_color(), 0);
  lv_obj_center(lbl_duty_inc);
  make_descendants_click_through(btn_duty_inc);

  lv_obj_add_event_cb(btn_duty_dec, gen_duty_step_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)-1);
  lv_obj_add_event_cb(btn_duty_inc, gen_duty_step_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)1);

  // Fixed 3.3V Amplitude Note at the bottom-right
  lbl_gen_amp = lv_label_create(right_col);
  lv_label_set_text(lbl_gen_amp, "0 - 2.5 V\n10 Hz - 50 kHz");
  lv_obj_set_style_text_color(lbl_gen_amp, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_gen_amp, &lv_font_montserrat_14, 0);
  lv_obj_set_style_text_align(lbl_gen_amp, LV_TEXT_ALIGN_RIGHT, 0);
  lv_obj_align(lbl_gen_amp, LV_ALIGN_BOTTOM_RIGHT, -10, -10);

  // Dynamic Visibility of Duty Cycle depending on wave type (only shown for PWM = index 1)
  int current_type = gen_wave_type[gen_active_channel];
  if (current_type == 1) {
      lv_obj_remove_flag(btn_duty_d0, LV_OBJ_FLAG_HIDDEN);
      lv_obj_remove_flag(btn_duty_d1, LV_OBJ_FLAG_HIDDEN);
      lv_obj_remove_flag(lbl_duty_percent, LV_OBJ_FLAG_HIDDEN);
      lv_obj_remove_flag(btn_duty_dec, LV_OBJ_FLAG_HIDDEN);
      lv_obj_remove_flag(btn_duty_inc, LV_OBJ_FLAG_HIDDEN);
  } else {
      lv_obj_add_flag(btn_duty_d0, LV_OBJ_FLAG_HIDDEN);
      lv_obj_add_flag(btn_duty_d1, LV_OBJ_FLAG_HIDDEN);
      lv_obj_add_flag(lbl_duty_percent, LV_OBJ_FLAG_HIDDEN);
      lv_obj_add_flag(btn_duty_dec, LV_OBJ_FLAG_HIDDEN);
      lv_obj_add_flag(btn_duty_inc, LV_OBJ_FLAG_HIDDEN);
  }
}
