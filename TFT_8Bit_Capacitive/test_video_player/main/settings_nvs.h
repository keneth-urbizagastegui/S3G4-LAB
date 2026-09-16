#ifndef SETTINGS_NVS_H
#define SETTINGS_NVS_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint8_t bright;      // 10-100, default 70
    uint16_t osd_ms;     // default 3000 (0 = nunca)
    uint8_t stats;       // 0/1, default 0
    uint8_t miniprog;    // 0/1, default 1
    uint8_t repeat;      // 0/1/2 (REPEAT_OFF=0, REPEAT_ALL=1, REPEAT_ONE=2), default 1
    uint8_t shuffle;     // 0/1, default 0
    uint8_t resume;      // 0/1, default 1
    uint8_t seekstep;    // 5/10/30, default 10
    char last_path[128]; // default ""
} app_settings_t;

esp_err_t settings_nvs_init(void);
esp_err_t settings_nvs_load(app_settings_t *out_settings);
esp_err_t settings_nvs_save(const app_settings_t *settings);

esp_err_t settings_nvs_get_pos(const char *path, uint32_t *out_pos_ms);
esp_err_t settings_nvs_set_pos(const char *path, uint32_t pos_ms);
int       settings_nvs_prune_positions(const char **valid_paths, int valid_count);

esp_err_t settings_nvs_set_last_path(const char *path);
esp_err_t settings_nvs_get_last_path(char *out_path, size_t max_len);

esp_err_t settings_nvs_set_u8(const char *key, uint8_t val);
esp_err_t settings_nvs_get_u8(const char *key, uint8_t *out_val);

#ifdef __cplusplus
}
#endif

#endif // SETTINGS_NVS_H
