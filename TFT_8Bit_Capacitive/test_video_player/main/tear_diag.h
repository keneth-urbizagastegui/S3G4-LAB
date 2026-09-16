#ifndef TEAR_DIAG_H
#define TEAR_DIAG_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    TEAR_DIAG_OFF    = 0, // Reproduccion normal de video
    TEAR_DIAG_MODE_A = 1, // Modo A: medio fotograma (10 franjas = 160 lineas, ~10.1 ms)
    TEAR_DIAG_MODE_B = 2, // Modo B: franja unica (1 franja = 16 lineas, ~1 ms)
    TEAR_DIAG_MODE_C = 3, // Modo C: patron color plano (rojo/azul a 30 Hz sin video)
} tear_diag_mode_t;

void tear_diag_init(void);
tear_diag_mode_t tear_diag_get_mode(void);
void tear_diag_set_mode(tear_diag_mode_t mode);
const char *tear_diag_get_mode_name(tear_diag_mode_t mode);

#ifdef __cplusplus
}
#endif

#endif // TEAR_DIAG_H
