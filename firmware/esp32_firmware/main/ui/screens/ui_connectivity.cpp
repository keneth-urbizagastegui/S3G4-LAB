#include "ui_connectivity.h"
#include "ui_common.h"
#include "wifi_ap.h"
#include <lvgl.h>
#include <string.h>

static lv_obj_t *lbl_wifi_status = NULL;
static lv_obj_t *lbl_ip_addr = NULL;
static lv_obj_t *lbl_server_status = NULL;
static lv_obj_t *sw_wifi = NULL;
static lv_obj_t *sw_server = NULL;
static lv_obj_t *list_networks = NULL;
static lv_obj_t *btn_scan = NULL;
static lv_obj_t *lbl_scan_btn = NULL;

static lv_timer_t *status_update_timer = NULL;
static bool is_scanning = false;
static char selected_ssid[33] = {0};

static lv_obj_t *modal_bg = NULL;
static lv_obj_t *ta_password = NULL;
static lv_obj_t *keyboard = NULL;

extern "C" {
    LV_FONT_DECLARE(lv_font_montserrat_14);
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

static void show_password_modal(void) {
    if (modal_bg != NULL) return;

    modal_bg = lv_obj_create(active_screen_container);
    lv_obj_set_size(modal_bg, 480, 320);
    lv_obj_set_pos(modal_bg, 0, 0);
    lv_obj_set_style_bg_color(modal_bg, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(modal_bg, LV_OPA_50, 0);
    lv_obj_set_style_border_width(modal_bg, 0, 0);
    lv_obj_set_style_radius(modal_bg, 0, 0);
    lv_obj_set_style_pad_all(modal_bg, 0, 0);
    lv_obj_remove_flag(modal_bg, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *dialog = lv_obj_create(modal_bg);
    lv_obj_set_size(dialog, 380, 240);
    lv_obj_align(dialog, LV_ALIGN_TOP_MID, 0, 10);
    lv_obj_set_style_bg_color(dialog, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(dialog, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(dialog, 2, 0);
    lv_obj_set_style_radius(dialog, 12, 0);
    lv_obj_set_style_pad_all(dialog, 8, 0);
    lv_obj_remove_flag(dialog, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_title = lv_label_create(dialog);
    lv_label_set_text_fmt(lbl_title, "Connect to: %s", selected_ssid);
    lv_obj_set_style_text_color(lbl_title, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_title, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_title, LV_ALIGN_TOP_MID, 0, 0);

    ta_password = lv_textarea_create(dialog);
    lv_textarea_set_one_line(ta_password, true);
    lv_textarea_set_password_mode(ta_password, true);
    lv_textarea_set_placeholder_text(ta_password, "Enter password...");
    lv_obj_set_size(ta_password, 320, 32);
    lv_obj_align(ta_password, LV_ALIGN_TOP_MID, 0, 20);
    lv_obj_set_style_bg_color(ta_password, get_current_bg_color(), 0);
    lv_obj_set_style_border_color(ta_password, get_current_accent_color(), 0);
    lv_obj_set_style_text_color(ta_password, get_current_text_color(), 0);

    keyboard = lv_keyboard_create(dialog);
    lv_obj_set_size(keyboard, 360, 130);
    lv_obj_align(keyboard, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_keyboard_set_textarea(keyboard, ta_password);
    
    lv_obj_add_event_cb(keyboard, [](lv_event_t *e) {
        lv_event_code_t code = lv_event_get_code(e);
        if (code == LV_EVENT_READY) {
            const char* password = lv_textarea_get_text(ta_password);
            wifi_sta_connect(selected_ssid, password);
            
            lv_obj_delete(modal_bg);
            modal_bg = NULL;
            ta_password = NULL;
            keyboard = NULL;
        } else if (code == LV_EVENT_CANCEL) {
            lv_obj_delete(modal_bg);
            modal_bg = NULL;
            ta_password = NULL;
            keyboard = NULL;
        }
    }, LV_EVENT_ALL, NULL);
}

static void status_timer_cb(lv_timer_t *timer) {
    char ip_buf[32] = {0};
    char ssid_buf[33] = {0};
    
    bool wifi_powered = wifi_sta_get_power();

    if (wifi_powered) {
        if (sw_wifi) lv_obj_add_state(sw_wifi, LV_STATE_CHECKED);
        if (btn_scan) lv_obj_remove_state(btn_scan, LV_STATE_DISABLED);
        
        wifi_sta_get_ip(ip_buf, sizeof(ip_buf));
        bool connected = wifi_sta_is_connected();

        if (connected) {
            wifi_sta_get_ssid(ssid_buf, sizeof(ssid_buf));
            lv_label_set_text_fmt(lbl_wifi_status, "Wi-Fi: Connected to %s", ssid_buf);
            lv_label_set_text_fmt(lbl_ip_addr, "IP: %s", ip_buf);
        } else {
            lv_label_set_text(lbl_wifi_status, "Wi-Fi: Disconnected");
            lv_label_set_text(lbl_ip_addr, "IP: 0.0.0.0");
        }
    } else {
        if (sw_wifi) lv_obj_remove_state(sw_wifi, LV_STATE_CHECKED);
        if (btn_scan) lv_obj_add_state(btn_scan, LV_STATE_DISABLED);
        
        lv_label_set_text(lbl_wifi_status, "Wi-Fi: DISABLED (OFF)");
        lv_label_set_text(lbl_ip_addr, "IP: 0.0.0.0");
        
        if (list_networks && lv_obj_get_child_count(list_networks) > 0) {
            lv_obj_clean(list_networks);
        }
    }

    bool server_active = webserver_is_running();
    if (server_active) {
        if (wifi_powered && wifi_sta_is_connected()) {
            lv_label_set_text_fmt(lbl_server_status, "Web Server: ACTIVE\nhttp://%s/", ip_buf);
        } else if (wifi_powered) {
            lv_label_set_text(lbl_server_status, "Web Server: ACTIVE\n(Waiting for Wi-Fi...)");
        } else {
            lv_label_set_text(lbl_server_status, "Web Server: ACTIVE\n(Wi-Fi is Powered OFF)");
        }
        lv_obj_add_state(sw_server, LV_STATE_CHECKED);
    } else {
        lv_label_set_text(lbl_server_status, "Web Server: INACTIVE");
        lv_obj_remove_state(sw_server, LV_STATE_CHECKED);
    }

    if (is_scanning && wifi_sta_is_scan_done()) {
        is_scanning = false;
        lv_label_set_text(lbl_scan_btn, "Scan Networks");
        if (wifi_powered && btn_scan) {
            lv_obj_remove_state(btn_scan, LV_STATE_DISABLED);
        }

        if (list_networks) {
            lv_obj_clean(list_networks);
            
            static wifi_scan_result_t scan_results[MAX_SCANNED_APS];
            int count = wifi_sta_get_scan_results(scan_results, MAX_SCANNED_APS);
            
            for (int i = 0; i < count; i++) {
                lv_obj_t * btn = lv_list_add_button(list_networks, LV_SYMBOL_WIFI, scan_results[i].ssid);
                lv_obj_set_style_bg_color(btn, get_current_bg_color(), 0);
                lv_obj_set_style_bg_color(btn, get_current_accent_color(), LV_STATE_PRESSED);
                lv_obj_set_style_text_color(btn, get_current_text_color(), 0);
                lv_obj_set_style_text_color(btn, lv_color_black(), LV_STATE_PRESSED);
                lv_obj_set_style_border_width(btn, 0, 0);
                
                lv_obj_add_event_cb(btn, [](lv_event_t *e) {
                    const char *ssid = lv_list_get_button_text(list_networks, (lv_obj_t *)lv_event_get_target(e));
                    strncpy(selected_ssid, ssid, sizeof(selected_ssid) - 1);
                    selected_ssid[sizeof(selected_ssid) - 1] = '\0';
                    show_password_modal();
                }, LV_EVENT_CLICKED, NULL);
            }
        }
    }
}

void populate_connectivity_ui(void) {
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
    lv_label_set_text(title_lbl, "WIFI & WEB SERVER");
    lv_obj_set_style_text_color(title_lbl, get_current_accent_color(), 0);
    lv_obj_set_style_text_font(title_lbl, &lv_font_montserrat_14, 0);
    lv_obj_align(title_lbl, LV_ALIGN_CENTER, 0, 0);

    lv_obj_t *left_panel = lv_obj_create(active_screen_container);
    lv_obj_set_size(left_panel, 220, 260);
    lv_obj_align(left_panel, LV_ALIGN_BOTTOM_LEFT, 10, -10);
    lv_obj_set_style_bg_color(left_panel, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(left_panel, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(left_panel, 2, 0);
    lv_obj_set_style_radius(left_panel, 12, 0);
    lv_obj_set_style_pad_all(left_panel, 12, 0);
    lv_obj_remove_flag(left_panel, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_wifi_hdr = lv_label_create(left_panel);
    lv_label_set_text(lbl_wifi_hdr, "CONNECTION STATUS");
    lv_obj_set_style_text_color(lbl_wifi_hdr, get_current_accent_color(), 0);
    lv_obj_set_style_text_font(lbl_wifi_hdr, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_wifi_hdr, LV_ALIGN_TOP_LEFT, 0, 0);

    lbl_wifi_status = lv_label_create(left_panel);
    lv_label_set_text(lbl_wifi_status, "Wi-Fi: Disconnected");
    lv_obj_set_style_text_color(lbl_wifi_status, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_wifi_status, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_wifi_status, LV_ALIGN_TOP_LEFT, 0, 18);

    lbl_ip_addr = lv_label_create(left_panel);
    lv_label_set_text(lbl_ip_addr, "IP: 0.0.0.0");
    lv_obj_set_style_text_color(lbl_ip_addr, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_ip_addr, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_ip_addr, LV_ALIGN_TOP_LEFT, 0, 34);

    // Wi-Fi Power Switch
    sw_wifi = lv_switch_create(left_panel);
    lv_obj_align(sw_wifi, LV_ALIGN_TOP_LEFT, 0, 54);
    lv_obj_add_event_cb(sw_wifi, [](lv_event_t *e) {
        lv_obj_t *sw = (lv_obj_t*)lv_event_get_target(e);
        bool power = lv_obj_has_state(sw, LV_STATE_CHECKED);
        wifi_sta_set_power(power);
    }, LV_EVENT_VALUE_CHANGED, NULL);

    lv_obj_t *lbl_wifi_sw_label = lv_label_create(left_panel);
    lv_label_set_text(lbl_wifi_sw_label, "Wi-Fi Transceiver");
    lv_obj_set_style_text_color(lbl_wifi_sw_label, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_wifi_sw_label, &lv_font_montserrat_14, 0);
    lv_obj_align_to(lbl_wifi_sw_label, sw_wifi, LV_ALIGN_OUT_RIGHT_MID, 10, 0);

    lv_obj_t *lbl_srv_hdr = lv_label_create(left_panel);
    lv_label_set_text(lbl_srv_hdr, "WEB SERVER CONTROLS");
    lv_obj_set_style_text_color(lbl_srv_hdr, get_current_accent_color(), 0);
    lv_obj_set_style_text_font(lbl_srv_hdr, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_srv_hdr, LV_ALIGN_TOP_LEFT, 0, 98);

    sw_server = lv_switch_create(left_panel);
    lv_obj_align(sw_server, LV_ALIGN_TOP_LEFT, 0, 118);
    lv_obj_add_event_cb(sw_server, [](lv_event_t *e) {
        lv_obj_t *sw = (lv_obj_t*)lv_event_get_target(e);
        if (lv_obj_has_state(sw, LV_STATE_CHECKED)) {
            webserver_start();
        } else {
            webserver_stop();
        }
    }, LV_EVENT_VALUE_CHANGED, NULL);

    lv_obj_t *lbl_sw_label = lv_label_create(left_panel);
    lv_label_set_text(lbl_sw_label, "Enable Server");
    lv_obj_set_style_text_color(lbl_sw_label, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_sw_label, &lv_font_montserrat_14, 0);
    lv_obj_align_to(lbl_sw_label, sw_server, LV_ALIGN_OUT_RIGHT_MID, 10, 0);

    lbl_server_status = lv_label_create(left_panel);
    lv_label_set_text(lbl_server_status, "Web Server: INACTIVE");
    lv_obj_set_style_text_color(lbl_server_status, get_current_text_color(), 0);
    lv_obj_set_style_text_font(lbl_server_status, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_server_status, LV_ALIGN_TOP_LEFT, 0, 148);

    lv_obj_t *right_panel = lv_obj_create(active_screen_container);
    lv_obj_set_size(right_panel, 220, 260);
    lv_obj_align(right_panel, LV_ALIGN_BOTTOM_RIGHT, -10, -10);
    lv_obj_set_style_bg_color(right_panel, get_current_panel_color(), 0);
    lv_obj_set_style_border_color(right_panel, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(right_panel, 2, 0);
    lv_obj_set_style_radius(right_panel, 12, 0);
    lv_obj_set_style_pad_all(right_panel, 10, 0);
    lv_obj_remove_flag(right_panel, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *lbl_list_hdr = lv_label_create(right_panel);
    lv_label_set_text(lbl_list_hdr, "AVAILABLE NETWORKS");
    lv_obj_set_style_text_color(lbl_list_hdr, get_current_accent_color(), 0);
    lv_obj_set_style_text_font(lbl_list_hdr, &lv_font_montserrat_14, 0);
    lv_obj_align(lbl_list_hdr, LV_ALIGN_TOP_LEFT, 0, 0);

    list_networks = lv_list_create(right_panel);
    lv_obj_set_size(list_networks, 200, 165);
    lv_obj_align(list_networks, LV_ALIGN_TOP_MID, 0, 20);
    lv_obj_set_style_bg_color(list_networks, get_current_bg_color(), 0);
    lv_obj_set_style_border_color(list_networks, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(list_networks, 1, 0);
    lv_obj_set_style_radius(list_networks, 8, 0);

    btn_scan = lv_button_create(right_panel);
    lv_obj_set_size(btn_scan, 200, 32);
    lv_obj_align(btn_scan, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_obj_set_style_bg_color(btn_scan, get_current_accent_color(), 0);
    lv_obj_set_style_border_width(btn_scan, 0, 0);
    lv_obj_set_style_radius(btn_scan, 6, 0);
    lv_obj_add_event_cb(btn_scan, [](lv_event_t *e) {
        if (!is_scanning) {
            is_scanning = true;
            lv_label_set_text(lbl_scan_btn, "Scanning...");
            lv_obj_add_state(btn_scan, LV_STATE_DISABLED);
            wifi_sta_start_scan();
        }
    }, LV_EVENT_CLICKED, NULL);

    lbl_scan_btn = lv_label_create(btn_scan);
    lv_label_set_text(lbl_scan_btn, "Scan Networks");
    lv_obj_set_style_text_font(lbl_scan_btn, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(lbl_scan_btn, lv_color_black(), 0);
    lv_obj_center(lbl_scan_btn);

    status_update_timer = lv_timer_create(status_timer_cb, 500, NULL);
    
    status_timer_cb(NULL);
}

void cleanup_connectivity_ui(void) {
    if (status_update_timer) {
        lv_timer_delete(status_update_timer);
        status_update_timer = NULL;
    }
    is_scanning = false;
    modal_bg = NULL;
    ta_password = NULL;
    keyboard = NULL;
    
    lbl_wifi_status = NULL;
    lbl_ip_addr = NULL;
    lbl_server_status = NULL;
    sw_wifi = NULL;
    sw_server = NULL;
    list_networks = NULL;
    btn_scan = NULL;
    lbl_scan_btn = NULL;
}
