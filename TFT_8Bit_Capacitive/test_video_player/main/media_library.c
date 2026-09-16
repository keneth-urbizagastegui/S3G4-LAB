#include "media_library.h"
#include "settings_nvs.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <dirent.h>
#include <unistd.h>
#include <sys/stat.h>
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "esp_jpeg_dec.h"
#include "cJSON.h"
#include "lvgl.h"
#include "sdkconfig.h"

static const char *TAG = "MEDIA_LIB";

#ifndef CONFIG_APP_THUMB_CACHE_MAX
#define CONFIG_APP_THUMB_CACHE_MAX 24
#endif

static media_item_t *s_items = NULL;
static int s_item_count = 0;
static int s_compatible_count = 0;
static media_scan_progress_cb_t s_progress_cb = NULL;

static bool is_avi_filename(const char *name) {
    if (!name) return false;
    size_t len = strlen(name);
    if (len < 4) return false;
    return (strcasecmp(name + len - 4, ".avi") == 0);
}

void media_library_set_progress_cb(media_scan_progress_cb_t cb) {
    s_progress_cb = cb;
}

int media_library_count(void) {
    return s_item_count;
}

int media_library_compatible_count(void) {
    return s_compatible_count;
}

const media_item_t *media_library_get(int index) {
    if (index >= 0 && index < s_item_count) {
        return &s_items[index];
    }
    return NULL;
}

int media_library_index_of(const char *path) {
    if (!path) return -1;
    for (int i = 0; i < s_item_count; i++) {
        if (strcmp(s_items[i].path, path) == 0) {
            return i;
        }
    }
    return -1;
}

static void free_library_items(void) {
    if (s_items) {
        for (int i = 0; i < s_item_count; i++) {
            if (s_items[i].thumb_dsc) {
                lv_image_dsc_t *dsc = (lv_image_dsc_t *)s_items[i].thumb_dsc;
                if (dsc->data) {
                    heap_caps_free((void *)dsc->data);
                }
                heap_caps_free(dsc);
                s_items[i].thumb_dsc = NULL;
            }
        }
        free(s_items);
        s_items = NULL;
    }
    s_item_count = 0;
    s_compatible_count = 0;
}

static void parse_json_metadata(const char *json_path, char *out_title, size_t title_len, char *out_sub, size_t sub_len, bool *out_has_json) {
    *out_has_json = false;
    struct stat st;
    if (stat(json_path, &st) != 0) {
        ESP_LOGI(TAG, "Sin fichero JSON %s, usando nombre base", json_path);
        return;
    }

    if (st.st_size > 2048) {
        ESP_LOGW(TAG, "JSON %s excede 2 KB (%ld B), se ignora con aviso", json_path, (long)st.st_size);
        return;
    }

    FILE *fj = fopen(json_path, "r");
    if (!fj) {
        ESP_LOGW(TAG, "No se pudo abrir JSON %s", json_path);
        return;
    }

    char *buf = (char *)malloc(st.st_size + 1);
    if (!buf) {
        fclose(fj);
        return;
    }

    size_t nr = fread(buf, 1, st.st_size, fj);
    buf[nr] = '\0';
    fclose(fj);

    cJSON *root = cJSON_Parse(buf);
    free(buf);

    if (!root) {
        ESP_LOGW(TAG, "JSON mal formado en %s", json_path);
        return;
    }

    cJSON *j_title = cJSON_GetObjectItem(root, "title");
    if (j_title && cJSON_IsString(j_title) && (j_title->valuestring != NULL)) {
        snprintf(out_title, title_len, "%s", j_title->valuestring);
    }

    cJSON *j_sub = cJSON_GetObjectItem(root, "subtitle");
    if (j_sub && cJSON_IsString(j_sub) && (j_sub->valuestring != NULL)) {
        snprintf(out_sub, sub_len, "%s", j_sub->valuestring);
    }

    cJSON_Delete(root);
    *out_has_json = true;
}

