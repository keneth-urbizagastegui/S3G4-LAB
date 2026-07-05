#include "ui_splash.h"
#include "ui_common.h"
#include <lvgl.h>

extern "C" {
  LV_FONT_DECLARE(lv_font_montserrat_28);
  LV_FONT_DECLARE(lv_font_montserrat_14);
}
LV_IMG_DECLARE(fondo_utec);

static void splash_timer_cb(lv_timer_t *timer) {
    if (current_screen == SCREEN_SPLASH) {
        transition_to_screen(SCREEN_HOME);
    }
}

void populate_splash_ui(void) {
  // Background Image (fondo_utec)
  lv_obj_t *img_bg = lv_image_create(active_screen_container);
  lv_image_set_src(img_bg, &fondo_utec);
  lv_obj_align(img_bg, LV_ALIGN_CENTER, 0, 0);

  // Top Dark Banner (60% Opacity)
  lv_obj_t *top_banner = lv_obj_create(active_screen_container);
  lv_obj_set_size(top_banner, 480, 32);
  lv_obj_align(top_banner, LV_ALIGN_TOP_MID, 0, 15);
  lv_obj_set_style_bg_color(top_banner, lv_color_hex(0x000000), 0);
  lv_obj_set_style_bg_opa(top_banner, LV_OPA_60, 0);
  lv_obj_set_style_border_width(top_banner, 0, 0);
  lv_obj_set_style_radius(top_banner, 0, 0);
  lv_obj_set_style_pad_all(top_banner, 0, 0);

  // Header Text on Top Banner
  lv_obj_t *lbl_header = lv_label_create(top_banner);
  lv_label_set_text(lbl_header, "PROYECTO FINAL DE CARRERA - ELECTRONICA");
  lv_obj_set_style_text_color(lbl_header, lv_color_hex(0xFFFFFF), 0);
  lv_obj_set_style_text_font(lbl_header, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_header);

  // Central Card for "S3G4 LAB" (Dark Box with Glow border)
  lv_obj_t *center_box = lv_obj_create(active_screen_container);
  lv_obj_set_size(center_box, 240, 60);
  lv_obj_align(center_box, LV_ALIGN_CENTER, 0, -10);
  lv_obj_set_style_bg_color(center_box, lv_color_hex(0x0A0F1D), 0);
  lv_obj_set_style_bg_opa(center_box, LV_OPA_80, 0);
  lv_obj_set_style_border_color(center_box, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(center_box, 1, 0);
  lv_obj_set_style_radius(center_box, 8, 0);
  lv_obj_set_style_pad_all(center_box, 0, 0);

  // Central Title "S3G4 SCOPE"
  lv_obj_t *lbl_title = lv_label_create(center_box);
  lv_label_set_text(lbl_title, "S3G4 SCOPE");
  lv_obj_set_style_text_color(lbl_title, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_28, 0);
  lv_obj_center(lbl_title);

  // Bottom Dark Banner (60% Opacity)
  lv_obj_t *bot_banner = lv_obj_create(active_screen_container);
  lv_obj_set_size(bot_banner, 480, 36);
  lv_obj_align(bot_banner, LV_ALIGN_BOTTOM_MID, 0, -25);
  lv_obj_set_style_bg_color(bot_banner, lv_color_hex(0x000000), 0);
  lv_obj_set_style_bg_opa(bot_banner, LV_OPA_60, 0);
  lv_obj_set_style_border_width(bot_banner, 0, 0);
  lv_obj_set_style_radius(bot_banner, 0, 0);
  lv_obj_set_style_pad_all(bot_banner, 0, 0);

  // Footer Text on Bottom Banner
  lv_obj_t *lbl_footer = lv_label_create(bot_banner);
  lv_label_set_text(lbl_footer, "OSCILOSCOPIO  \u2022  GENERADOR  \u2022  MULTIMETRO");
  lv_obj_set_style_text_color(lbl_footer, lv_color_hex(0xEEEEEE), 0);
  lv_obj_set_style_text_font(lbl_footer, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_footer);

  // Loading indicator Text
  lv_obj_t *lbl_loading = lv_label_create(active_screen_container);
  lv_label_set_text(lbl_loading, "Starting system...");
  lv_obj_align(lbl_loading, LV_ALIGN_BOTTOM_MID, 0, -5);
  lv_obj_set_style_text_color(lbl_loading, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(lbl_loading, &lv_font_montserrat_14, 0);

  lv_timer_t *timer = lv_timer_create(splash_timer_cb, 3500, NULL);
  lv_timer_set_repeat_count(timer, 1);
}
