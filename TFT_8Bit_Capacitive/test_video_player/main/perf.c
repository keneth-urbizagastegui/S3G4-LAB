#include "perf.h"
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "lcd_bus.h"
#include "ili9488_8080.h"

static portMUX_TYPE s_perf_mux = portMUX_INITIALIZER_UNLOCKED;

// Contadores en ventana de reporte
static uint32_t s_frames_decoded = 0;
static uint32_t s_frames_presented = 0;
static uint32_t s_frames_dropped = 0;
static uint32_t s_oversize_frames = 0;
static uint32_t s_frame_mismatch = 0;

static uint64_t s_read_sum_us = 0;
static uint32_t s_read_count = 0;
static uint32_t s_read_max_us = 0;
#define RD_SAMPLES_MAX 128
static uint32_t s_rd_samples[RD_SAMPLES_MAX];
static uint32_t s_rd_samples_cnt = 0;
static uint32_t s_rd_slow_count = 0;

// Lectura real de SD en avi_reader_task (P3c)
static uint64_t s_reader_rd_sum_us = 0;
static uint32_t s_reader_rd_count = 0;
static uint32_t s_reader_rd_max_us = 0;
static uint32_t s_reader_rd_samples[RD_SAMPLES_MAX];
static uint32_t s_reader_rd_samples_cnt = 0;

static uint64_t s_slots_ready_sum = 0;
static uint32_t s_slots_ready_count = 0;

// Sincronización TE (P1/P2)
static uint64_t s_te_wait_sum_us = 0;
static uint32_t s_te_wait_count = 0;
static uint32_t s_te_wait_max_us = 0;
static uint32_t s_te_timeout_count = 0;

static uint64_t s_decode_sum_us = 0;
static uint32_t s_decode_count = 0;
static uint32_t s_decode_max_us = 0;
static uint64_t s_frame_dec_sum_us = 0;
static uint32_t s_frame_dec_count = 0;
static uint32_t s_frame_dec_max_us = 0;

static uint64_t s_blit_sum_us = 0;
static uint32_t s_blit_count = 0;
static uint32_t s_blit_max_us = 0;

static uint32_t s_late_max_us = 0;
static int32_t s_last_drift_ms = 0;

// Métricas de franjas y recorte direct F3
static char s_present_path_override[16] = "";
static int s_vrect_override_y1 = -1;
static int s_vrect_override_y2 = -1;

static uint32_t s_strip_count = 0;
static uint64_t s_strip_sum_us = 0;

static uint32_t s_direct_frames_count = 0;
static uint32_t s_total_strips_sent = 0;
static uint64_t s_frame_blit_sum_us = 0;

static uint32_t s_lvgl_rows_clipped = 0;

// Latencia táctil (T1)
static uint64_t s_touch_rd_sum_us = 0;
static uint32_t s_touch_rd_count = 0;
static uint32_t s_touch_rd_max_us = 0;

static uint32_t s_touch_age_max_us = 0;

static float s_last_dec_fps = 0.0f;
static float s_last_pres_fps = 0.0f;

static int s_track = 0;
static char s_scn[32] = "init";

static int64_t s_last_report_us = 0;

