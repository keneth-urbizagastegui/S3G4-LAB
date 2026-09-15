#ifndef PERF_H
#define PERF_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

void perf_init(void);
void perf_mark_read(uint32_t us);
void perf_mark_decode(uint32_t us);
void perf_mark_decoded(void);
void perf_mark_presented(void);
void perf_mark_blit(uint32_t us);
void perf_mark_oversize(void);
void perf_mark_frame_mismatch(void);
void perf_mark_late(uint32_t us);
void perf_mark_dropped(void);
void perf_mark_drift(int32_t drift_ms);
void perf_set_scenario(int track, const char *scn);
void perf_report_if_due(void);

// Métricas de latencia táctil (T1)
void perf_mark_touch_read(uint32_t us);
void perf_mark_touch_age(uint32_t us);

// Consulta de FPS calculados de la ventana actual
void perf_get_fps(float *dec_fps, float *pres_fps);

// Estado de UI para informe PERF (publicado por gui_task)
void perf_get_ui_state(char *out_view, size_t max_len, int *out_hud);

// Métricas de presentación y recorte de franjas F3
void perf_set_present_path(const char *path);
void perf_set_vrect(int y1, int y2);
void perf_mark_strip(uint32_t strip_us);
void perf_mark_direct_frame(uint32_t strips_count, uint32_t frame_blit_us);
void perf_mark_lvgl_clipped(uint32_t rows);

#ifdef __cplusplus
}
#endif

#endif // PERF_H
