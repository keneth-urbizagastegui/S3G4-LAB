#ifndef EEZ_LVGL_UI_IMAGES_H
#define EEZ_LVGL_UI_IMAGES_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

extern const lv_img_dsc_t img_back;
extern const lv_img_dsc_t img_brightness;
extern const lv_img_dsc_t img_chevron_down;
extern const lv_img_dsc_t img_close;
extern const lv_img_dsc_t img_film;
extern const lv_img_dsc_t img_fwd10;
extern const lv_img_dsc_t img_lock;
extern const lv_img_dsc_t img_lock_big;
extern const lv_img_dsc_t img_next;
extern const lv_img_dsc_t img_pause;
extern const lv_img_dsc_t img_play;
extern const lv_img_dsc_t img_prev;
extern const lv_img_dsc_t img_queue;
extern const lv_img_dsc_t img_repeat;
extern const lv_img_dsc_t img_repeat_one;
extern const lv_img_dsc_t img_rescan;
extern const lv_img_dsc_t img_rew10;
extern const lv_img_dsc_t img_sdcard;
extern const lv_img_dsc_t img_sdcard_big;
extern const lv_img_dsc_t img_sdcard_error_big;
extern const lv_img_dsc_t img_seek_back;
extern const lv_img_dsc_t img_seek_fwd;
extern const lv_img_dsc_t img_settings;
extern const lv_img_dsc_t img_shuffle;
extern const lv_img_dsc_t img_warning;

#ifndef EXT_IMG_DESC_T
#define EXT_IMG_DESC_T
typedef struct _ext_img_desc_t {
    const char *name;
    const lv_img_dsc_t *img_dsc;
} ext_img_desc_t;
#endif

extern const ext_img_desc_t images[25];

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_IMAGES_H*/