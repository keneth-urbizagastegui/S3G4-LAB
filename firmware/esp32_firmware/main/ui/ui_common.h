#ifndef UI_COMMON_H
#define UI_COMMON_H

#include <lvgl.h>

// Definición de pantallas en el sistema
typedef enum {
    SCREEN_SPLASH = 0,
    SCREEN_HOME,
    SCREEN_OSCOPE,
    SCREEN_DMM,
    SCREEN_GEN,
    SCREEN_VIEW,
    SCREEN_PERSON,
    SCREEN_CONNECTIVITY
} eScreen;

extern eScreen current_screen;
extern lv_obj_t *active_screen_container;

// Componentes expuestos para actualización asíncrona de telemetría (desde main.cpp)
extern bool scope_ch_active[4];
extern bool scope_meas_active[4][14];
extern lv_obj_t *scope_meas_labels[4][14];
extern int scope_timebase_idx;
extern int scope_volt_div_idx[4];
extern int scope_trig_mode;
extern int scope_trig_level_mode;
extern int scope_trig_edge;
extern int scope_trig_source;
extern int scope_trig_arrow_x;
extern int scope_trig_arrow_y;

int get_y_coord_for_zero_v(int ch);

extern lv_obj_t *chart_obj;
extern lv_chart_series_t *ser_ch1;
extern lv_chart_series_t *ser_ch2;
extern lv_chart_series_t *ser_ch3;
extern lv_chart_series_t *ser_ch4;
extern lv_obj_t *lbl_dmm_val;

void format_scope_meas_value(char *buf, size_t buf_sz, int m_idx, float val);

// Variables globales de opciones estéticas configurables
extern int opt_grid_type;      // 0=Dot, 1=Line, 2=None
extern int opt_grid_intensity; // 0=Low, 1=Medium, 2=High
extern int opt_ch1_color;      // 0=Yellow, 1=Lime, 2=Cyan, 3=Pink, 4=White
extern int opt_ch2_color;      
extern int opt_ch3_color;      
extern int opt_ch4_color;      
extern int opt_dmm_mode;       // 0=Small win, 1=Full screen
extern bool opt_disp_inver;    // false=OFF, true=ON
extern int opt_theme_idx;      // 0=UTEC, 1=Ice, 2=Yellow, 3=Mint

// Estructura para definir paletas de colores del sistema
typedef struct {
    uint32_t bg_color;     // Color de fondo primario (oscuro)
    uint32_t accent_color; // Color de realce (botones activos, bordes)
    uint32_t panel_color;  // Color de paneles de control (intermedio)
    uint32_t text_color;   // Color de texto primario
} tTheme;

extern const tTheme themes[];

// Helper getters para los colores del tema actual
lv_color_t get_current_bg_color(void);
lv_color_t get_current_accent_color(void);
lv_color_t get_current_panel_color(void);
lv_color_t get_current_text_color(void);

/**
 * @brief Cambia de pantalla limpiando la memoria del contenedor anterior y llamando al constructor de la nueva.
 */
void transition_to_screen(eScreen next_screen);

#endif // UI_COMMON_H
