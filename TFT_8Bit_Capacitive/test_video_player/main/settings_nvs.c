#include "settings_nvs.h"
#include <string.h>
#include <stdio.h>
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"

static const char *TAG = "SETTINGS_NVS";
#define NVS_NAMESPACE "s3g4vid"

static nvs_handle_t s_handle = 0;
static bool s_initialized = false;

static void get_pos_key(const char *path, char *out_key, size_t max_len) {
    if (!path || !out_key || max_len < 16) return;
    const char *base = strrchr(path, '/');
    base = base ? (base + 1) : path;
    uint32_t hash = 2166136261u;
    for (const char *p = base; *p; p++) {
        hash ^= (uint8_t)*p;
        hash *= 16777619u;
    }
    snprintf(out_key, max_len, "pos_%08lx", (unsigned long)hash);
}

esp_err_t settings_nvs_init(void) {
    if (s_initialized) {
        return ESP_OK;
    }

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Fallo inicializando nvs_flash: %s", esp_err_to_name(err));
        return err;
    }

    err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &s_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Fallo abriendo espacio NVS '%s': %s", NVS_NAMESPACE, esp_err_to_name(err));
        return err;
    }

    s_initialized = true;
    ESP_LOGI(TAG, "NVS '%s' inicializado con exito", NVS_NAMESPACE);
    return ESP_OK;
}

esp_err_t settings_nvs_load(app_settings_t *out) {
    if (!out) return ESP_ERR_INVALID_ARG;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }

    // Valores por defecto segun tabla F5b §4
    out->bright = 70;
    out->osd_ms = 3000;
    out->stats = 0;
    out->miniprog = 1;
    out->repeat = 1;
    out->shuffle = 0;
    out->resume = 1;
    out->seekstep = 10;
    out->last_path[0] = '\0';

    uint8_t u8_val = 0;
    uint16_t u16_val = 0;

    if (nvs_get_u8(s_handle, "bright", &u8_val) == ESP_OK) {
        if (u8_val >= 10 && u8_val <= 100) out->bright = u8_val;
    }
    if (nvs_get_u16(s_handle, "osd_ms", &u16_val) == ESP_OK) {
        out->osd_ms = u16_val;
    }
    if (nvs_get_u8(s_handle, "stats", &u8_val) == ESP_OK) {
        out->stats = u8_val ? 1 : 0;
    }
    if (nvs_get_u8(s_handle, "miniprog", &u8_val) == ESP_OK) {
        out->miniprog = u8_val ? 1 : 0;
    }
    if (nvs_get_u8(s_handle, "repeat", &u8_val) == ESP_OK) {
        if (u8_val <= 2) out->repeat = u8_val;
    }
    if (nvs_get_u8(s_handle, "shuffle", &u8_val) == ESP_OK) {
        out->shuffle = u8_val ? 1 : 0;
    }
    if (nvs_get_u8(s_handle, "resume", &u8_val) == ESP_OK) {
        out->resume = u8_val ? 1 : 0;
    }
    if (nvs_get_u8(s_handle, "seekstep", &u8_val) == ESP_OK) {
        if (u8_val == 5 || u8_val == 10 || u8_val == 30) out->seekstep = u8_val;
    }

    size_t req_len = sizeof(out->last_path);
    if (nvs_get_str(s_handle, "last_path", out->last_path, &req_len) != ESP_OK) {
        out->last_path[0] = '\0';
    }

    ESP_LOGI(TAG, "Ajustes NVS leidos: bright=%u, osd=%u, repeat=%u, resume=%u, last='%s'",
             out->bright, out->osd_ms, out->repeat, out->resume, out->last_path);
    return ESP_OK;
}

