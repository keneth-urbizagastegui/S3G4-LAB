#include "ui_view.h"
#include "ui_common.h"
#include <lvgl.h>
#include <math.h>

bool view_box_has_data[18] = {false}; // Starts empty as requested
static int view_selected_box = -1;     // Absolute selected index (0-17)
static int view_current_page = 0;      // 0 = Page 1, 1 = Page 2

static void make_descendants_click_through(lv_obj_t *obj) {
    if (!obj) return;
    uint32_t cnt = lv_obj_get_child_count(obj);
    for (uint32_t i = 0; i < cnt; i++) {
        lv_obj_t *child = lv_obj_get_child(obj, i);
        lv_obj_remove_flag(child, LV_OBJ_FLAG_CLICKABLE);
        make_descendants_click_through(child);
    }
}

static void open_full_capture_preview(int abs_idx) {
    lv_obj_t *overlay = lv_obj_create(active_screen_container);
    lv_obj_set_size(overlay, 480, 320);
    lv_obj_set_pos(overlay, 0, 0);
    lv_obj_set_style_bg_color(overlay, get_current_bg_color(), 0);
    lv_obj_set_style_border_width(overlay, 0, 0);
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_SCROLLABLE);

    // Title bar inside overlay
    lv_obj_t *t_bar = lv_obj_create(overlay);
    lv_obj_set_size(t_bar, 480, 32);
    lv_obj_set_pos(t_bar, 0, 0);
    lv_obj_set_style_bg_color(t_bar, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(t_bar, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(t_bar, 1, 0);
    lv_obj_set_style_border_side(t_bar, LV_BORDER_SIDE_BOTTOM, 0);
    lv_obj_set_style_radius(t_bar, 0, 0);
    lv_obj_set_style_pad_all(t_bar, 0, 0);
    lv_obj_remove_flag(t_bar, LV_OBJ_FLAG_SCROLLABLE);

    // Return button "◀ Volver"
    lv_obj_t *btn_back = lv_button_create(t_bar);
    lv_obj_set_size(btn_back, 75, 24);
    lv_obj_align(btn_back, LV_ALIGN_LEFT_MID, 6, 0);
    lv_obj_set_style_bg_color(btn_back, get_current_panel_color(), 0);
    lv_obj_set_style_bg_color(btn_back, get_current_accent_color(), LV_STATE_PRESSED);
    lv_obj_set_style_border_color(btn_back, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(btn_back, 1, 0);
    lv_obj_set_style_radius(btn_back, 6, 0);
    lv_obj_set_style_pad_all(btn_back, 0, 0);
    lv_obj_remove_flag(btn_back, LV_OBJ_FLAG_SCROLLABLE);
    
    // Deletes the overlay when clicked
    lv_obj_add_event_cb(btn_back, [](lv_event_t *ev){
        lv_obj_t *ov = (lv_obj_t *)lv_event_get_user_data(ev);
        lv_obj_delete(ov);
    }, LV_EVENT_CLICKED, overlay);

    lv_obj_t *lbl_back = lv_label_create(btn_back);
    lv_label_set_text(lbl_back, "◀ Volver");
    lv_obj_set_style_text_color(lbl_back, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_back, &lv_font_montserrat_14, 0);
    lv_obj_center(lbl_back);

    make_descendants_click_through(btn_back);

    // Title label
    lv_obj_t *title_lbl = lv_label_create(t_bar);
    lv_label_set_text_fmt(title_lbl, "SCREENSHOT %d PREVIEW", abs_idx + 1);
    lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
    lv_obj_set_style_text_font(title_lbl, &lv_font_montserrat_14, 0);
    lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

    // Full chart
    lv_obj_t *full_chart = lv_chart_create(overlay);
    lv_obj_set_size(full_chart, 400, 240);
    lv_obj_align(full_chart, LV_ALIGN_CENTER, 0, 20);
    lv_obj_set_style_bg_color(full_chart, lv_color_hex(0x000000), 0);
    lv_obj_set_style_border_color(full_chart, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(full_chart, 1, 0);
    lv_obj_set_style_radius(full_chart, 8, 0);
    lv_obj_remove_flag(full_chart, LV_OBJ_FLAG_SCROLLABLE);

    lv_chart_set_type(full_chart, LV_CHART_TYPE_LINE);
    lv_chart_set_point_count(full_chart, 256);
    lv_chart_set_range(full_chart, LV_CHART_AXIS_PRIMARY_Y, 0, 255);
    lv_chart_set_div_line_count(full_chart, 9, 11);
    lv_obj_set_style_line_color(full_chart, lv_color_hex(0x222222), LV_PART_MAIN);

    // Draw capture signal (mock sine wave or simple signals for demo if they contain data)
    lv_chart_series_t *ser = lv_chart_add_series(full_chart, get_current_accent_color(), LV_CHART_AXIS_PRIMARY_Y);
    for (int i = 0; i < 256; i++) {
        double rad = (double)i * 2.0 * 3.14159 / 64.0;
        int val = 127 + (int)(80.0 * sin(rad + abs_idx));
        lv_chart_set_value_by_id(full_chart, ser, i, val);
    }
    lv_chart_refresh(full_chart);
}

static void create_thumbnail_chart(lv_obj_t *parent, int index) {
    if (!view_box_has_data[index]) {
        lv_obj_t *lbl_empty = lv_label_create(parent);
        lv_label_set_text(lbl_empty, "EMPTY");
        lv_obj_set_style_text_color(lbl_empty, lv_color_hex(0x555555), 0);
        lv_obj_set_style_text_font(lbl_empty, &lv_font_montserrat_14, 0);
        lv_obj_center(lbl_empty);
        return;
    }

    lv_obj_t *mini_chart = lv_chart_create(parent);
    lv_obj_set_size(mini_chart, 96, 52);
    lv_obj_center(mini_chart);
    lv_obj_set_style_bg_color(mini_chart, lv_color_hex(0x000000), 0);
    lv_obj_set_style_border_width(mini_chart, 0, 0);
    lv_obj_set_style_pad_all(mini_chart, 0, 0);
    lv_obj_remove_flag(mini_chart, LV_OBJ_FLAG_SCROLLABLE);
    
    lv_chart_set_div_line_count(mini_chart, 3, 4);
    lv_obj_set_style_line_color(mini_chart, lv_color_hex(0x222222), LV_PART_MAIN);
    
    lv_chart_set_type(mini_chart, LV_CHART_TYPE_LINE);
    lv_chart_set_point_count(mini_chart, 30);
    lv_chart_set_range(mini_chart, LV_CHART_AXIS_PRIMARY_Y, 0, 255);

    lv_chart_series_t *ser = lv_chart_add_series(mini_chart, get_current_accent_color(), LV_CHART_AXIS_PRIMARY_Y);
    for (int i = 0; i < 30; i++) {
        double rad = (double)i * 2.0 * 3.14159 / 15.0;
        int val = 127 + (int)(80.0 * sin(rad + index));
        lv_chart_set_value_by_id(mini_chart, ser, i, val);
    }
    lv_chart_refresh(mini_chart);
}

static void thumbnail_click_cb(lv_event_t *e) {
    int rel_idx = (int)(uintptr_t)lv_event_get_user_data(e);
    int abs_idx = view_current_page * 9 + rel_idx;

    if (view_selected_box == abs_idx) {
        // Second tap: show full capture if it contains data
        if (view_box_has_data[abs_idx]) {
            open_full_capture_preview(abs_idx);
        }
    } else {
        // First tap: select and highlight
        view_selected_box = abs_idx;
        transition_to_screen(SCREEN_VIEW);
    }
}

static void view_scroll_up_cb(lv_event_t *e) {
    if (view_current_page > 0) {
        view_current_page--;
        transition_to_screen(SCREEN_VIEW);
    }
}

static void view_scroll_down_cb(lv_event_t *e) {
    if (view_current_page < 1) {
        view_current_page++;
        transition_to_screen(SCREEN_VIEW);
    }
}

static void view_delete_cb(lv_event_t *e) {
    if (view_selected_box >= 0 && view_selected_box < 18) {
        view_box_has_data[view_selected_box] = false;
        view_selected_box = -1;
        transition_to_screen(SCREEN_VIEW);
    }
}

void populate_view_ui(void) {
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
  lv_label_set_text(title_lbl, "IMAGE VIEW");
  lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
  lv_obj_set_style_text_font(title_lbl, &lv_font_montserrat_14, 0);
  lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

  // Larger Grid Container (380x240) to utilize the extra space
  lv_obj_t *grid_container = lv_obj_create(active_screen_container);
  lv_obj_set_size(grid_container, 380, 240);
  lv_obj_set_pos(grid_container, 10, 42);
  lv_obj_set_style_bg_color(grid_container, get_current_panel_color(), 0);
  lv_obj_set_style_border_color(grid_container, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(grid_container, 1, 0);
  lv_obj_set_style_radius(grid_container, 8, 0);
  lv_obj_set_style_pad_all(grid_container, 8, 0);
  lv_obj_remove_flag(grid_container, LV_OBJ_FLAG_SCROLLABLE);

  // 3x3 Matrix Grid
  for (int row = 0; row < 3; row++) {
      for (int col = 0; col < 3; col++) {
          int rel_idx = row * 3 + col;
          int abs_idx = view_current_page * 9 + rel_idx;
          
          lv_obj_t *thumb_box = lv_obj_create(grid_container);
          lv_obj_set_size(thumb_box, 114, 66);
          lv_obj_set_pos(thumb_box, col * 124, row * 74);
          lv_obj_set_style_bg_color(thumb_box, lv_color_hex(0x000000), 0);
          
          if (view_selected_box == abs_idx) {
              lv_obj_set_style_border_color(thumb_box, lv_color_hex(0xDA3637), 0); // red border
              lv_obj_set_style_border_width(thumb_box, 2, 0);
          } else {
              lv_obj_set_style_border_color(thumb_box, lv_color_hex(0x1F2937), 0);
              lv_obj_set_style_border_width(thumb_box, 1, 0);
          }
          
          lv_obj_set_style_radius(thumb_box, 6, 0);
          lv_obj_set_style_pad_all(thumb_box, 0, 0);
          lv_obj_remove_flag(thumb_box, LV_OBJ_FLAG_SCROLLABLE);
          lv_obj_add_flag(thumb_box, LV_OBJ_FLAG_CLICKABLE);
          lv_obj_add_event_cb(thumb_box, thumbnail_click_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)rel_idx);
          
          create_thumbnail_chart(thumb_box, abs_idx);
          make_descendants_click_through(thumb_box);
      }
  }

  // Right Side Compact Icon-Only Buttons Column (Bottom-Right side)
  // X = 418, size = 44x44
  
  // 1. Scroll Up Button
  lv_obj_t *btn_up = lv_button_create(active_screen_container);
  lv_obj_set_size(btn_up, 44, 44);
  lv_obj_set_pos(btn_up, 418, 100);
  lv_obj_set_style_bg_color(btn_up, get_current_panel_color(), 0);
  lv_obj_set_style_bg_color(btn_up, get_current_accent_color(), LV_STATE_PRESSED);
  lv_obj_set_style_border_color(btn_up, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(btn_up, 1, 0);
  lv_obj_set_style_radius(btn_up, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_pad_all(btn_up, 0, 0);
  lv_obj_remove_flag(btn_up, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_add_event_cb(btn_up, view_scroll_up_cb, LV_EVENT_CLICKED, NULL);

  lv_obj_t *lbl_up = lv_label_create(btn_up);
  lv_label_set_text(lbl_up, LV_SYMBOL_UP);
  lv_obj_set_style_text_color(lbl_up, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_up, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_up);
  make_descendants_click_through(btn_up);

  // 2. Scroll Down Button
  lv_obj_t *btn_down = lv_button_create(active_screen_container);
  lv_obj_set_size(btn_down, 44, 44);
  lv_obj_set_pos(btn_down, 418, 155);
  lv_obj_set_style_bg_color(btn_down, get_current_panel_color(), 0);
  lv_obj_set_style_bg_color(btn_down, get_current_accent_color(), LV_STATE_PRESSED);
  lv_obj_set_style_border_color(btn_down, get_current_accent_color(), 0);
  lv_obj_set_style_border_width(btn_down, 1, 0);
  lv_obj_set_style_radius(btn_down, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_pad_all(btn_down, 0, 0);
  lv_obj_remove_flag(btn_down, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_add_event_cb(btn_down, view_scroll_down_cb, LV_EVENT_CLICKED, NULL);

  lv_obj_t *lbl_down = lv_label_create(btn_down);
  lv_label_set_text(lbl_down, LV_SYMBOL_DOWN);
  lv_obj_set_style_text_color(lbl_down, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_down, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_down);
  make_descendants_click_through(btn_down);

  // 3. Delete Button (Trash)
  lv_obj_t *btn_delete = lv_button_create(active_screen_container);
  lv_obj_set_size(btn_delete, 44, 44);
  lv_obj_set_pos(btn_delete, 418, 210);
  lv_obj_set_style_bg_color(btn_delete, get_current_panel_color(), 0);
  lv_obj_set_style_bg_color(btn_delete, lv_color_hex(0xDA3637), LV_STATE_PRESSED);
  lv_obj_set_style_border_color(btn_delete, lv_color_hex(0xDA3637), 0);
  lv_obj_set_style_border_width(btn_delete, 1, 0);
  lv_obj_set_style_radius(btn_delete, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_pad_all(btn_delete, 0, 0);
  lv_obj_remove_flag(btn_delete, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_add_event_cb(btn_delete, view_delete_cb, LV_EVENT_CLICKED, NULL);

  lv_obj_t *lbl_del = lv_label_create(btn_delete);
  lv_label_set_text(lbl_del, LV_SYMBOL_TRASH);
  lv_obj_set_style_text_color(lbl_del, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_del, &lv_font_montserrat_14, 0);
  lv_obj_center(lbl_del);
  make_descendants_click_through(btn_delete);

  // Page Indicator Label
  lv_obj_t *lbl_page = lv_label_create(active_screen_container);
  lv_label_set_text_fmt(lbl_page, "%d/2", view_current_page + 1);
  lv_obj_set_style_text_color(lbl_page, get_current_text_color(), 0);
  lv_obj_set_style_text_font(lbl_page, &lv_font_montserrat_14, 0);
  lv_obj_align(lbl_page, LV_ALIGN_BOTTOM_RIGHT, -20, -10);
}
