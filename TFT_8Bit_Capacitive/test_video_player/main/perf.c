#include "perf.h"
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"

static portMUX_TYPE s_perf_mux = portMUX_INITIALIZER_UNLOCKED;

// Contadores en ventana de reporte
static uint32_t s_frames_decoded = 0;
static uint32_t s_frames_presented = 0;
static uint32_t s_frames_dropped = 0;    // Siempre 0 en F0/F1
static uint32_t s_oversize_frames = 0;
static uint32_t s_frame_mismatch = 0;

static uint64_t s_read_sum_us = 0;
static uint32_t s_read_count = 0;
static uint32_t s_read_max_us = 0;

static uint64_t s_decode_sum_us = 0;
static uint32_t s_decode_count = 0;
static uint32_t s_decode_max_us = 0;

static uint64_t s_blit_sum_us = 0;
static uint32_t s_blit_count = 0;
static uint32_t s_blit_max_us = 0;

static uint32_t s_late_max_us = 0;
static int32_t s_last_drift_ms = 0;

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
    s_decode_sum_us = 0;
    s_decode_count = 0;
    s_decode_max_us = 0;
    s_blit_sum_us = 0;
    s_blit_count = 0;
    s_blit_max_us = 0;
    s_late_max_us = 0;
    s_last_drift_ms = 0;
    s_touch_rd_sum_us = 0;
    s_touch_rd_count = 0;
    s_touch_rd_max_us = 0;
    s_touch_age_max_us = 0;
    s_last_dec_fps = 0.0f;
    s_last_pres_fps = 0.0f;
    s_last_report_us = esp_timer_get_time();
    portEXIT_CRITICAL(&s_perf_mux);
}

void perf_mark_read(uint32_t us) {
    portENTER_CRITICAL(&s_perf_mux);
    s_read_sum_us += us;
    s_read_count++;
    if (us > s_read_max_us) {
        s_read_max_us = us;
    }
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

    int track = s_track;
    char scn[32];
    strncpy(scn, s_scn, sizeof(scn));
    scn[sizeof(scn) - 1] = '\0';

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

    s_touch_rd_sum_us = 0;
    s_touch_rd_count = 0;
    s_touch_rd_max_us = 0;
    s_touch_age_max_us = 0;

    s_last_report_us = now;
    portEXIT_CRITICAL(&s_perf_mux);

    double dec_fps = (window_us > 0) ? ((double)dec * 1000000.0 / (double)window_us) : 0.0;
    double pres_fps = (window_us > 0) ? ((double)pres * 1000000.0 / (double)window_us) : 0.0;
    double rd_avg = (rd_cnt > 0) ? (((double)rd_sum / (double)rd_cnt) / 1000.0) : 0.0;
    double dec_avg = (dec_cnt > 0) ? (((double)dec_sum / (double)dec_cnt) / 1000.0) : 0.0;
    double blit_avg = (blit_cnt > 0) ? (((double)blit_sum / (double)blit_cnt) / 1000.0) : 0.0;
    double rd_max = (double)rd_max_us / 1000.0;
    double dec_max = (double)dec_max_us / 1000.0;
    double blit_max = (double)blit_max_us / 1000.0;
    double late_max = (double)late_max_us / 1000.0;

    double touch_read_ms_avg = (touch_rd_cnt > 0) ? (((double)touch_rd_sum / (double)touch_rd_cnt) / 1000.0) : 0.0;
    double touch_read_ms_max = (double)touch_rd_max_us / 1000.0;
    double touch_age_ms_max = (double)touch_age_max_us / 1000.0;

    portENTER_CRITICAL(&s_perf_mux);
    s_last_dec_fps = (float)dec_fps;
    s_last_pres_fps = (float)pres_fps;
    portEXIT_CRITICAL(&s_perf_mux);

    char view_str[16] = "studio";
    int hud_val = 0;
    perf_get_ui_state(view_str, sizeof(view_str), &hud_val);

    uint32_t heap_int = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    uint32_t heap_psram = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    uint32_t t_ms = (uint32_t)(now / 1000);

    printf("PERF,t_ms=%lu,dec_fps=%.1f,pres_fps=%.1f,drop=%lu,over=%lu,frame_mismatch=%lu,rd_avg=%.1f,rd_max=%.1f,dec_avg=%.1f,dec_max=%.1f,blit_avg=%.1f,blit_max=%.1f,late_max=%.1f,drift_ms=%ld,touch_read_ms_avg=%.1f,touch_read_ms_max=%.1f,touch_age_ms_max=%.1f,heap_int=%lu,heap_psram=%lu,track=%d,scn=%s,view=%s,hud=%d\n",
           (unsigned long)t_ms, dec_fps, pres_fps, (unsigned long)drop, (unsigned long)over,
           (unsigned long)mismatch,
           rd_avg, rd_max,
           dec_avg, dec_max,
           blit_avg, blit_max,
           late_max,
           (long)drift_ms,
           touch_read_ms_avg, touch_read_ms_max, touch_age_ms_max,
           (unsigned long)heap_int, (unsigned long)heap_psram,
           track, scn,
           view_str, hud_val);
    fflush(stdout);
}