esp_err_t settings_nvs_save(const app_settings_t *s) {
    if (!s) return ESP_ERR_INVALID_ARG;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }

    nvs_set_u8(s_handle, "bright", s->bright);
    nvs_set_u16(s_handle, "osd_ms", s->osd_ms);
    nvs_set_u8(s_handle, "stats", s->stats);
    nvs_set_u8(s_handle, "miniprog", s->miniprog);
    nvs_set_u8(s_handle, "repeat", s->repeat);
    nvs_set_u8(s_handle, "shuffle", s->shuffle);
    nvs_set_u8(s_handle, "resume", s->resume);
    nvs_set_u8(s_handle, "seekstep", s->seekstep);
    nvs_set_str(s_handle, "last_path", s->last_path);

    return nvs_commit(s_handle);
}

esp_err_t settings_nvs_get_pos(const char *path, uint32_t *out_pos_ms) {
    if (!path || !out_pos_ms) return ESP_ERR_INVALID_ARG;
    *out_pos_ms = 0;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }

    char key[16];
    get_pos_key(path, key, sizeof(key));

    uint32_t val = 0;
    esp_err_t err = nvs_get_u32(s_handle, key, &val);
    if (err == ESP_OK) {
        *out_pos_ms = val;
    }
    return err;
}

esp_err_t settings_nvs_set_pos(const char *path, uint32_t pos_ms) {
    if (!path) return ESP_ERR_INVALID_ARG;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }

    char key[16];
    get_pos_key(path, key, sizeof(key));

    esp_err_t err = nvs_set_u32(s_handle, key, pos_ms);
    if (err == ESP_OK) {
        err = nvs_commit(s_handle);
    }
    return err;
}

int settings_nvs_prune_positions(const char **valid_paths, int valid_count) {
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return 0;
    }

    int pruned = 0;
    nvs_iterator_t it = NULL;
    esp_err_t res = nvs_entry_find("nvs", NVS_NAMESPACE, NVS_TYPE_U32, &it);

    while (res == ESP_OK && it != NULL) {
        nvs_entry_info_t info;
        nvs_entry_info(it, &info);

        if (strncmp(info.key, "pos_", 4) == 0) {
            bool found = false;
            for (int i = 0; i < valid_count; i++) {
                if (!valid_paths[i]) continue;
                char exp_key[16];
                get_pos_key(valid_paths[i], exp_key, sizeof(exp_key));
                if (strcmp(info.key, exp_key) == 0) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                nvs_erase_key(s_handle, info.key);
                pruned++;
            }
        }
        res = nvs_entry_next(&it);
    }
    nvs_release_iterator(it);

    if (pruned > 0) {
        nvs_commit(s_handle);
    }
    ESP_LOGI(TAG, "Poda NVS: %d claves pos_* obsoletas borradas", pruned);
    return pruned;
}

esp_err_t settings_nvs_set_last_path(const char *path) {
    if (!path) return ESP_ERR_INVALID_ARG;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }
    char cur[128];
    size_t len = sizeof(cur);
    if (nvs_get_str(s_handle, "last_path", cur, &len) == ESP_OK) {
        if (strcmp(cur, path) == 0) {
            return ESP_OK;
        }
    }
    esp_err_t err = nvs_set_str(s_handle, "last_path", path);
    if (err == ESP_OK) {
        err = nvs_commit(s_handle);
    }
    return err;
}

esp_err_t settings_nvs_get_last_path(char *out_path, size_t max_len) {
    if (!out_path || max_len == 0) return ESP_ERR_INVALID_ARG;
    out_path[0] = '\0';
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }
    size_t req_len = max_len;
    return nvs_get_str(s_handle, "last_path", out_path, &req_len);
}

esp_err_t settings_nvs_set_u8(const char *key, uint8_t val) {
    if (!key) return ESP_ERR_INVALID_ARG;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }
    esp_err_t err = nvs_set_u8(s_handle, key, val);
    if (err == ESP_OK) {
        err = nvs_commit(s_handle);
    }
    return err;
}

esp_err_t settings_nvs_get_u8(const char *key, uint8_t *out_val) {
    if (!key || !out_val) return ESP_ERR_INVALID_ARG;
    if (!s_initialized) {
        esp_err_t err = settings_nvs_init();
        if (err != ESP_OK) return err;
    }
    return nvs_get_u8(s_handle, key, out_val);
}
