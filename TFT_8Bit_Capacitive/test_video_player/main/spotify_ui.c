#include "spotify_ui.h"
#include <stdio.h>
#include <string.h>
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "ili9488_8080.h"
#include "perf.h"

__attribute__((unused)) static const char *TAG = "SPOTIFY_UI";

// Lista de reproducción oficial cargada en la MicroSD (formato AVI MJPEG a 30 FPS)
const track_meta_t g_playlist[PLAYLIST_SIZE] = {
    {"Dance No More", "Harry Styles", "/sdcard/harry.avi"},
    {"hate that i made you love me", "Ariana Grande", "/sdcard/ariana.avi"},
    {"ICONIC BY MISTAKE", "LE SSERAFIM x ILLIT", "/sdcard/lesserafim.avi"},
    {"HANDS UP", "MEOVV", "/sdcard/meovv.avi"},
};

// Dimensiones de canvas de video
#define STUDIO_W 240
#define STUDIO_H 160
#define FULL_W   480
#define FULL_H   320

// Búferes dobles de cuadros RGB565 en PSRAM para eliminación de tearing
static uint16_t *s_buf_studio[2] = {NULL, NULL};
static volatile uint8_t s_studio_write_idx = 0;
static volatile uint8_t s_studio_read_idx = 1;

static uint16_t *s_buf_fullscreen[2] = {NULL, NULL};
static volatile uint8_t s_fs_write_idx = 0;
static volatile uint8_t s_fs_read_idx = 1;

static int s_current_track_idx = 0;
static playback_state_t s_play_state = PLAYBACK_STATE_PLAYING;
static view_mode_t s_view_mode = VIEW_MODE_STUDIO;

static track_change_cb_t s_track_cb = NULL;
static playback_ctrl_cb_t s_play_cb = NULL;
static seek_cb_t s_seek_cb = NULL;

// Objetos LVGL principales
static lv_obj_t *s_scr_studio = NULL;
static lv_obj_t *s_scr_fullscreen = NULL;

// Elementos modo Studio
static lv_obj_t *s_canvas_studio = NULL;
static lv_obj_t *s_lbl_title = NULL;
static lv_obj_t *s_lbl_artist = NULL;
static lv_obj_t *s_slider = NULL;
static lv_obj_t *s_lbl_time_cur = NULL;
static lv_obj_t *s_lbl_time_dur = NULL;
static lv_obj_t *s_btn_play_pause = NULL;
static lv_obj_t *s_lbl_play_pause = NULL;
static lv_obj_t *s_dropdown_tracks = NULL;
static lv_obj_t *s_lbl_fps_studio = NULL;

// Barras de ecualizador animadas
static lv_obj_t *s_eq_bars[4] = {NULL, NULL, NULL, NULL};
static uint8_t s_eq_step = 0;

// Elementos modo Fullscreen
static lv_obj_t *s_canvas_fullscreen = NULL;
static lv_obj_t *s_hud_overlay = NULL;
static lv_obj_t *s_hud_lbl_title = NULL;
static lv_obj_t *s_hud_lbl_time = NULL;
static lv_obj_t *s_hud_slider = NULL;
static lv_obj_t *s_hud_btn_play = NULL;
static lv_obj_t *s_hud_lbl_play = NULL;
static lv_obj_t *s_hud_lbl_fps = NULL;

static int64_t s_last_touch_hud_time = 0;
static bool s_slider_user_dragging = false;
static int s_hud_forced_mode = 0; // 0=auto, 1=siempre oculto, 2=siempre visible

// Paleta Spotify Premium
#define COLOR_SPOTIFY_BLACK      lv_color_hex(0x121212)
#define COLOR_SPOTIFY_CARD       lv_color_hex(0x181818)
#define COLOR_SPOTIFY_SURFACE    lv_color_hex(0x282828)
#define COLOR_SPOTIFY_GREEN      lv_color_hex(0x1DB954)
#define COLOR_SPOTIFY_GREEN_GLOW lv_color_hex(0x1ED760)
#define COLOR_SPOTIFY_WHITE      lv_color_hex(0xFFFFFF)
#define COLOR_SPOTIFY_GRAY       lv_color_hex(0xB3B3B3)
#define COLOR_SPOTIFY_DARKGRAY   lv_color_hex(0x404040)

// -------------------------------------------------------------
// Callbacks de Eventos
// -------------------------------------------------------------
static void on_btn_play_pause_click(lv_event_t *e) {
    player_cmd_t cmd = {.type = PCMD_TOGGLE};
    player_cmd_send(&cmd);
    ESP_LOGI("SPOTIFY_UI", "[TOUCH] Boton PLAY/PAUSE -> PCMD_TOGGLE");
}

static void on_btn_stop_click(lv_event_t *e) {
    player_cmd_t cmd = {.type = PCMD_STOP};
    player_cmd_send(&cmd);
    ESP_LOGI("SPOTIFY_UI", "[TOUCH] Boton STOP -> PCMD_STOP");
}

static void on_btn_prev_click(lv_event_t *e) {
    player_cmd_t cmd = {.type = PCMD_PREV};
    player_cmd_send(&cmd);
    ESP_LOGI("SPOTIFY_UI", "[TOUCH] Boton PREV -> PCMD_PREV");
}

static void on_btn_next_click(lv_event_t *e) {
    player_cmd_t cmd = {.type = PCMD_NEXT};
    player_cmd_send(&cmd);
    ESP_LOGI("SPOTIFY_UI", "[TOUCH] Boton NEXT -> PCMD_NEXT");
}

