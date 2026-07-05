#include "ui_common.h"
#include <esp_log.h>
#include <cstdio>

// Headers of screen instantiators
#include "ui_splash.h"
#include "ui_home.h"
#include "ui_scope.h"
#include "ui_dmm.h"
#include "ui_gen.h"
#include "ui_view.h"
#include "ui_person.h"
#include "ui_connectivity.h"

static const char *TAG = "ui_common";

// Definition of global variables
eScreen current_screen = SCREEN_SPLASH;
lv_obj_t *active_screen_container = NULL;

// Definitions of scope state variables
bool scope_ch_active[4] = {true, false, false, false};
bool scope_meas_active[4][14] = {
    {true, false, false, false, false, false, false, false, false, false, false, false, false, false},
    {false, false, false, false, false, false, false, false, false, false, false, false, false, false},
    {false, false, false, false, false, false, false, false, false, false, false, false, false, false},
    {false, false, false, false, false, false, false, false, false, false, false, false, false, false}
};
lv_obj_t *scope_meas_labels[4][14] = {
    {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL}
};
int scope_timebase_idx = 11; // 200us
int scope_volt_div_idx[4] = {2, 2, 2, 2}; // 200mV
int scope_trig_mode = 0; // Auto
int scope_trig_level_mode = 0; // Auto
int scope_trig_edge = 0; // Rise
int scope_trig_source = 0; // CH1
int scope_trig_arrow_x = 240;
int scope_trig_arrow_y = 162;

lv_obj_t *chart_obj = NULL;
lv_chart_series_t *ser_ch1 = NULL;
lv_chart_series_t *ser_ch2 = NULL;
lv_chart_series_t *ser_ch3 = NULL;
lv_chart_series_t *ser_ch4 = NULL;
lv_obj_t *lbl_dmm_val = NULL;

// Personalization settings
int opt_grid_type = 1;
int opt_grid_intensity = 1;
int opt_ch1_color = 0; // Yellow
int opt_ch2_color = 2; // Cyan
int opt_ch3_color = 1; // Lime
int opt_ch4_color = 4; // White
int opt_dmm_mode = 0;
bool opt_disp_inver = false;
int opt_theme_idx = 0;

// Theme list definitions
const tTheme themes[] = {
    {0x010310, 0x23A9BD, 0x0E1929, 0xFFFFFF}, // UTEC Dark
    {0x003152, 0xADDFF1, 0x004A7C, 0xFFFFFF}, // Ice Ice
    {0x122837, 0xFBFC09, 0x1E3B4F, 0xFFFFFF}, // Warning Yellow
    {0x07191E, 0x02F5A1, 0x0E2D34, 0xFFFFFF}  // Dark Mint
};

// Color helper implementations
lv_color_t get_current_bg_color(void) {
    return lv_color_hex(themes[opt_theme_idx].bg_color);
}
lv_color_t get_current_accent_color(void) {
    return lv_color_hex(themes[opt_theme_idx].accent_color);
}
lv_color_t get_current_panel_color(void) {
    return lv_color_hex(themes[opt_theme_idx].panel_color);
}
lv_color_t get_current_text_color(void) {
    return lv_color_hex(themes[opt_theme_idx].text_color);
}

// Timer declared in ui_dmm.cpp to delete it safely on navigation
extern lv_timer_t *dmm_update_timer;

void transition_to_screen(eScreen next_screen) {
    ESP_LOGI(TAG, "Transitioning to screen %d", (int)next_screen);
    current_screen = next_screen;

    // 1. Delete DMM update timer if running
    if (dmm_update_timer) {
        lv_timer_delete(dmm_update_timer);
        dmm_update_timer = NULL;
    }

    // 1.1 Safely cleanup Scope UI resources (timers)
    cleanup_scope_ui();

    // 1.2 Safely cleanup Connectivity UI resources (timers)
    cleanup_connectivity_ui();

    // 2. Safely destroy active layout container
    if (active_screen_container) {
        lv_obj_delete(active_screen_container);
        active_screen_container = NULL;
    }

    // Clear dynamic telemetry pointers
    chart_obj = NULL;
    ser_ch1 = NULL;
    ser_ch2 = NULL;
    ser_ch3 = NULL;
    ser_ch4 = NULL;
    lbl_dmm_val = NULL;

    // 3. Rebuild active root layout container
    lv_obj_t *scr = lv_screen_active();
    active_screen_container = lv_obj_create(scr);
    lv_obj_set_size(active_screen_container, 480, 320);
    lv_obj_set_pos(active_screen_container, 0, 0);
    lv_obj_set_style_bg_color(active_screen_container, get_current_bg_color(), 0);
    lv_obj_set_style_border_width(active_screen_container, 0, 0);
    lv_obj_set_style_radius(active_screen_container, 0, 0);
    lv_obj_set_style_pad_all(active_screen_container, 0, 0);

    // 4. Construct the designated UI screen layout
    switch (next_screen) {
        case SCREEN_SPLASH:
            populate_splash_ui();
            break;
        case SCREEN_HOME:
            populate_home_ui();
            break;
        case SCREEN_OSCOPE:
            populate_scope_ui();
            break;
        case SCREEN_DMM:
            populate_dmm_ui();
            break;
        case SCREEN_GEN:
            populate_gen_ui();
            break;
        case SCREEN_VIEW:
            populate_view_ui();
            break;
        case SCREEN_PERSON:
            populate_person_ui();
            break;
        case SCREEN_CONNECTIVITY:
            populate_connectivity_ui();
            break;
    }
}