static void load_jpeg_thumbnail(const char *jpg_path, media_item_t *item, int *thumb_cache_count) {
    struct stat st;
    if (stat(jpg_path, &st) != 0) {
        item->has_thumb = false;
        item->thumb_dsc = NULL;
        return;
    }

    item->has_thumb = true;

    if (*thumb_cache_count >= CONFIG_APP_THUMB_CACHE_MAX) {
        ESP_LOGI(TAG, "Tope de miniaturas alcanzado (%d), usando marcador para %s", CONFIG_APP_THUMB_CACHE_MAX, jpg_path);
        item->thumb_dsc = NULL;
        return;
    }

    FILE *f = fopen(jpg_path, "rb");
    if (!f) {
        item->thumb_dsc = NULL;
        return;
    }

    size_t fsz = (size_t)st.st_size;
    uint8_t *jpg_buf = (uint8_t *)malloc(fsz);
    if (!jpg_buf) {
        fclose(f);
        item->thumb_dsc = NULL;
        return;
    }

    size_t r = fread(jpg_buf, 1, fsz, f);
    fclose(f);
    if (r < fsz) {
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    jpeg_dec_config_t cfg = DEFAULT_JPEG_DEC_CONFIG();
    cfg.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;
    cfg.block_enable = false;

    jpeg_dec_handle_t dec = NULL;
    if (jpeg_dec_open(&cfg, &dec) != JPEG_ERR_OK) {
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    jpeg_dec_io_t io = {
        .inbuf = jpg_buf,
        .inbuf_len = (int)fsz,
        .outbuf = NULL,
    };

    jpeg_dec_header_info_t hdr_info;
    if (jpeg_dec_parse_header(dec, &io, &hdr_info) != JPEG_ERR_OK) {
        ESP_LOGW(TAG, "Fallo parseando cabecera JPEG miniatura %s", jpg_path);
        jpeg_dec_close(dec);
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    if (hdr_info.width != 144 || hdr_info.height != 81) {
        ESP_LOGW(TAG, "Miniatura %s tiene dimensiones %ux%u != 144x81, usando marcador",
                 jpg_path, hdr_info.width, hdr_info.height);
        jpeg_dec_close(dec);
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    int outlen = 0;
    jpeg_dec_get_outbuf_len(dec, &outlen);
    if (outlen <= 0) {
        jpeg_dec_close(dec);
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    uint8_t *rgb_psram = (uint8_t *)heap_caps_aligned_alloc(16, outlen, MALLOC_CAP_SPIRAM);
    if (!rgb_psram) {
        ESP_LOGE(TAG, "Fallo reservando %d B en PSRAM para miniatura %s", outlen, jpg_path);
        jpeg_dec_close(dec);
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    io.outbuf = rgb_psram;
    if (jpeg_dec_process(dec, &io) != JPEG_ERR_OK) {
        ESP_LOGE(TAG, "Fallo decodificando miniatura %s", jpg_path);
        heap_caps_free(rgb_psram);
        jpeg_dec_close(dec);
        free(jpg_buf);
        item->thumb_dsc = NULL;
        return;
    }

    jpeg_dec_close(dec);
    free(jpg_buf);

    lv_image_dsc_t *dsc = (lv_image_dsc_t *)heap_caps_malloc(sizeof(lv_image_dsc_t), MALLOC_CAP_SPIRAM);
    if (!dsc) {
        heap_caps_free(rgb_psram);
        item->thumb_dsc = NULL;
        return;
    }

    dsc->header.cf = LV_COLOR_FORMAT_RGB565;
    dsc->header.w = 144;
    dsc->header.h = 81;
    dsc->header.flags = 0;
    dsc->header.magic = LV_IMAGE_HEADER_MAGIC;
    dsc->data_size = outlen;
    dsc->data = rgb_psram;
    dsc->reserved = NULL;

    item->thumb_dsc = dsc;
    (*thumb_cache_count)++;
}

esp_err_t media_library_scan(void) {
    int64_t t_scan_start_us = esp_timer_get_time();
    ESP_LOGI(TAG, "Iniciando escaneo dinamico de biblioteca multimedia...");

    free_library_items();

    // 1. Elegir directorio: /sdcard/videos si existe y tiene archivos, o /sdcard
    char base_dir[64] = "/sdcard";
    DIR *d_test = opendir("/sdcard/videos");
    if (d_test) {
        struct dirent *de;
        bool has_avi = false;
        while ((de = readdir(d_test)) != NULL) {
            if (de->d_name[0] != '.' && is_avi_filename(de->d_name)) {
                has_avi = true;
                break;
            }
        }
        closedir(d_test);
        if (has_avi) {
            snprintf(base_dir, sizeof(base_dir), "/sdcard/videos");
        }
    }

    DIR *dir = opendir(base_dir);
    if (!dir) {
        ESP_LOGE(TAG, "No se pudo abrir directorio %s", base_dir);
        uint32_t scan_ms = (uint32_t)((esp_timer_get_time() - t_scan_start_us) / 1000);
        printf("LIB,count=0,compatible=0,incompatible=0,with_json=0,with_thumb=0,scan_ms=%u\n", (unsigned int)scan_ms);
        fflush(stdout);
        if (s_progress_cb) s_progress_cb(0, 0);
        return ESP_OK;
    }

    char **avi_files = NULL;
    int avi_count = 0;
    int avi_cap = 0;

    struct dirent *de;
    while ((de = readdir(dir)) != NULL) {
        if (de->d_name[0] == '.') continue;
        if (is_avi_filename(de->d_name)) {
            if (avi_count >= avi_cap) {
                avi_cap = (avi_cap == 0) ? 8 : avi_cap * 2;
                avi_files = (char **)realloc(avi_files, avi_cap * sizeof(char *));
            }
            avi_files[avi_count++] = strdup(de->d_name);
        }
    }
    closedir(dir);

    if (avi_count == 0) {
        if (avi_files) free(avi_files);
        uint32_t scan_ms = (uint32_t)((esp_timer_get_time() - t_scan_start_us) / 1000);
        printf("LIB,count=0,compatible=0,incompatible=0,with_json=0,with_thumb=0,scan_ms=%u\n", (unsigned int)scan_ms);
        fflush(stdout);
        if (s_progress_cb) s_progress_cb(0, 0);
        return ESP_OK;
    }

    // Orden alfabetico estable por nombre de fichero
    for (int i = 0; i < avi_count - 1; i++) {
        for (int j = i + 1; j < avi_count; j++) {
            if (strcmp(avi_files[i], avi_files[j]) > 0) {
                char *tmp = avi_files[i];
                avi_files[i] = avi_files[j];
                avi_files[j] = tmp;
            }
        }
    }

    s_items = (media_item_t *)calloc(avi_count, sizeof(media_item_t));
    if (!s_items) {
        ESP_LOGE(TAG, "Fallo reservando memoria para %d items", avi_count);
        for (int i = 0; i < avi_count; i++) free(avi_files[i]);
        free(avi_files);
        return ESP_ERR_NO_MEM;
    }
    s_item_count = avi_count;

    int with_json = 0;
    int with_thumb = 0;
    int thumb_cache_count = 0;

    const char **valid_paths = (const char **)malloc(avi_count * sizeof(char *));

    for (int idx = 0; idx < avi_count; idx++) {
        if (s_progress_cb) {
            s_progress_cb(idx, avi_count);
        }

        media_item_t *it = &s_items[idx];
        snprintf(it->path, sizeof(it->path), "%s/%s", base_dir, avi_files[idx]);
        valid_paths[idx] = it->path;

        // Nombre sin extension por defecto
        char stem[64];
        snprintf(stem, sizeof(stem), "%s", avi_files[idx]);
        char *dot = strrchr(stem, '.');
        if (dot) *dot = '\0';

        snprintf(it->title, sizeof(it->title), "%s", stem);
        it->subtitle[0] = '\0';
        it->compatible = true;
        it->incompat[0] = '\0';
        it->rotated = false;
        it->has_thumb = false;
        it->thumb_dsc = NULL;
        it->resume_ms = 0;

        // --- 1. Inspeccionar cabecera AVI y reglas de compatibilidad ---
        FILE *f = fopen(it->path, "rb");
        if (!f) {
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "No se pudo abrir");
            printf("MEDIA,file=%s,size=0,w=0,h=0,us_per_frame=0,fps_milli=0,frames=0,idx1=0,chunk_avg=0,chunk_max=0,subsampling=unknown,compat=0,reason=%s\n",
                   it->path, it->incompat);
            fflush(stdout);
            continue;
        }

        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        fseek(f, 0, SEEK_SET);

        if (file_size < 128) {
            fclose(f);
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "Archivo truncado");
            printf("MEDIA,file=%s,size=%ld,w=0,h=0,us_per_frame=0,fps_milli=0,frames=0,idx1=0,chunk_avg=0,chunk_max=0,subsampling=unknown,compat=0,reason=%s\n",
                   it->path, file_size, it->incompat);
            fflush(stdout);
            continue;
        }

        size_t hdr_cap = 16384;
        uint8_t *hdr = (uint8_t *)malloc(hdr_cap);
        if (!hdr) {
            fclose(f);
            continue;
        }

        size_t r = fread(hdr, 1, hdr_cap, f);
        if (r < 128 || memcmp(hdr, "RIFF", 4) != 0 || memcmp(hdr + 8, "AVI ", 4) != 0) {
            free(hdr);
            fclose(f);
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "Archivo no valido");
            printf("MEDIA,file=%s,size=%ld,w=0,h=0,us_per_frame=0,fps_milli=0,frames=0,idx1=0,chunk_avg=0,chunk_max=0,subsampling=unknown,compat=0,reason=%s\n",
                   it->path, file_size, it->incompat);
            fflush(stdout);
            continue;
        }

        uint32_t riff_len = *(uint32_t *)(hdr + 4);
        if (file_size < (long)(riff_len + 8)) {
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "Archivo truncado");
        }

        // Buscar bloque avih
        int avih_pos = -1;
        for (size_t i = 0; i + 48 <= r; i++) {
            if (memcmp(hdr + i, "avih", 4) == 0) {
                avih_pos = (int)i;
                break;
            }
        }

        uint32_t us_per_frame = 33333;
        uint32_t frames = 0;
        uint32_t w = 0;
        uint32_t h = 0;

        if (avih_pos >= 0) {
            uint8_t *p = hdr + avih_pos + 8;
            us_per_frame = *(uint32_t *)(p);
            frames = *(uint32_t *)(p + 16);
            w = *(uint32_t *)(p + 32);
            h = *(uint32_t *)(p + 36);
        } else {
            if (it->compatible) {
                it->compatible = false;
                snprintf(it->incompat, sizeof(it->incompat), "Sin cabecera avih");
            }
        }

        it->w = (uint16_t)w;
        it->h = (uint16_t)h;
        it->frames = frames;
        it->fps_milli = (us_per_frame > 0) ? (uint32_t)(1000000000ULL / (uint64_t)us_per_frame) : 0;
        it->dur_ms = ((uint64_t)frames * (uint64_t)us_per_frame) / 1000ULL;

        // Buscar LIST movi
        long movi_pos = -1;
        long movi_chunk_start = -1;
        uint32_t movi_len = 0;
        for (size_t i = 0; i + 12 <= r; i++) {
            if (memcmp(hdr + i, "LIST", 4) == 0 && memcmp(hdr + i + 8, "movi", 4) == 0) {
                movi_chunk_start = (long)i;
                movi_len = *(uint32_t *)(hdr + i + 4);
                movi_pos = (long)i + 12;
                break;
            }
        }

        if (movi_pos < 0) {
            movi_pos = 2048;
        }

        if (movi_chunk_start >= 0 && (long)(movi_chunk_start + 8 + movi_len) > file_size) {
            if (it->compatible) {
                it->compatible = false;
                snprintf(it->incompat, sizeof(it->incompat), "Archivo truncado");
            }
        }

        // Buscar fourcc en strh / strf
        char fourcc[5] = "    ";
        for (size_t i = 0; i + 16 <= r; i++) {
            if (memcmp(hdr + i, "strh", 4) == 0 && memcmp(hdr + i + 8, "vids", 4) == 0) {
                memcpy(fourcc, hdr + i + 12, 4);
                fourcc[4] = '\0';
                break;
            }
        }

        // Buscar primer chunk de video para subsampling y verificacion JPEG
        const char *subsampling = "unknown";
        bool is_first_chunk_jpeg = false;

        fseek(f, movi_pos, SEEK_SET);
        uint8_t chunk_search_buf[4096];
        long vchunk_data_pos = -1;
        uint32_t vchunk_data_len = 0;
        long cur_pos = movi_pos;

        while (cur_pos < file_size && cur_pos < movi_pos + 256 * 1024) {
            fseek(f, cur_pos, SEEK_SET);
            size_t nr = fread(chunk_search_buf, 1, sizeof(chunk_search_buf), f);
            if (nr < 8) break;
            bool found = false;
            for (size_t i = 0; i + 8 <= nr; i++) {
                if (memcmp(chunk_search_buf + i, "00dc", 4) == 0 || memcmp(chunk_search_buf + i, "00db", 4) == 0) {
                    vchunk_data_len = *(uint32_t *)(chunk_search_buf + i + 4);
                    vchunk_data_pos = cur_pos + (long)i + 8;
                    found = true;
                    break;
                }
            }
            if (found) break;
            if (nr <= 8) break;
            cur_pos += (long)(nr - 8);
        }

        if (vchunk_data_pos > 0 && vchunk_data_len > 0 && vchunk_data_pos + 4 <= file_size) {
            fseek(f, vchunk_data_pos, SEEK_SET);
            size_t read_len = (vchunk_data_len > 4096) ? 4096 : vchunk_data_len;
            uint8_t *jbuf = (uint8_t *)malloc(read_len);
            if (jbuf) {
                size_t jread = fread(jbuf, 1, read_len, f);
                if (jread >= 4 && jbuf[0] == 0xFF && jbuf[1] == 0xD8) {
                    is_first_chunk_jpeg = true;
                    size_t p = 2;
                    while (p + 4 < jread) {
                        if (jbuf[p] != 0xFF) { p++; continue; }
                        while (p < jread && jbuf[p] == 0xFF) p++;
                        if (p >= jread) break;
                        uint8_t marker = jbuf[p++];
                        if (marker == 0xD9 || marker == 0xDA) break;
                        if (p + 2 > jread) break;
                        uint16_t seg_len = ((uint16_t)jbuf[p] << 8) | jbuf[p + 1];
                        if (marker == 0xC0 || marker == 0xC2) {
                            if (p + 8 <= jread) {
                                uint8_t num_components = jbuf[p + 7];
                                if (num_components >= 1 && p + 10 <= jread) {
                                    uint8_t sample_byte = jbuf[p + 9];
                                    uint8_t h_sample = (sample_byte >> 4) & 0x0F;
                                    uint8_t v_sample = sample_byte & 0x0F;
                                    if (h_sample == 2 && v_sample == 2) subsampling = "420";
                                    else if (h_sample == 2 && v_sample == 1) subsampling = "422";
                                    else if (h_sample == 1 && v_sample == 1) subsampling = "444";
                                    else if (h_sample == 4 && v_sample == 1) subsampling = "411";
                                }
                            }
                            break;
                        }
                        p += seg_len;
                    }
                }
                free(jbuf);
            }
        }

        // Recorrer idx1
        int has_idx1 = 0;
        uint32_t chunk_avg = 0;
        uint32_t chunk_max = 0;

        if (file_size > 1024) {
            long idx1_file_pos = -1;
            uint32_t idx_size = 0;

            if (movi_chunk_start >= 0 && movi_len > 0) {
                long cand = movi_chunk_start + 8 + movi_len + (movi_len & 1);
                if (cand + 8 <= file_size) {
                    fseek(f, cand, SEEK_SET);
                    uint8_t chk[8];
                    if (fread(chk, 1, 8, f) == 8 && memcmp(chk, "idx1", 4) == 0) {
                        idx1_file_pos = cand;
                        idx_size = *(uint32_t *)(chk + 4);
                        has_idx1 = 1;
                    }
                }
            }

            if (!has_idx1) {
                long scan_bytes = (file_size > 64 * 1024) ? 64 * 1024 : file_size;
                fseek(f, file_size - scan_bytes, SEEK_SET);
                uint8_t *tail = (uint8_t *)malloc(scan_bytes);
                if (tail) {
                    size_t tr = fread(tail, 1, scan_bytes, f);
                    for (long i = 0; i + 8 <= (long)tr; i++) {
                        if (memcmp(tail + i, "idx1", 4) == 0) {
                            idx1_file_pos = (file_size - scan_bytes) + i;
                            idx_size = *(uint32_t *)(tail + i + 4);
                            has_idx1 = 1;
                            break;
                        }
                    }
                    free(tail);
                }
            }

            if (has_idx1 && idx_size > 0 && idx1_file_pos >= 0) {
                fseek(f, idx1_file_pos + 8, SEEK_SET);
                uint32_t bytes_left = idx_size;
                uint64_t total_chunk_bytes = 0;
                uint32_t count_chunks = 0;
                uint8_t ent_buf[2048];
                while (bytes_left >= 16) {
                    size_t to_read = (bytes_left > sizeof(ent_buf)) ? sizeof(ent_buf) : bytes_left;
                    to_read = (to_read / 16) * 16;
                    size_t nr = fread(ent_buf, 1, to_read, f);
                    if (nr < 16) break;
                    for (size_t k = 0; k + 16 <= nr; k += 16) {
                        if (memcmp(ent_buf + k, "00dc", 4) == 0 || memcmp(ent_buf + k, "00db", 4) == 0) {
                            uint32_t clen = *(uint32_t *)(ent_buf + k + 12);
                            total_chunk_bytes += clen;
                            count_chunks++;
                            if (clen > chunk_max) {
                                chunk_max = clen;
                            }
                        }
                    }
                    bytes_left -= (uint32_t)nr;
                }
                if (count_chunks > 0) {
                    chunk_avg = (uint32_t)(total_chunk_bytes / count_chunks);
                }
            }
        }

        it->chunk_max = chunk_max;
        free(hdr);
        fclose(f);

        // --- VALIDACION DE REGLAS F5b §7.1 ---
        // Regla 1: MJPEG
        bool is_mjpeg = (strcasecmp(fourcc, "MJPG") == 0 ||
                         strcasecmp(fourcc, "JPEG") == 0 ||
                         strcasecmp(fourcc, "DMB1") == 0 ||
                         is_first_chunk_jpeg);
        if (!is_mjpeg && it->compatible) {
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "No es MJPEG");
        }

        // Regla 2: 320x480 (girado) o 480x320 (clasico)
        if (it->w == 320 && it->h == 480) {
            it->rotated = true;
        } else if (it->w == 480 && it->h == 320) {
            it->rotated = false;
        } else {
            if (it->compatible) {
                it->compatible = false;
                snprintf(it->incompat, sizeof(it->incompat), "Resolucion %ux%u", it->w, it->h);
            }
        }

        // Regla 3: Submuestreo 4:2:0
        if (strcmp(subsampling, "420") != 0 && it->compatible) {
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "Color 4:2:2 o 4:4:4");
        }

        // Regla 4: fps entre 24 y 31
        uint32_t fps = (it->fps_milli + 500) / 1000;
        if ((fps < 24 || fps > 31) && it->compatible) {
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "%u fps", (unsigned int)fps);
        }

        // Regla 5: chunk max <= 128 KB
        if (chunk_max > (128 * 1024) && it->compatible) {
            it->compatible = false;
            snprintf(it->incompat, sizeof(it->incompat), "Fotogramas de %u KB", (unsigned int)(chunk_max / 1024));
        }

        // Regla 6: idx1 presente (aviso, no bloqueo a menos que el archivo este corrupto)
        // Ya considerado en "Archivo truncado" si correspondia.

        const char *reason_str = it->compatible ? "ok" : it->incompat;

        printf("MEDIA,file=%s,size=%ld,w=%u,h=%u,us_per_frame=%u,fps_milli=%llu,frames=%u,idx1=%d,chunk_avg=%u,chunk_max=%u,subsampling=%s,compat=%d,reason=%s\n",
               it->path, file_size, (unsigned int)w, (unsigned int)h,
               (unsigned int)us_per_frame, (unsigned long long)it->fps_milli,
               (unsigned int)frames, has_idx1,
               (unsigned int)chunk_avg, (unsigned int)chunk_max,
               subsampling, it->compatible ? 1 : 0, reason_str);
        fflush(stdout);

        // --- 2. Metadatos JSON ---
        char json_path[140];
        snprintf(json_path, sizeof(json_path), "%s/%s.json", base_dir, stem);
        bool has_json = false;
        parse_json_metadata(json_path, it->title, sizeof(it->title), it->subtitle, sizeof(it->subtitle), &has_json);
        if (has_json) with_json++;

        // --- 3. Miniaturas JPG ---
        char jpg_path[140];
        snprintf(jpg_path, sizeof(jpg_path), "%s/%s.jpg", base_dir, stem);
        load_jpeg_thumbnail(jpg_path, it, &thumb_cache_count);
        if (it->has_thumb) with_thumb++;

        // --- 4. Posicion de reanudacion en NVS ---
        uint32_t saved_pos = 0;
        if (settings_nvs_get_pos(it->path, &saved_pos) == ESP_OK) {
            if (saved_pos >= 5000 && (it->dur_ms > 10000 && saved_pos <= it->dur_ms - 10000)) {
                it->resume_ms = saved_pos;
            } else {
                it->resume_ms = 0;
            }
        }

        if (it->compatible) {
            s_compatible_count++;
        }
    }

    // Poda de claves NVS de videos que ya no estan
    settings_nvs_prune_positions(valid_paths, avi_count);
    free(valid_paths);

    for (int i = 0; i < avi_count; i++) {
        free(avi_files[i]);
    }
    free(avi_files);

    if (s_progress_cb) {
        s_progress_cb(avi_count, avi_count);
    }

    uint32_t total_scan_ms = (uint32_t)((esp_timer_get_time() - t_scan_start_us) / 1000);

    // Linea LIB requerida por F5b
    printf("LIB,count=%d,compatible=%d,incompatible=%d,with_json=%d,with_thumb=%d,scan_ms=%u\n",
           avi_count, s_compatible_count, avi_count - s_compatible_count, with_json, with_thumb, (unsigned int)total_scan_ms);
    fflush(stdout);

    ESP_LOGI(TAG, "Escaneo completado en %u ms: %d videos (%d compatibles, %d incompatibles, %d json, %d thumb)",
             (unsigned int)total_scan_ms, avi_count, s_compatible_count, avi_count - s_compatible_count, with_json, with_thumb);

    return ESP_OK;
}
