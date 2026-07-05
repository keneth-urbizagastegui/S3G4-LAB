#ifndef UI_DMM_H
#define UI_DMM_H

#include <lvgl.h>

// Temporizador expuesto externamente para que transition_to_screen pueda destruirlo al cambiar de pantalla
extern lv_timer_t *dmm_update_timer;

/**
 * @brief Dibuja la pantalla del Multímetro Digital (DMM) emulado con su panel y spinner de autocalibración.
 */
void populate_dmm_ui(void);

#endif // UI_DMM_H