static void on_btn_fullscreen_toggle(lv_event_t *e) {
    if (s_view_mode == VIEW_MODE_STUDIO) {
        ESP_LOGI("SPOTIFY_UI", "[TOUCH] Cambiando a modo FULLSCREEN (480x320)");
        spotify_ui_set_view_mode(VIEW_MODE_FULLSCREEN);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, FULL_W, FULL_H}};
        player_cmd_send(&cmd);
    } else {
        ESP_LOGI("SPOTIFY_UI", "[TOUCH] Saliendo a modo STUDIO (240x160)");
        spotify_ui_set_view_mode(VIEW_MODE_STUDIO);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {10, 34, STUDIO_W, STUDIO_H}};
        player_cmd_send(&cmd);
    }
}

static void on_dropdown_change(lv_event_t *e) {
    lv_obj_t *dropdown = lv_event_get_target(e);
    uint32_t selected = lv_dropdown_get_selected(dropdown);
    if (selected < PLAYLIST_SIZE) {
        player_cmd_t cmd = {.type = PCMD_OPEN, .arg = (int32_t)selected};
        player_cmd_send(&cmd);
    }
}

static void on_slider_event(lv_event_t *e) {
    lv_event_code_t code = lv_event_get_code(e);
    lv_obj_t *slider = lv_event_get_target(e);

    if (code == LV_EVENT_PRESSED) {
        s_slider_user_dragging = true;
    } else if (code == LV_EVENT_RELEASED) {
        s_slider_user_dragging = false;
        int val = lv_slider_get_value(slider);
        player_status_t st;
        player_get_status(&st);
        int64_t dur = (int64_t)st.dur_ms;
        int32_t seek_ms = (int32_t)((dur * val) / 100);
        player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = seek_ms};
        player_cmd_send(&cmd);
    }
}

static void on_brightness_slider_event(lv_event_t *e) {
    lv_obj_t *slider = lv_event_get_target(e);
    int val = lv_slider_get_value(slider);
    ili9488_8080_set_backlight((uint8_t)val);
}

static void on_fullscreen_tap(lv_event_t *e) {
    if (!s_hud_overlay) return;
    if (s_hud_forced_mode == 1 || s_hud_forced_mode == 2) return;
    if (lv_obj_has_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN)) {
        lv_obj_remove_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
        s_last_touch_hud_time = esp_timer_get_time();
    } else {
        lv_obj_add_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
    }
}