void format_scope_meas_value(char *buf, size_t buf_sz, int m_idx, float val) {
    float abs_val = (val < 0) ? -val : val;
    switch(m_idx) {
        case 0: // Freq
            if (abs_val >= 1000000.0f) {
                snprintf(buf, buf_sz, "Frq:%.2fMHz", val / 1000000.0f);
            } else if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "Frq:%.2fkHz", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "Frq:%.1fHz", val);
            }
            break;
        case 1: // PKPK
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "PKPK:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "PKPK:%.1fmV", val);
            }
            break;
        case 2: // Mean
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "Mea:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "Mea:%.1fmV", val);
            }
            break;
        case 3: // RMS
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "RMS:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "RMS:%.1fmV", val);
            }
            break;
        case 4: // Amp
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "AMP:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "AMP:%.1fmV", val);
            }
            break;
        case 5: // Duty
            snprintf(buf, buf_sz, "Duty:%.1f%%", val);
            break;
        case 6: // Wid+
            if (abs_val >= 1.0f) {
                snprintf(buf, buf_sz, "T+:%.2fs", val);
            } else if (abs_val >= 0.001f) {
                snprintf(buf, buf_sz, "T+:%.2fms", val * 1000.0f);
            } else {
                snprintf(buf, buf_sz, "T+:%.1fus", val * 1000000.0f);
            }
            break;
        case 7: // Wid-
            if (abs_val >= 1.0f) {
                snprintf(buf, buf_sz, "T-:%.2fs", val);
            } else if (abs_val >= 0.001f) {
                snprintf(buf, buf_sz, "T-:%.2fms", val * 1000.0f);
            } else {
                snprintf(buf, buf_sz, "T-:%.1fus", val * 1000000.0f);
            }
            break;
        case 8: // Perd
            if (abs_val >= 1.0f) {
                snprintf(buf, buf_sz, "T:%.2fs", val);
            } else if (abs_val >= 0.001f) {
                snprintf(buf, buf_sz, "T:%.2fms", val * 1000.0f);
            } else {
                snprintf(buf, buf_sz, "T:%.1fus", val * 1000000.0f);
            }
            break;
        case 9: // Max
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "MAX:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "MAX:%.1fmV", val);
            }
            break;
        case 10: // Min
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "MIN:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "MIN:%.1fmV", val);
            }
            break;
        case 11: // Top
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "TOP:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "TOP:%.1fmV", val);
            }
            break;
        case 12: // Base
            if (abs_val >= 1000.0f) {
                snprintf(buf, buf_sz, "Bas:%.2fV", val / 1000.0f);
            } else {
                snprintf(buf, buf_sz, "Bas:%.1fmV", val);
            }
            break;
        case 13: // Duty-
            snprintf(buf, buf_sz, "Dut-:%.1f%%", val);
            break;
        default:
            snprintf(buf, buf_sz, "--");
            break;
    }
}

int get_y_coord_for_zero_v(int ch) {
    static const uint8_t volt_div_gain_mapping[] = { 4, 3, 2, 1, 0, 0, 0 };
    int scale = volt_div_gain_mapping[scope_volt_div_idx[ch]];
    float term1 = 9810.0f / (float)(1 << scale);
    float v_adc_0v = (term1 - 214.0f) * (float)(1 << (scale + 12)) / 19620.0f;
    float y_val = v_adc_0v / 16.0f;
    if (y_val < 0) y_val = 0;
    if (y_val > 255) y_val = 255;
    return 280 - (int)((y_val / 255.0f) * 236.0f);
}
