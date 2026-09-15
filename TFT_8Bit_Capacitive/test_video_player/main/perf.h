#ifndef PERF_H
#define PERF_H

#include <stdint.h>
#include <stdbool.h>

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
void perf_set_scenario(int track, const char *scn);
void perf_report_if_due(void);

#ifdef __cplusplus
}
#endif

#endif // PERF_H