void perf_set_present_path(const char *path) {
    if (!path) return;
    portENTER_CRITICAL(&s_perf_mux);
    strncpy(s_present_path_override, path, sizeof(s_present_path_override) - 1);
    s_present_path_override[sizeof(s_present_path_override) - 1] = '\0';
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_set_vrect(int y1, int y2) {
    portENTER_CRITICAL(&s_perf_mux);
    s_vrect_override_y1 = y1;
    s_vrect_override_y2 = y2;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_strip(uint32_t strip_us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_strip_count++;
    s_strip_sum_us += strip_us;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_direct_frame(uint32_t strips_count, uint32_t frame_blit_us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_direct_frames_count++;
    s_total_strips_sent += strips_count;
    s_frame_blit_sum_us += frame_blit_us;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_lvgl_clipped(uint32_t rows) {
    portENTER_CRITICAL(&s_perf_mux);
    s_lvgl_rows_clipped += rows;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_init(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frames_decoded = 0;
    s_frames_presented = 0;
    s_frames_dropped = 0;
    s_oversize_frames = 0;
    s_frame_mismatch = 0;
    s_read_sum_us = 0;
    s_read_count = 0;
    s_read_max_us = 0;
    s_rd_samples_cnt = 0;
    s_rd_slow_count = 0;
    s_reader_rd_sum_us = 0;
    s_reader_rd_count = 0;
    s_reader_rd_max_us = 0;
    s_reader_rd_samples_cnt = 0;
    s_slots_ready_sum = 0;
    s_slots_ready_count = 0;
    s_te_wait_sum_us = 0;
    s_te_wait_count = 0;
    s_te_wait_max_us = 0;
    s_te_timeout_count = 0;
    s_decode_sum_us = 0;
    s_decode_count = 0;
    s_decode_max_us = 0;
    s_frame_dec_sum_us = 0;
    s_frame_dec_count = 0;
    s_frame_dec_max_us = 0;
    s_blit_sum_us = 0;
    s_blit_count = 0;
    s_blit_max_us = 0;
    s_late_max_us = 0;
    s_last_drift_ms = 0;
    s_strip_count = 0;
    s_strip_sum_us = 0;
    s_direct_frames_count = 0;
    s_total_strips_sent = 0;
    s_frame_blit_sum_us = 0;
    s_lvgl_rows_clipped = 0;
    s_present_path_override[0] = '\0';
    s_vrect_override_y1 = -1;
    s_vrect_override_y2 = -1;
    s_touch_rd_sum_us = 0;
    s_touch_rd_count = 0;
    s_touch_rd_max_us = 0;
    s_touch_age_max_us = 0;
    s_last_dec_fps = 0.0f;
    s_last_pres_fps = 0.0f;
    s_last_report_us = esp_timer_get_time();
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_q_wait(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_read_sum_us += us;
    s_read_count++;
    if (us > s_read_max_us) {
        s_read_max_us = us;
    }
    if (s_rd_samples_cnt < RD_SAMPLES_MAX) {
        s_rd_samples[s_rd_samples_cnt++] = us;
    }
    if (us > 20000) {
        s_rd_slow_count++;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_read(uint32_t us) {
    perf_mark_q_wait(us);
}

void perf_mark_reader_read(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_reader_rd_sum_us += us;
    s_reader_rd_count++;
    if (us > s_reader_rd_max_us) {
        s_reader_rd_max_us = us;
    }
    if (s_reader_rd_samples_cnt < RD_SAMPLES_MAX) {
        s_reader_rd_samples[s_reader_rd_samples_cnt++] = us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_slots_ready(uint32_t count) {
    portENTER_CRITICAL(&s_perf_mux);
    s_slots_ready_sum += count;
    s_slots_ready_count++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_te_wait(uint32_t wait_us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_te_wait_sum_us += wait_us;
    s_te_wait_count++;
    if (wait_us > s_te_wait_max_us) {
        s_te_wait_max_us = wait_us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_te_timeout(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_te_timeout_count++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_decode(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_decode_sum_us += us;
    s_decode_count++;
    if (us > s_decode_max_us) {
        s_decode_max_us = us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_frame_decode(uint32_t frame_dec_us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frame_dec_sum_us += frame_dec_us;
    s_frame_dec_count++;
    if (frame_dec_us > s_frame_dec_max_us) {
        s_frame_dec_max_us = frame_dec_us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_decoded(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frames_decoded++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_presented(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frames_presented++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_blit(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_blit_sum_us += us;
    s_blit_count++;
    if (us > s_blit_max_us) {
        s_blit_max_us = us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_oversize(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_oversize_frames++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_frame_mismatch(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frame_mismatch++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_late(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    if (us > s_late_max_us) {
        s_late_max_us = us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_dropped(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frames_dropped++;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_drift(int32_t drift_ms) {
    portENTER_CRITICAL(&s_perf_mux);
    s_last_drift_ms = drift_ms;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_touch_read(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_touch_rd_sum_us += us;
    s_touch_rd_count++;
    if (us > s_touch_rd_max_us) {
        s_touch_rd_max_us = us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_touch_age(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    if (us > s_touch_age_max_us) {
        s_touch_age_max_us = us;
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_get_fps(float *dec_fps, float *pres_fps) {
    portENTER_CRITICAL(&s_perf_mux);
    if (dec_fps) *dec_fps = s_last_dec_fps;
    if (pres_fps) *pres_fps = s_last_pres_fps;
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_set_scenario(int track, const char *scn) {
    portENTER_CRITICAL(&s_perf_mux);
    s_track = track;
    if (scn) {
        strncpy(s_scn, scn, sizeof(s_scn) - 1);
        s_scn[sizeof(s_scn) - 1] = '\0';
    }
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_report_if_due(void) {
    int64_t now = esp_timer_get_time();
    if (s_last_report_us == 0) {
        s_last_report_us = now;
        return;
    }

    int64_t window_us = now - s_last_report_us;
    if (window_us < 2000000) {
        return;
    }

    portENTER_CRITICAL(&s_perf_mux);
    uint32_t dec = s_frames_decoded;
    uint32_t pres = s_frames_presented;
    uint32_t drop = s_frames_dropped;
    uint32_t over = s_oversize_frames;
    uint32_t mismatch = s_frame_mismatch;

    uint64_t rd_sum = s_read_sum_us;
    uint32_t rd_cnt = s_read_count;
    uint32_t rd_max_us = s_read_max_us;

    uint64_t reader_rd_sum = s_reader_rd_sum_us;
    uint32_t reader_rd_cnt = s_reader_rd_count;
    uint32_t reader_rd_max_us = s_reader_rd_max_us;
    uint32_t reader_rd_cnt_samples = s_reader_rd_samples_cnt;
    uint32_t reader_rd_samples_copy[RD_SAMPLES_MAX];
    if (reader_rd_cnt_samples > 0) {
        memcpy(reader_rd_samples_copy, s_reader_rd_samples, reader_rd_cnt_samples * sizeof(uint32_t));
    }
    s_reader_rd_sum_us = 0;
    s_reader_rd_count = 0;
    s_reader_rd_max_us = 0;
    s_reader_rd_samples_cnt = 0;

    uint64_t slots_ready_sum = s_slots_ready_sum;
    uint32_t slots_ready_cnt = s_slots_ready_count;
    s_slots_ready_sum = 0;
    s_slots_ready_count = 0;

    uint64_t te_wait_sum = s_te_wait_sum_us;
    uint32_t te_wait_cnt = s_te_wait_count;
    uint32_t te_wait_max_us = s_te_wait_max_us;
    uint32_t te_timeout_cnt = s_te_timeout_count;
    s_te_wait_sum_us = 0;
    s_te_wait_count = 0;
    s_te_wait_max_us = 0;
    s_te_timeout_count = 0;

    uint64_t dec_sum = s_decode_sum_us;
    uint32_t dec_cnt = s_decode_count;
    uint32_t dec_max_us = s_decode_max_us;

    uint64_t blit_sum = s_blit_sum_us;
    uint32_t blit_cnt = s_blit_count;
    uint32_t blit_max_us = s_blit_max_us;

    uint32_t late_max_us = s_late_max_us;
    int32_t drift_ms = s_last_drift_ms;

    uint64_t touch_rd_sum = s_touch_rd_sum_us;
    uint32_t touch_rd_cnt = s_touch_rd_count;
    uint32_t touch_rd_max_us = s_touch_rd_max_us;
    uint32_t touch_age_max_us = s_touch_age_max_us;

    uint32_t rd_slow = s_rd_slow_count;
    uint32_t rd_cnt_samples = s_rd_samples_cnt;
    uint32_t rd_samples_copy[RD_SAMPLES_MAX];
    if (rd_cnt_samples > 0) {
        memcpy(rd_samples_copy, s_rd_samples, rd_cnt_samples * sizeof(uint32_t));
    }
    s_rd_samples_cnt = 0;
    s_rd_slow_count = 0;

    uint64_t frame_dec_sum = s_frame_dec_sum_us;
    uint32_t frame_dec_cnt = s_frame_dec_count;
    uint32_t frame_dec_max_us = s_frame_dec_max_us;
    s_frame_dec_sum_us = 0;
    s_frame_dec_count = 0;
    s_frame_dec_max_us = 0;

    int track = s_track;
    char scn[32];
    strncpy(scn, s_scn, sizeof(scn));
    scn[sizeof(scn) - 1] = '\0';

    uint32_t strip_cnt = s_strip_count;
    uint64_t strip_sum = s_strip_sum_us;
    uint32_t dir_frames = s_direct_frames_count;
    uint32_t tot_strips = s_total_strips_sent;
    uint64_t frame_blit_sum = s_frame_blit_sum_us;
    uint32_t lvgl_clipped = s_lvgl_rows_clipped;

    // Reiniciar contadores para la siguiente ventana
    s_frames_decoded = 0;
    s_frames_presented = 0;
    s_frames_dropped = 0;
    s_oversize_frames = 0;
    s_frame_mismatch = 0;

    s_read_sum_us = 0;
    s_read_count = 0;
    s_read_max_us = 0;

    s_decode_sum_us = 0;
    s_decode_count = 0;
    s_decode_max_us = 0;

    s_blit_sum_us = 0;
    s_blit_count = 0;
    s_blit_max_us = 0;

    s_late_max_us = 0;

    s_strip_count = 0;
    s_strip_sum_us = 0;
    s_direct_frames_count = 0;
    s_total_strips_sent = 0;
    s_frame_blit_sum_us = 0;
    s_lvgl_rows_clipped = 0;

    s_touch_rd_sum_us = 0;
    s_touch_rd_count = 0;
    s_touch_rd_max_us = 0;
    s_touch_age_max_us = 0;

    s_last_report_us = now;
    portEXIT_CRITICAL(&s_perf_mux);

    // Muestreo de TE en la ventana
    uint32_t te_pulses = 0;
    float te_hz = 0.0f;
    float te_jitter_ms = 0.0f;
    bool te_present = false;
    lcd_bus_te_perf_sample(&te_pulses, &te_hz, &te_jitter_ms, &te_present);
    int te_present_int = te_present ? 1 : 0;

    double te_wait_ms_avg = (te_wait_cnt > 0) ? (((double)te_wait_sum / (double)te_wait_cnt) / 1000.0) : 0.0;
    double te_wait_ms_max = (double)te_wait_max_us / 1000.0;

    // Calcular percentiles q_wait (consumidor)
    for (uint32_t i = 1; i < rd_cnt_samples; i++) {
        uint32_t key = rd_samples_copy[i];
        int j = (int)i - 1;
        while (j >= 0 && rd_samples_copy[j] > key) {
            rd_samples_copy[j + 1] = rd_samples_copy[j];
            j--;
        }
        rd_samples_copy[j + 1] = key;
    }
    double q_wait_p50 = 0.0;
    double q_wait_p95 = 0.0;
    if (rd_cnt_samples > 0) {
        uint32_t idx50 = (rd_cnt_samples * 50) / 100;
        if (idx50 >= rd_cnt_samples) idx50 = rd_cnt_samples - 1;
        q_wait_p50 = (double)rd_samples_copy[idx50] / 1000.0;

        uint32_t idx95 = (rd_cnt_samples * 95) / 100;
        if (idx95 >= rd_cnt_samples) idx95 = rd_cnt_samples - 1;
        q_wait_p95 = (double)rd_samples_copy[idx95] / 1000.0;
    }
    double q_wait_avg = (rd_cnt > 0) ? (((double)rd_sum / (double)rd_cnt) / 1000.0) : 0.0;
    double q_wait_max = (double)rd_max_us / 1000.0;

    // Calcular percentiles reader_rd (lectura real de SD en Core 0)
    for (uint32_t i = 1; i < reader_rd_cnt_samples; i++) {
        uint32_t key = reader_rd_samples_copy[i];
        int j = (int)i - 1;
        while (j >= 0 && reader_rd_samples_copy[j] > key) {
            reader_rd_samples_copy[j + 1] = reader_rd_samples_copy[j];
            j--;
        }
        reader_rd_samples_copy[j + 1] = key;
    }
    double reader_rd_p50 = 0.0;
    double reader_rd_p95 = 0.0;
    if (reader_rd_cnt_samples > 0) {
        uint32_t idx50 = (reader_rd_cnt_samples * 50) / 100;
        if (idx50 >= reader_rd_cnt_samples) idx50 = reader_rd_cnt_samples - 1;
        reader_rd_p50 = (double)reader_rd_samples_copy[idx50] / 1000.0;

        uint32_t idx95 = (reader_rd_cnt_samples * 95) / 100;
        if (idx95 >= reader_rd_cnt_samples) idx95 = reader_rd_cnt_samples - 1;
        reader_rd_p95 = (double)reader_rd_samples_copy[idx95] / 1000.0;
    }
    double reader_rd_avg = (reader_rd_cnt > 0) ? (((double)reader_rd_sum / (double)reader_rd_cnt) / 1000.0) : 0.0;
    double reader_rd_max = (double)reader_rd_max_us / 1000.0;

    double slots_ready_avg = (slots_ready_cnt > 0) ? ((double)slots_ready_sum / (double)slots_ready_cnt) : 0.0;

    // rd_* se asigna a la lectura real del lector para consistencia
    double rd_avg = reader_rd_avg;
    double rd_max = reader_rd_max;
    double rd_p50 = reader_rd_p50;
    double rd_p95 = reader_rd_p95;

    double dec_frame_ms_avg = (frame_dec_cnt > 0) ? (((double)frame_dec_sum / (double)frame_dec_cnt) / 1000.0) : 0.0;
    double dec_frame_ms_max = (double)frame_dec_max_us / 1000.0;

    double dec_fps = (window_us > 0) ? ((double)dec * 1000000.0 / (double)window_us) : 0.0;
    double pres_fps = (window_us > 0) ? ((double)pres * 1000000.0 / (double)window_us) : 0.0;
    double dec_avg = (dec_cnt > 0) ? (((double)dec_sum / (double)dec_cnt) / 1000.0) : 0.0;
    double blit_avg = (blit_cnt > 0) ? (((double)blit_sum / (double)blit_cnt) / 1000.0) : 0.0;
    double dec_max = (double)dec_max_us / 1000.0;
    double blit_max = (double)blit_max_us / 1000.0;
    double late_max = (double)late_max_us / 1000.0;

    double touch_read_ms_avg = (touch_rd_cnt > 0) ? (((double)touch_rd_sum / (double)touch_rd_cnt) / 1000.0) : 0.0;
    double touch_read_ms_max = (double)touch_rd_max_us / 1000.0;
    double touch_age_ms_max = (double)touch_age_max_us / 1000.0;

    double strip_ms_avg = (strip_cnt > 0) ? (((double)strip_sum / (double)strip_cnt) / 1000.0) : 0.0;
    double frame_blit_ms_avg = (dir_frames > 0) ? (((double)frame_blit_sum / (double)dir_frames) / 1000.0) : 0.0;
    uint32_t strips_per_frame = (dir_frames > 0) ? (tot_strips / dir_frames) : 0;

    portENTER_CRITICAL(&s_perf_mux);
    s_last_dec_fps = (float)dec_fps;
    s_last_pres_fps = (float)pres_fps;
    portEXIT_CRITICAL(&s_perf_mux);

    char view_str[16] = "studio";
    int hud_val = 0;
    perf_get_ui_state(view_str, sizeof(view_str), &hud_val);

    char path_str[16] = "lvgl";
    int v_y1 = 0, v_y2 = 319;

    portENTER_CRITICAL(&s_perf_mux);
    if (s_present_path_override[0] != '\0') {
        strncpy(path_str, s_present_path_override, sizeof(path_str) - 1);
        path_str[sizeof(path_str) - 1] = '\0';
    } else if (strcmp(view_str, "full") == 0) {
        strncpy(path_str, "direct", sizeof(path_str) - 1);
        path_str[sizeof(path_str) - 1] = '\0';
    } else {
        strncpy(path_str, "lvgl", sizeof(path_str) - 1);
        path_str[sizeof(path_str) - 1] = '\0';
    }

    int ovr_y1 = s_vrect_override_y1;
    int ovr_y2 = s_vrect_override_y2;
    portEXIT_CRITICAL(&s_perf_mux);

    int16_t vx, vy, vw, vh;
    lcd_bus_get_video_rect(&vx, &vy, &vw, &vh);

    if (ovr_y1 >= 0 && ovr_y2 >= 0) {
        v_y1 = ovr_y1;
        v_y2 = ovr_y2;
    } else if (strcmp(path_str, "direct") == 0) {
        v_y1 = vy;
        v_y2 = (vh > 0) ? (vy + vh - 1) : vy;
    } else {
        v_y1 = 34;
        v_y2 = 193;
    }

    uint32_t heap_int = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    uint32_t heap_psram = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    uint32_t t_ms = (uint32_t)(now / 1000);
    uint8_t cur_madctl = ili9488_8080_get_madctl();

    printf("PERF,t_ms=%lu,dec_fps=%.1f,pres_fps=%.1f,drop=%lu,over=%lu,frame_mismatch=%lu,rd_avg=%.1f,rd_max=%.1f,rd_p50=%.1f,rd_p95=%.1f,rd_slow=%lu,reader_rd_avg=%.1f,reader_rd_max=%.1f,reader_rd_p50=%.1f,reader_rd_p95=%.1f,slots_ready_avg=%.1f,q_wait_avg=%.1f,q_wait_max=%.1f,q_wait_p50=%.1f,q_wait_p95=%.1f,te_present=%d,te_hz=%.1f,te_jitter_ms=%.2f,te_wait_ms_avg=%.2f,te_wait_ms_max=%.2f,te_timeout=%lu,dec_avg=%.1f,dec_max=%.1f,dec_frame_ms_avg=%.1f,dec_frame_ms_max=%.1f,blit_avg=%.1f,blit_max=%.1f,late_max=%.1f,drift_ms=%ld,touch_read_ms_avg=%.1f,touch_read_ms_max=%.1f,touch_age_ms_max=%.1f,heap_int=%lu,heap_psram=%lu,track=%d,scn=%s,view=%s,hud=%d,present_path=%s,rot=90,madctl=0x%02X,vrect=%d-%d,strips_per_frame=%lu,strip_ms_avg=%.2f,frame_blit_ms_avg=%.1f,lvgl_rows_clipped=%lu,dec_frames=%lu\n",
           (unsigned long)t_ms, dec_fps, pres_fps, (unsigned long)drop, (unsigned long)over,
           (unsigned long)mismatch,
           rd_avg, rd_max,
           rd_p50, rd_p95, (unsigned long)rd_slow,
           reader_rd_avg, reader_rd_max, reader_rd_p50, reader_rd_p95,
           slots_ready_avg,
           q_wait_avg, q_wait_max, q_wait_p50, q_wait_p95,
           te_present_int, (double)te_hz, (double)te_jitter_ms,
           te_wait_ms_avg, te_wait_ms_max, (unsigned long)te_timeout_cnt,
           dec_avg, dec_max,
           dec_frame_ms_avg, dec_frame_ms_max,
           blit_avg, blit_max,
           late_max,
           (long)drift_ms,
           touch_read_ms_avg, touch_read_ms_max, touch_age_ms_max,
           (unsigned long)heap_int, (unsigned long)heap_psram,
           track, scn,
           view_str, hud_val,
           path_str,
           (unsigned int)cur_madctl,
           v_y1, v_y2,
           (unsigned long)strips_per_frame,
           strip_ms_avg,
           frame_blit_ms_avg,
           (unsigned long)lvgl_clipped,
           (unsigned long)dec);
    fflush(stdout);
}
