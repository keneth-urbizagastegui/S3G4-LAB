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
static uint32_t s_frames_dropped = 0;    // Siempre 0 en F0
static uint32_t s_oversize_frames = 0;

static uint64_t s_read_sum_us = 0;
static uint32_t s_read_count = 0;
static uint32_t s_read_max_us = 0;

static uint64_t s_decode_sum_us = 0;
static uint32_t s_decode_count = 0;
static uint32_t s_decode_max_us = 0;

static uint64_t s_blit_sum_us = 0;
static uint32_t s_blit_count = 0;
static uint32_t s_blit_max_us = 0;

static uint32_t s_late_max_us = 0;       // Siempre 0 en F0

static int s_track = 0;
static char s_scn[32] = "init";

static int64_t s_last_report_us = 0;

void perf_init(void) {
    portENTER_CRITICAL(&s_perf_mux);
    s_frames_decoded = 0;
    s_frames_presented = 0;
    s_frames_dropped = 0;
    s_oversize_frames = 0;
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

    uint64_t rd_sum = s_read_sum_us;
    uint32_t rd_cnt = s_read_count;
    uint32_t rd_max = s_read_max_us;

    uint64_t dec_sum = s_decode_sum_us;
    uint32_t dec_cnt = s_decode_count;
    uint32_t dec_max = s_decode_max_us;

    uint64_t blit_sum = s_blit_sum_us;
    uint32_t blit_cnt = s_blit_count;
    uint32_t blit_max = s_blit_max_us;

    uint32_t late_max = s_late_max_us;
    int track = s_track;
    char scn[32];
    strncpy(scn, s_scn, sizeof(scn));
    scn[sizeof(scn) - 1] = '\0';

    // Reiniciar contadores para la siguiente ventana
    s_frames_decoded = 0;
    s_frames_presented = 0;
    s_frames_dropped = 0;
    s_oversize_frames = 0;

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

    s_last_report_us = now;
    portEXIT_CRITICAL(&s_perf_mux);

    double dec_fps = (window_us > 0) ? ((double)dec * 1000000.0 / (double)window_us) : 0.0;
    double pres_fps = (window_us > 0) ? ((double)pres * 1000000.0 / (double)window_us) : 0.0;
    uint32_t rd_avg = (rd_cnt > 0) ? (uint32_t)(rd_sum / rd_cnt) : 0;
    uint32_t dec_avg = (dec_cnt > 0) ? (uint32_t)(dec_sum / dec_cnt) : 0;
    uint32_t blit_avg = (blit_cnt > 0) ? (uint32_t)(blit_sum / blit_cnt) : 0;

    uint32_t heap_int = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    uint32_t heap_psram = (uint32_t)heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    uint32_t t_ms = (uint32_t)(now / 1000);

    printf("PERF,t_ms=%lu,dec_fps=%.2f,pres_fps=%.2f,drop=%lu,over=%lu,rd_avg=%lu,rd_max=%lu,dec_avg=%lu,dec_max=%lu,blit_avg=%lu,blit_max=%lu,late_max=%lu,heap_int=%lu,heap_psram=%lu,track=%d,scn=%s\n",
           (unsigned long)t_ms, dec_fps, pres_fps, (unsigned long)drop, (unsigned long)over,
           (unsigned long)rd_avg, (unsigned long)rd_max,
           (unsigned long)dec_avg, (unsigned long)dec_max,
           (unsigned long)blit_avg, (unsigned long)blit_max,
           (unsigned long)late_max,
           (unsigned long)heap_int, (unsigned long)heap_psram,
           track, scn);
    fflush(stdout);
}