// -------------------------------------------------------------
// Construcción de Pantalla Modo Estudio (Spotify UI)
// -------------------------------------------------------------
static void build_studio_screen(void) {
    s_scr_studio = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(s_scr_studio, COLOR_SPOTIFY_BLACK, 0);

    // 1. Barra Superior Header (480 x 28)
    lv_obj_t *header = lv_obj_create(s_scr_studio);
    lv_obj_set_size(header, 480, 28);
    lv_obj_set_pos(header, 0, 0);
    lv_obj_set_style_bg_color(header, COLOR_SPOTIFY_BLACK, 0);
    lv_obj_set_style_border_side(header, LV_BORDER_SIDE_BOTTOM, 0);
    lv_obj_set_style_border_color(header, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_border_width(header, 1, 0);
    lv_obj_set_style_pad_all(header, 0, 0);

    // Icono punto verde Spotify
    lv_obj_t *dot = lv_obj_create(header);
    lv_obj_set_size(dot, 10, 10);
    lv_obj_set_pos(dot, 10, 8);
    lv_obj_set_style_radius(dot, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(dot, COLOR_SPOTIFY_GREEN, 0);
    lv_obj_set_style_border_width(dot, 0, 0);

    lv_obj_t *lbl_brand = lv_label_create(header);
    lv_label_set_text(lbl_brand, "SPOTIFY VIDEO");
    lv_obj_set_style_text_color(lbl_brand, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_set_pos(lbl_brand, 26, 6);

    // Pill badge superior derecha
    lv_obj_t *badge = lv_obj_create(header);
    lv_obj_set_size(badge, 175, 20);
    lv_obj_set_pos(badge, 295, 4);
    lv_obj_set_style_bg_color(badge, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(badge, 10, 0);
    lv_obj_set_style_border_width(badge, 0, 0);
    lv_obj_set_style_pad_all(badge, 0, 0);

    s_lbl_fps_studio = lv_label_create(badge);
    lv_label_set_text(s_lbl_fps_studio, "30.0 FPS • SIMD ESP32-S3");
    lv_obj_set_style_text_color(s_lbl_fps_studio, COLOR_SPOTIFY_GREEN_GLOW, 0);
    lv_obj_center(s_lbl_fps_studio);

    // 2. Canvas de Video Studio (240x160 a la izquierda)
    s_canvas_studio = lv_canvas_create(s_scr_studio);
    lv_canvas_set_buffer(s_canvas_studio, s_buf_studio[0], STUDIO_W, STUDIO_H, LV_COLOR_FORMAT_RGB565);
    lv_obj_set_size(s_canvas_studio, STUDIO_W, STUDIO_H);
    lv_obj_set_pos(s_canvas_studio, 10, 34);
    lv_obj_set_style_radius(s_canvas_studio, 8, 0);
    lv_obj_set_style_border_width(s_canvas_studio, 1, 0);
    lv_obj_set_style_border_color(s_canvas_studio, COLOR_SPOTIFY_SURFACE, 0);

    // 3. Panel de Información Lateral (Derecha, 215x160)
    lv_obj_t *info_panel = lv_obj_create(s_scr_studio);
    lv_obj_set_size(info_panel, 215, STUDIO_H);
    lv_obj_set_pos(info_panel, 256, 34);
    lv_obj_set_style_bg_color(info_panel, COLOR_SPOTIFY_CARD, 0);
    lv_obj_set_style_radius(info_panel, 10, 0);
    lv_obj_set_style_border_width(info_panel, 1, 0);
    lv_obj_set_style_border_color(info_panel, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_pad_all(info_panel, 8, 0);

    s_lbl_title = lv_label_create(info_panel);
    lv_label_set_text(s_lbl_title, g_playlist[0].title);
    lv_obj_set_style_text_color(s_lbl_title, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_set_pos(s_lbl_title, 2, 2);

    s_lbl_artist = lv_label_create(info_panel);
    lv_label_set_text(s_lbl_artist, g_playlist[0].artist);
    lv_obj_set_style_text_color(s_lbl_artist, COLOR_SPOTIFY_GRAY, 0);
    lv_obj_set_pos(s_lbl_artist, 2, 20);

    // 4 Barras de Ecualizador Animadas en el Info Panel
    for (int i = 0; i < 4; i++) {
        s_eq_bars[i] = lv_obj_create(info_panel);
        lv_obj_set_size(s_eq_bars[i], 3, 10);
        lv_obj_set_pos(s_eq_bars[i], 180 + i * 5, 8);
        lv_obj_set_style_bg_color(s_eq_bars[i], COLOR_SPOTIFY_GREEN, 0);
        lv_obj_set_style_radius(s_eq_bars[i], 2, 0);
        lv_obj_set_style_border_width(s_eq_bars[i], 0, 0);
    }

    // Dropdown selector de canciones estilizado
    s_dropdown_tracks = lv_dropdown_create(info_panel);
    lv_dropdown_set_options(s_dropdown_tracks,
        "1. Harry Styles\n"
        "2. Ariana Grande\n"
        "3. LE SSERAFIM\n"
        "4. MEOVV");
    lv_obj_set_size(s_dropdown_tracks, 195, 34);
    lv_obj_set_pos(s_dropdown_tracks, 2, 42);
    lv_obj_set_style_bg_color(s_dropdown_tracks, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_text_color(s_dropdown_tracks, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_set_style_border_color(s_dropdown_tracks, COLOR_SPOTIFY_GREEN, 0);
    lv_obj_set_style_radius(s_dropdown_tracks, 6, 0);
    lv_obj_add_event_cb(s_dropdown_tracks, on_dropdown_change, LV_EVENT_VALUE_CHANGED, NULL);

    // Slider de Brillo de Pantalla con icono sol
    lv_obj_t *lbl_bri = lv_label_create(info_panel);
    lv_label_set_text(lbl_bri, LV_SYMBOL_IMAGE);
    lv_obj_set_style_text_color(lbl_bri, COLOR_SPOTIFY_GRAY, 0);
    lv_obj_set_pos(lbl_bri, 2, 88);

    lv_obj_t *bri_slider = lv_slider_create(info_panel);
    lv_obj_set_size(bri_slider, 80, 6);
    lv_obj_set_pos(bri_slider, 18, 92);
    lv_slider_set_range(bri_slider, 20, 100);
    lv_slider_set_value(bri_slider, 100, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(bri_slider, COLOR_SPOTIFY_SURFACE, LV_PART_MAIN);
    lv_obj_set_style_bg_color(bri_slider, COLOR_SPOTIFY_GREEN, LV_PART_INDICATOR);
    lv_obj_set_style_bg_color(bri_slider, COLOR_SPOTIFY_WHITE, LV_PART_KNOB);
    lv_obj_set_style_pad_all(bri_slider, 2, LV_PART_KNOB);
    lv_obj_add_event_cb(bri_slider, on_brightness_slider_event, LV_EVENT_VALUE_CHANGED, NULL);

    // Botón Fullscreen Expand
    lv_obj_t *btn_fs = lv_button_create(info_panel);
    lv_obj_set_size(btn_fs, 85, 28);
    lv_obj_set_pos(btn_fs, 110, 80);
    lv_obj_set_style_bg_color(btn_fs, COLOR_SPOTIFY_GREEN, 0);
    lv_obj_set_style_radius(btn_fs, 14, 0);
    lv_obj_add_event_cb(btn_fs, on_btn_fullscreen_toggle, LV_EVENT_CLICKED, NULL);

    lv_obj_t *lbl_fs = lv_label_create(btn_fs);
    lv_label_set_text(lbl_fs, "[+] EXPAND");
    lv_obj_set_style_text_color(lbl_fs, COLOR_SPOTIFY_BLACK, 0);
    lv_obj_center(lbl_fs);

    // Label estado calidad
    lv_obj_t *lbl_info_sub = lv_label_create(info_panel);
    lv_label_set_text(lbl_info_sub, "30 FPS • YUV420 SIMD • Zero Tearing");
    lv_obj_set_style_text_color(lbl_info_sub, COLOR_SPOTIFY_GRAY, 0);
    lv_obj_set_pos(lbl_info_sub, 2, 114);

    // 4. Barra de Progreso y Scrubber (Y: 202..230)
    s_lbl_time_cur = lv_label_create(s_scr_studio);
    lv_label_set_text(s_lbl_time_cur, "00:00");
    lv_obj_set_style_text_color(s_lbl_time_cur, COLOR_SPOTIFY_GRAY, 0);
    lv_obj_set_pos(s_lbl_time_cur, 14, 206);

    s_slider = lv_slider_create(s_scr_studio);
    lv_obj_set_size(s_slider, 370, 8);
    lv_obj_set_pos(s_slider, 55, 210);
    lv_slider_set_range(s_slider, 0, 100);
    lv_slider_set_value(s_slider, 0, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(s_slider, COLOR_SPOTIFY_DARKGRAY, LV_PART_MAIN);
    lv_obj_set_style_bg_color(s_slider, COLOR_SPOTIFY_GREEN, LV_PART_INDICATOR);
    lv_obj_set_style_bg_color(s_slider, COLOR_SPOTIFY_WHITE, LV_PART_KNOB);
    lv_obj_set_style_pad_all(s_slider, 4, LV_PART_KNOB);
    lv_obj_add_event_cb(s_slider, on_slider_event, LV_EVENT_ALL, NULL);

    s_lbl_time_dur = lv_label_create(s_scr_studio);
    lv_label_set_text(s_lbl_time_dur, "03:21");
    lv_obj_set_style_text_color(s_lbl_time_dur, COLOR_SPOTIFY_GRAY, 0);
    lv_obj_set_pos(s_lbl_time_dur, 432, 206);

    // 5. Barra de Controles Multimedia Premium (Y: 232..312)
    lv_obj_t *ctrl_bar = lv_obj_create(s_scr_studio);
    lv_obj_set_size(ctrl_bar, 460, 72);
    lv_obj_set_pos(ctrl_bar, 10, 234);
    lv_obj_set_style_bg_color(ctrl_bar, COLOR_SPOTIFY_CARD, 0);
    lv_obj_set_style_radius(ctrl_bar, 12, 0);
    lv_obj_set_style_border_width(ctrl_bar, 1, 0);
    lv_obj_set_style_border_color(ctrl_bar, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_pad_all(ctrl_bar, 0, 0);

    // Botón Shuffle
    lv_obj_t *btn_shuf = lv_button_create(ctrl_bar);
    lv_obj_set_size(btn_shuf, 40, 40);
    lv_obj_set_pos(btn_shuf, 20, 16);
    lv_obj_set_style_bg_color(btn_shuf, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(btn_shuf, LV_RADIUS_CIRCLE, 0);
    lv_obj_t *l_shuf = lv_label_create(btn_shuf);
    lv_label_set_text(l_shuf, LV_SYMBOL_SHUFFLE);
    lv_obj_set_style_text_color(l_shuf, COLOR_SPOTIFY_GREEN, 0);
    lv_obj_center(l_shuf);

    // Botón Prev
    lv_obj_t *btn_prev = lv_button_create(ctrl_bar);
    lv_obj_set_size(btn_prev, 46, 46);
    lv_obj_set_pos(btn_prev, 100, 13);
    lv_obj_set_style_bg_color(btn_prev, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(btn_prev, LV_RADIUS_CIRCLE, 0);
    lv_obj_add_event_cb(btn_prev, on_btn_prev_click, LV_EVENT_CLICKED, NULL);
    lv_obj_t *l_prev = lv_label_create(btn_prev);
    lv_label_set_text(l_prev, LV_SYMBOL_PREV);
    lv_obj_set_style_text_color(l_prev, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_center(l_prev);

    // Botón Play/Pause (Grande Verde Spotify con Glow)
    s_btn_play_pause = lv_button_create(ctrl_bar);
    lv_obj_set_size(s_btn_play_pause, 56, 56);
    lv_obj_set_pos(s_btn_play_pause, 202, 8);
    lv_obj_set_style_bg_color(s_btn_play_pause, COLOR_SPOTIFY_GREEN, 0);
    lv_obj_set_style_radius(s_btn_play_pause, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_border_width(s_btn_play_pause, 2, 0);
    lv_obj_set_style_border_color(s_btn_play_pause, COLOR_SPOTIFY_GREEN_GLOW, 0);
    lv_obj_add_event_cb(s_btn_play_pause, on_btn_play_pause_click, LV_EVENT_CLICKED, NULL);

    s_lbl_play_pause = lv_label_create(s_btn_play_pause);
    lv_label_set_text(s_lbl_play_pause, LV_SYMBOL_PAUSE);
    lv_obj_set_style_text_color(s_lbl_play_pause, COLOR_SPOTIFY_BLACK, 0);
    lv_obj_center(s_lbl_play_pause);

    // Botón Next
    lv_obj_t *btn_next = lv_button_create(ctrl_bar);
    lv_obj_set_size(btn_next, 46, 46);
    lv_obj_set_pos(btn_next, 304, 13);
    lv_obj_set_style_bg_color(btn_next, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(btn_next, LV_RADIUS_CIRCLE, 0);
    lv_obj_add_event_cb(btn_next, on_btn_next_click, LV_EVENT_CLICKED, NULL);
    lv_obj_t *l_next = lv_label_create(btn_next);
    lv_label_set_text(l_next, LV_SYMBOL_NEXT);
    lv_obj_set_style_text_color(l_next, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_center(l_next);

    // Botón Stop
    lv_obj_t *btn_stop = lv_button_create(ctrl_bar);
    lv_obj_set_size(btn_stop, 40, 40);
    lv_obj_set_pos(btn_stop, 395, 16);
    lv_obj_set_style_bg_color(btn_stop, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(btn_stop, LV_RADIUS_CIRCLE, 0);
    lv_obj_add_event_cb(btn_stop, on_btn_stop_click, LV_EVENT_CLICKED, NULL);
    lv_obj_t *l_stop = lv_label_create(btn_stop);
    lv_label_set_text(l_stop, LV_SYMBOL_STOP);
    lv_obj_set_style_text_color(l_stop, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_center(l_stop);
}

// -------------------------------------------------------------
// Construcción de Pantalla Modo Fullscreen (480x320 con OSD HUD)
// -------------------------------------------------------------
static void build_fullscreen_screen(void) {
    s_scr_fullscreen = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(s_scr_fullscreen, lv_color_black(), 0);

    // Canvas de Video Fullscreen
    s_canvas_fullscreen = lv_canvas_create(s_scr_fullscreen);
    lv_canvas_set_buffer(s_canvas_fullscreen, s_buf_fullscreen[0], FULL_W, FULL_H, LV_COLOR_FORMAT_RGB565);
    lv_obj_set_size(s_canvas_fullscreen, FULL_W, FULL_H);
    lv_obj_set_pos(s_canvas_fullscreen, 0, 0);
    lv_obj_add_event_cb(s_canvas_fullscreen, on_fullscreen_tap, LV_EVENT_CLICKED, NULL);

    // OSD HUD Overlay Flotante
    s_hud_overlay = lv_obj_create(s_scr_fullscreen);
    lv_obj_set_size(s_hud_overlay, 480, FULL_H);
    lv_obj_set_pos(s_hud_overlay, 0, 0);
    lv_obj_set_style_bg_opa(s_hud_overlay, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(s_hud_overlay, 0, 0);
    lv_obj_set_style_pad_all(s_hud_overlay, 0, 0);
    lv_obj_add_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);

    // Barra superior flotante OSD (Título + FPS)
    lv_obj_t *top_bar = lv_obj_create(s_hud_overlay);
    lv_obj_set_size(top_bar, 460, 36);
    lv_obj_set_pos(top_bar, 10, 10);
    lv_obj_set_style_bg_color(top_bar, COLOR_SPOTIFY_CARD, 0);
    lv_obj_set_style_bg_opa(top_bar, LV_OPA_80, 0);
    lv_obj_set_style_radius(top_bar, 18, 0);
    lv_obj_set_style_border_width(top_bar, 1, 0);
    lv_obj_set_style_border_color(top_bar, COLOR_SPOTIFY_SURFACE, 0);

    s_hud_lbl_title = lv_label_create(top_bar);
    lv_label_set_text(s_hud_lbl_title, g_playlist[0].title);
    lv_obj_set_style_text_color(s_hud_lbl_title, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_set_pos(s_hud_lbl_title, 16, 8);

    s_hud_lbl_fps = lv_label_create(top_bar);
    lv_label_set_text(s_hud_lbl_fps, "30.0 FPS");
    lv_obj_set_style_text_color(s_hud_lbl_fps, COLOR_SPOTIFY_GREEN_GLOW, 0);
    lv_obj_set_pos(s_hud_lbl_fps, 390, 8);

    // Barra inferior flotante OSD (Controles + Seek + Salir)
    lv_obj_t *bot_bar = lv_obj_create(s_hud_overlay);
    lv_obj_set_size(bot_bar, 460, 58);
    lv_obj_set_pos(bot_bar, 10, 252);
    lv_obj_set_style_bg_color(bot_bar, COLOR_SPOTIFY_CARD, 0);
    lv_obj_set_style_bg_opa(bot_bar, LV_OPA_90, 0);
    lv_obj_set_style_radius(bot_bar, 20, 0);
    lv_obj_set_style_border_width(bot_bar, 1, 0);
    lv_obj_set_style_border_color(bot_bar, COLOR_SPOTIFY_SURFACE, 0);

    // Botón Prev OSD
    lv_obj_t *hud_prev = lv_button_create(bot_bar);
    lv_obj_set_size(hud_prev, 36, 36);
    lv_obj_set_pos(hud_prev, 10, 10);
    lv_obj_set_style_bg_color(hud_prev, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(hud_prev, LV_RADIUS_CIRCLE, 0);
    lv_obj_add_event_cb(hud_prev, on_btn_prev_click, LV_EVENT_CLICKED, NULL);
    lv_obj_t *lp = lv_label_create(hud_prev);
    lv_label_set_text(lp, LV_SYMBOL_PREV);
    lv_obj_set_style_text_color(lp, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_center(lp);

    // Botón Play/Pause OSD
    s_hud_btn_play = lv_button_create(bot_bar);
    lv_obj_set_size(s_hud_btn_play, 42, 42);
    lv_obj_set_pos(s_hud_btn_play, 56, 7);
    lv_obj_set_style_bg_color(s_hud_btn_play, COLOR_SPOTIFY_GREEN, 0);
    lv_obj_set_style_radius(s_hud_btn_play, LV_RADIUS_CIRCLE, 0);
    lv_obj_add_event_cb(s_hud_btn_play, on_btn_play_pause_click, LV_EVENT_CLICKED, NULL);

    s_hud_lbl_play = lv_label_create(s_hud_btn_play);
    lv_label_set_text(s_hud_lbl_play, LV_SYMBOL_PAUSE);
    lv_obj_set_style_text_color(s_hud_lbl_play, COLOR_SPOTIFY_BLACK, 0);
    lv_obj_center(s_hud_lbl_play);

    // Botón Next OSD
    lv_obj_t *hud_next = lv_button_create(bot_bar);
    lv_obj_set_size(hud_next, 36, 36);
    lv_obj_set_pos(hud_next, 108, 10);
    lv_obj_set_style_bg_color(hud_next, COLOR_SPOTIFY_SURFACE, 0);
    lv_obj_set_style_radius(hud_next, LV_RADIUS_CIRCLE, 0);
    lv_obj_add_event_cb(hud_next, on_btn_next_click, LV_EVENT_CLICKED, NULL);
    lv_obj_t *ln = lv_label_create(hud_next);
    lv_label_set_text(ln, LV_SYMBOL_NEXT);
    lv_obj_set_style_text_color(ln, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_center(ln);

    // Slider OSD Fullscreen
    s_hud_slider = lv_slider_create(bot_bar);
    lv_obj_set_size(s_hud_slider, 175, 6);
    lv_obj_set_pos(s_hud_slider, 156, 25);
    lv_slider_set_range(s_hud_slider, 0, 100);
    lv_obj_set_style_bg_color(s_hud_slider, COLOR_SPOTIFY_DARKGRAY, LV_PART_MAIN);
    lv_obj_set_style_bg_color(s_hud_slider, COLOR_SPOTIFY_GREEN, LV_PART_INDICATOR);
    lv_obj_set_style_bg_color(s_hud_slider, COLOR_SPOTIFY_WHITE, LV_PART_KNOB);
    lv_obj_set_style_pad_all(s_hud_slider, 3, LV_PART_KNOB);
    lv_obj_add_event_cb(s_hud_slider, on_slider_event, LV_EVENT_ALL, NULL);

    s_hud_lbl_time = lv_label_create(bot_bar);
    lv_label_set_text(s_hud_lbl_time, "00:00");
    lv_obj_set_style_text_color(s_hud_lbl_time, COLOR_SPOTIFY_GRAY, 0);
    lv_obj_set_pos(s_hud_lbl_time, 156, 8);

    // Botón Salir de Fullscreen [✖ SALIR]
    lv_obj_t *btn_exit = lv_button_create(bot_bar);
    lv_obj_set_size(btn_exit, 95, 34);
    lv_obj_set_pos(btn_exit, 345, 11);
    lv_obj_set_style_bg_color(btn_exit, lv_color_hex(0xE91429), 0);
    lv_obj_set_style_radius(btn_exit, 17, 0);
    lv_obj_add_event_cb(btn_exit, on_btn_fullscreen_toggle, LV_EVENT_CLICKED, NULL);

    lv_obj_t *l_exit = lv_label_create(btn_exit);
    lv_label_set_text(l_exit, "[X] SALIR");
    lv_obj_set_style_text_color(l_exit, COLOR_SPOTIFY_WHITE, 0);
    lv_obj_center(l_exit);
}

// -------------------------------------------------------------
// API Pública de Spotify UI
// -------------------------------------------------------------
void spotify_ui_init(track_change_cb_t track_cb, playback_ctrl_cb_t play_cb, seek_cb_t seek_cb) {
    s_track_cb = track_cb;
    s_play_cb = play_cb;
    s_seek_cb = seek_cb;

    // Asignar doble búfer en PSRAM para Studio (240x160 RGB565)
    for (int i = 0; i < 2; i++) {
        if (!s_buf_studio[i]) {
            s_buf_studio[i] = (uint16_t *)heap_caps_aligned_alloc(64, STUDIO_W * STUDIO_H * 2, MALLOC_CAP_SPIRAM);
            assert(s_buf_studio[i] != NULL);
            memset(s_buf_studio[i], 0, STUDIO_W * STUDIO_H * 2);
        }
    }

    // Asignar doble búfer en PSRAM para Fullscreen (480x320 RGB565)
    for (int i = 0; i < 2; i++) {
        if (!s_buf_fullscreen[i]) {
            s_buf_fullscreen[i] = (uint16_t *)heap_caps_aligned_alloc(64, FULL_W * FULL_H * 2, MALLOC_CAP_SPIRAM);
            assert(s_buf_fullscreen[i] != NULL);
            memset(s_buf_fullscreen[i], 0, FULL_W * FULL_H * 2);
        }
    }

    build_studio_screen();
    build_fullscreen_screen();

    lv_screen_load(s_scr_studio);
    s_view_mode = VIEW_MODE_STUDIO;

    // Vista inicial coherente (X2): enviar PCMD_SET_VIDEO_RECT coherente con STUDIO (240x160)
    player_cmd_t cmd = {
        .type = PCMD_SET_VIDEO_RECT,
        .rect = {10, 34, STUDIO_W, STUDIO_H}
    };
    player_cmd_send(&cmd);
}

void spotify_ui_update_progress(uint32_t elapsed_sec, uint32_t duration_sec, int percent) {
    if (!s_slider_user_dragging) {
        char buf_cur[16];
        char buf_dur[16];
        snprintf(buf_cur, sizeof(buf_cur), "%02u:%02u", (unsigned int)(elapsed_sec / 60), (unsigned int)(elapsed_sec % 60));
        snprintf(buf_dur, sizeof(buf_dur), "%02u:%02u", (unsigned int)(duration_sec / 60), (unsigned int)(duration_sec % 60));

        if (s_lbl_time_cur) lv_label_set_text(s_lbl_time_cur, buf_cur);
        if (s_lbl_time_dur) lv_label_set_text(s_lbl_time_dur, buf_dur);
        if (s_slider) lv_slider_set_value(s_slider, percent, LV_ANIM_OFF);

        if (s_hud_lbl_time) {
            char hud_time_str[64];
            snprintf(hud_time_str, sizeof(hud_time_str), "%s / %s", buf_cur, buf_dur);
            lv_label_set_text(s_hud_lbl_time, hud_time_str);
        }
        if (s_hud_slider) lv_slider_set_value(s_hud_slider, percent, LV_ANIM_OFF);
    }

    // Ocultar / auto-ocultar HUD OSD en Fullscreen segun modo forzado
    if (s_view_mode == VIEW_MODE_FULLSCREEN && s_hud_overlay) {
        if (s_hud_forced_mode == 1) {
            if (!lv_obj_has_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN)) {
                lv_obj_add_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
            }
        } else if (s_hud_forced_mode == 2) {
            if (lv_obj_has_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN)) {
                lv_obj_remove_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
            }
        } else {
            if (!lv_obj_has_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN)) {
                if (esp_timer_get_time() - s_last_touch_hud_time > 3500000) {
                    lv_obj_add_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
                }
            }
        }
    }
}

void spotify_ui_update_fps(float fps) {
    char buf[32];
    snprintf(buf, sizeof(buf), "%.1f FPS • SIMD ESP32-S3", fps);
    if (s_lbl_fps_studio) lv_label_set_text(s_lbl_fps_studio, buf);

    char buf_hud[16];
    snprintf(buf_hud, sizeof(buf_hud), "%.1f FPS", fps);
    if (s_hud_lbl_fps) lv_label_set_text(s_hud_lbl_fps, buf_hud);
}

void spotify_ui_tick(void) {
    // Animación suave de las 4 barras del ecualizador
    if (s_play_state == PLAYBACK_STATE_PLAYING) {
        s_eq_step++;
        static const uint8_t wave[4][8] = {
            {4, 8, 14, 10, 6, 12, 16, 8},
            {12, 16, 8, 4, 14, 10, 6, 12},
            {8, 4, 12, 16, 8, 14, 10, 6},
            {14, 10, 6, 12, 16, 8, 4, 8},
        };
        for (int i = 0; i < 4; i++) {
            if (s_eq_bars[i]) {
                uint8_t h = wave[i][s_eq_step % 8];
                lv_obj_set_size(s_eq_bars[i], 3, h);
                lv_obj_set_pos(s_eq_bars[i], 180 + i * 5, 20 - h);
            }
        }
    } else {
        for (int i = 0; i < 4; i++) {
            if (s_eq_bars[i]) {
                lv_obj_set_size(s_eq_bars[i], 3, 3);
                lv_obj_set_pos(s_eq_bars[i], 180 + i * 5, 17);
            }
        }
    }
}

void spotify_ui_set_track(int index) {
    if (index < 0 || index >= PLAYLIST_SIZE) return;
    s_current_track_idx = index;

    if (s_lbl_title) lv_label_set_text(s_lbl_title, g_playlist[index].title);
    if (s_lbl_artist) lv_label_set_text(s_lbl_artist, g_playlist[index].artist);
    if (s_hud_lbl_title) lv_label_set_text(s_hud_lbl_title, g_playlist[index].title);
    if (s_dropdown_tracks) lv_dropdown_set_selected(s_dropdown_tracks, index);
}

void spotify_ui_set_play_state(playback_state_t state) {
    s_play_state = state;
    const char *sym = (state == PLAYBACK_STATE_PLAYING) ? LV_SYMBOL_PAUSE : LV_SYMBOL_PLAY;
    if (s_lbl_play_pause) lv_label_set_text(s_lbl_play_pause, sym);
    if (s_hud_lbl_play) lv_label_set_text(s_hud_lbl_play, sym);
}

void spotify_ui_set_view_mode(view_mode_t mode) {
    s_view_mode = mode;
    if (mode == VIEW_MODE_STUDIO) {
        lv_screen_load(s_scr_studio);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {10, 34, STUDIO_W, STUDIO_H}};
        player_cmd_send(&cmd);
    } else {
        lv_screen_load(s_scr_fullscreen);
        if (s_hud_overlay) {
            if (s_hud_forced_mode == 1) {
                lv_obj_add_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
            } else {
                lv_obj_remove_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
                s_last_touch_hud_time = esp_timer_get_time();
            }
        }
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, FULL_W, FULL_H}};
        player_cmd_send(&cmd);
    }
}

void spotify_ui_set_hud_forced(int mode) {
    s_hud_forced_mode = mode;
    if (s_view_mode == VIEW_MODE_FULLSCREEN && s_hud_overlay) {
        if (mode == 1) {
            lv_obj_add_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
        } else if (mode == 2) {
            lv_obj_remove_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN);
        }
    }
}

view_mode_t spotify_ui_get_view_mode(void) {
    return s_view_mode;
}

playback_state_t spotify_ui_get_play_state(void) {
    return s_play_state;
}

uint16_t *spotify_ui_get_studio_buffer(void) {
    return s_buf_studio[s_studio_write_idx];
}

uint16_t *spotify_ui_get_fullscreen_buffer(void) {
    return s_buf_fullscreen[s_fs_write_idx];
}

void spotify_ui_commit_frame(void) {
    if (s_view_mode == VIEW_MODE_STUDIO) {
        s_studio_read_idx = s_studio_write_idx;
        s_studio_write_idx = (s_studio_write_idx + 1) % 2;
    } else {
        s_fs_read_idx = s_fs_write_idx;
        s_fs_write_idx = (s_fs_write_idx + 1) % 2;
    }
}

void spotify_ui_invalidate_video(void) {
    if (s_view_mode == VIEW_MODE_STUDIO && s_canvas_studio) {
        lv_canvas_set_buffer(s_canvas_studio, s_buf_studio[s_studio_read_idx], STUDIO_W, STUDIO_H, LV_COLOR_FORMAT_RGB565);
        lv_obj_invalidate(s_canvas_studio);
    } else if (s_view_mode == VIEW_MODE_FULLSCREEN && s_canvas_fullscreen) {
        lv_canvas_set_buffer(s_canvas_fullscreen, s_buf_fullscreen[s_fs_read_idx], FULL_W, FULL_H, LV_COLOR_FORMAT_RGB565);
        lv_obj_invalidate(s_canvas_fullscreen);
    }
}

bool spotify_ui_display_frame(uint16_t *buf, int width, int height) {
    if (!buf) return false;
    if (s_view_mode == VIEW_MODE_STUDIO) {
        if (width != STUDIO_W || height != STUDIO_H) {
            perf_mark_frame_mismatch();
            return false;
        }
        if (s_canvas_studio) {
            lv_canvas_set_buffer(s_canvas_studio, buf, STUDIO_W, STUDIO_H, LV_COLOR_FORMAT_RGB565);
            lv_obj_invalidate(s_canvas_studio);
            return true;
        }
    } else if (s_view_mode == VIEW_MODE_FULLSCREEN) {
        if (width != FULL_W || height != FULL_H) {
            perf_mark_frame_mismatch();
            return false;
        }
        if (s_canvas_fullscreen) {
            lv_canvas_set_buffer(s_canvas_fullscreen, buf, FULL_W, FULL_H, LV_COLOR_FORMAT_RGB565);
            lv_obj_invalidate(s_canvas_fullscreen);
            return true;
        }
    }
    return false;
}

void spotify_ui_update_from_status(const player_status_t *status) {
    if (!status) return;

    if (status->track_index >= 0 && status->track_index < PLAYLIST_SIZE) {
        s_current_track_idx = status->track_index;
    }

    // 1. Titulo y artista
    if (s_lbl_title && status->title[0] != '\0') {
        lv_label_set_text(s_lbl_title, status->title);
    }
    if (s_hud_lbl_title && status->title[0] != '\0') {
        lv_label_set_text(s_hud_lbl_title, status->title);
    }
    if (s_lbl_artist && status->subtitle[0] != '\0') {
        lv_label_set_text(s_lbl_artist, status->subtitle);
    }

    // 2. Dropdown
    if (s_dropdown_tracks && status->track_index >= 0 && status->track_index < PLAYLIST_SIZE) {
        if (lv_dropdown_get_selected(s_dropdown_tracks) != (uint32_t)status->track_index) {
            lv_dropdown_set_selected(s_dropdown_tracks, (uint32_t)status->track_index);
        }
    }

    // 3. Play / Pause estado e icono
    playback_state_t new_st = (status->state == PST_PLAYING) ? PLAYBACK_STATE_PLAYING :
                              ((status->state == PST_PAUSED) ? PLAYBACK_STATE_PAUSED : PLAYBACK_STATE_STOPPED);
    s_play_state = new_st;
    const char *sym = (new_st == PLAYBACK_STATE_PLAYING) ? LV_SYMBOL_PAUSE : LV_SYMBOL_PLAY;
    if (s_lbl_play_pause) lv_label_set_text(s_lbl_play_pause, sym);
    if (s_hud_lbl_play) lv_label_set_text(s_hud_lbl_play, sym);

    // 4. Progreso y tiempo
    uint32_t elapsed_sec = (uint32_t)(status->pos_ms / 1000);
    uint32_t duration_sec = (uint32_t)(status->dur_ms / 1000);
    int percent = (status->dur_ms > 0) ? (int)((status->pos_ms * 100) / status->dur_ms) : 0;
    spotify_ui_update_progress(elapsed_sec, duration_sec, percent);

    // 5. FPS
    spotify_ui_update_fps(status->pres_fps);

    // 6. Animacion de ecualizador si esta en PLAYING
    if (status->state == PST_PLAYING) {
        spotify_ui_tick();
    }
}

void spotify_ui_get_published_info(char *title_buf, size_t max_len, int *track_idx, view_mode_t *vmode, int *hud_vis) {
    if (vmode) *vmode = s_view_mode;
    if (track_idx) *track_idx = s_current_track_idx;

    if (title_buf && max_len > 0) {
        const char *txt = "";
        if (s_view_mode == VIEW_MODE_FULLSCREEN) {
            if (s_hud_lbl_title) {
                txt = lv_label_get_text(s_hud_lbl_title);
            }
        } else {
            if (s_lbl_title) {
                txt = lv_label_get_text(s_lbl_title);
            }
        }
        if (!txt) txt = "";
        snprintf(title_buf, max_len, "%s", txt);
    }

    if (hud_vis) {
        if (s_view_mode == VIEW_MODE_FULLSCREEN && s_hud_overlay) {
            *hud_vis = lv_obj_has_flag(s_hud_overlay, LV_OBJ_FLAG_HIDDEN) ? 0 : 1;
        } else {
            *hud_vis = 0;
        }
    }
}
