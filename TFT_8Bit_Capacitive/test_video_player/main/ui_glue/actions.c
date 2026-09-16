#include "ui/actions.h"
#include "ui/screens.h"
#include "ui/images.h"
#include "ui/ui.h"
#include "ui_glue.h"
#include "player.h"
#include "settings_nvs.h"
#include "media_library.h"
#include "lcd_bus.h"
#include "esp_timer.h"
#include "esp_log.h"
#include <stdio.h>
#include <string.h>

static const char *TAG = "UI_ACTIONS";

static bool s_osd_visible = true;
static int s_hud_forced_mode = 0; // 0=auto, 1=forced hidden, 2=forced visible
static int64_t s_last_touch_time = 0;
static bool s_seeking = false;
static int s_current_track_idx = 0;
static view_mode_t s_view_mode = VIEW_MODE_FULLSCREEN;
static app_settings_t s_settings;

void ui_glue_init(void) {
    settings_nvs_load(&s_settings);
    s_last_touch_time = esp_timer_get_time() / 1000;
    s_osd_visible = true;
    s_hud_forced_mode = 0;
    s_view_mode = VIEW_MODE_FULLSCREEN;
}

bool ui_glue_is_osd_visible(void) {
    return s_osd_visible;
}

void ui_glue_set_osd_visible(bool visible) {
    s_osd_visible = visible;
    if (visible) {
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 40, 480, 196}};
        player_cmd_send(&cmd);
        lcd_bus_set_video_rect(0, 40, 480, 196);
        if (objects.osd_top) lv_obj_remove_flag(objects.osd_top, LV_OBJ_FLAG_HIDDEN);
        if (objects.osd_bottom) lv_obj_remove_flag(objects.osd_bottom, LV_OBJ_FLAG_HIDDEN);
        if (objects.bar_mini_progress) lv_obj_add_flag(objects.bar_mini_progress, LV_OBJ_FLAG_HIDDEN);
    } else {
        if (objects.osd_top) lv_obj_add_flag(objects.osd_top, LV_OBJ_FLAG_HIDDEN);
        if (objects.osd_bottom) lv_obj_add_flag(objects.osd_bottom, LV_OBJ_FLAG_HIDDEN);
        if (objects.bar_mini_progress) lv_obj_remove_flag(objects.bar_mini_progress, LV_OBJ_FLAG_HIDDEN);
        player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
        player_cmd_send(&cmd);
        lcd_bus_set_video_rect(0, 0, 480, 320);
    }
}

void ui_glue_set_hud_forced(int mode) {
    s_hud_forced_mode = mode;
    if (mode == 1) {
        ui_glue_set_osd_visible(false);
    } else if (mode == 2) {
        ui_glue_set_osd_visible(true);
    }
}

int ui_glue_get_hud_forced(void) {
    return s_hud_forced_mode;
}

void ui_glue_set_view_mode(view_mode_t mode) {
    s_view_mode = mode;
    if (mode == VIEW_MODE_FULLSCREEN) {
        loadScreen(SCREEN_ID_SCR_PLAYER);
        if (s_osd_visible) {
            lcd_bus_set_video_rect(0, 40, 480, 196);
        } else {
            lcd_bus_set_video_rect(0, 0, 480, 320);
        }
    } else {
        loadScreen(SCREEN_ID_SCR_LIBRARY);
        lcd_bus_set_video_rect(0, 0, 0, 0);
    }
}

view_mode_t ui_glue_get_view_mode(void) {
    return s_view_mode;
}

void ui_glue_get_published_info(char *title_buf, size_t max_len, int *track_idx, view_mode_t *vmode, int *hud_vis) {
    if (vmode) *vmode = s_view_mode;
    if (track_idx) *track_idx = s_current_track_idx;
    if (hud_vis) *hud_vis = s_osd_visible ? 1 : 0;
    if (title_buf && max_len > 0) {
        const char *txt = (objects.lbl_title) ? lv_label_get_text(objects.lbl_title) : "";
        snprintf(title_buf, max_len, "%s", txt ? txt : "");
    }
}

void ui_glue_tick(void) {
    player_status_t st;
    player_get_status(&st);
    s_current_track_idx = st.track_index;

    // Update play icon
    if (objects.lbl_play_icon) {
        const char *sym = (st.state == PST_PLAYING) ? "\uF04C" : "\uF04B";
        lv_label_set_text(objects.lbl_play_icon, sym);
    }

    // Auto-hide OSD
    if (s_hud_forced_mode == 0 && s_osd_visible && st.state == PST_PLAYING && !s_seeking) {
        int64_t now = esp_timer_get_time() / 1000;
        uint32_t timeout = s_settings.osd_ms ? s_settings.osd_ms : 3000;
        if (now - s_last_touch_time >= timeout) {
            ui_glue_set_osd_visible(false);
        }
    }
}

// ----------------- EEZ Studio Action Handlers -----------------

void action_toggle_play(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    player_cmd_t cmd = {.type = PCMD_TOGGLE};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: toggle_play");
}

void action_prev(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    player_cmd_t cmd = {.type = PCMD_PREV};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: prev");
}

void action_next(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    player_cmd_t cmd = {.type = PCMD_NEXT};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: next");
}

void action_rew10(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    player_status_t st;
    player_get_status(&st);
    int32_t step = s_settings.seekstep ? (s_settings.seekstep * 1000) : 10000;
    int32_t target = (st.pos_ms > (uint64_t)step) ? (int32_t)(st.pos_ms - step) : 0;
    player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = target};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: rew10 -> target %ld ms", (long)target);
}

void action_fwd10(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    player_status_t st;
    player_get_status(&st);
    int32_t step = s_settings.seekstep ? (s_settings.seekstep * 1000) : 10000;
    int32_t target = (int32_t)(st.pos_ms + step);
    if (st.dur_ms > 0 && (uint64_t)target > st.dur_ms) target = (int32_t)st.dur_ms;
    player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = target};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: fwd10 -> target %ld ms", (long)target);
}

void action_seek_begin(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    s_seeking = true;
}

void action_seek_preview(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (objects.sld_seek) {
        int32_t val = lv_slider_get_value(objects.sld_seek);
        player_status_t st;
        player_get_status(&st);
        if (st.dur_ms > 0 && objects.lbl_pos) {
            uint32_t preview_sec = (uint32_t)(((uint64_t)val * st.dur_ms) / (1000 * 1000));
            char buf[16];
            snprintf(buf, sizeof(buf), "%lu:%02lu", (unsigned long)(preview_sec / 60), (unsigned long)(preview_sec % 60));
            lv_label_set_text(objects.lbl_pos, buf);
        }
    }
}

void action_seek_commit(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (objects.sld_seek) {
        int32_t val = lv_slider_get_value(objects.sld_seek);
        player_status_t st;
        player_get_status(&st);
        if (st.dur_ms > 0) {
            int32_t target = (int32_t)(((uint64_t)val * st.dur_ms) / 1000);
            player_cmd_t cmd = {.type = PCMD_SEEK_MS, .arg = target};
            player_cmd_send(&cmd);
            ESP_LOGI(TAG, "Action: seek_commit -> %ld ms", (long)target);
        }
    }
    s_seeking = false;
}

void action_cycle_repeat(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    s_settings.repeat = (s_settings.repeat + 1) % 3;
    settings_nvs_save(&s_settings);
    player_cmd_t cmd = {.type = PCMD_SET_REPEAT, .arg = s_settings.repeat};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: cycle_repeat -> %d", s_settings.repeat);
}

void action_toggle_shuffle(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    s_settings.shuffle = !s_settings.shuffle;
    settings_nvs_save(&s_settings);
    player_cmd_t cmd = {.type = PCMD_SET_SHUFFLE, .arg = s_settings.shuffle};
    player_cmd_send(&cmd);
    ESP_LOGI(TAG, "Action: toggle_shuffle -> %d", s_settings.shuffle);
}

void action_lock(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: lock");
}

void action_toggle_osd(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    if (s_hud_forced_mode != 0) return;
    ui_glue_set_osd_visible(!s_osd_visible);
    ESP_LOGI(TAG, "Action: toggle_osd -> visible=%d", s_osd_visible);
}

void action_open_library(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    s_view_mode = VIEW_MODE_STUDIO;
    lcd_bus_set_video_rect(0, 0, 0, 0);
    player_cmd_t cmd = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 0, 0}};
    player_cmd_send(&cmd);
    action_library_populate(NULL);
    loadScreen(SCREEN_ID_SCR_LIBRARY);
    ESP_LOGI(TAG, "Action: open_library");
}

void action_open_queue(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: open_queue");
}

void action_close_queue(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: close_queue");
}

void action_open_settings(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: open_settings");
}

void action_settings_tab(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_open_stats(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_play_index(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    lv_obj_t *target = lv_event_get_current_target(e);
    int idx = (int)(uintptr_t)lv_obj_get_user_data(target);
    const media_item_t *item = media_library_get(idx);
    if (!item) return;

    if (!item->compatible) {
        ESP_LOGW(TAG, "Video incompatible: %s (%s)", item->path, item->incompat);
        return;
    }

    ESP_LOGI(TAG, "Action: play_index -> %d (%s)", idx, item->path);
    player_cmd_t cmd_open = {.type = PCMD_OPEN, .arg = idx};
    player_cmd_send(&cmd_open);

    // 2s rewind on resume
    if (item->resume_ms > 2000) {
        uint32_t resume_pos = item->resume_ms - 2000;
        player_cmd_t cmd_seek = {.type = PCMD_SEEK_MS, .arg = (int32_t)resume_pos};
        player_cmd_send(&cmd_seek);
        ESP_LOGI(TAG, "Resuming with 2s rewind: target %lu ms (saved %lu ms)",
                 (unsigned long)resume_pos, (unsigned long)item->resume_ms);
    }

    s_view_mode = VIEW_MODE_FULLSCREEN;
    loadScreen(SCREEN_ID_SCR_PLAYER);
    if (s_osd_visible) {
        player_cmd_t cmd_rect = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 40, 480, 196}};
        player_cmd_send(&cmd_rect);
        lcd_bus_set_video_rect(0, 40, 480, 196);
    } else {
        player_cmd_t cmd_rect = {.type = PCMD_SET_VIDEO_RECT, .rect = {0, 0, 480, 320}};
        player_cmd_send(&cmd_rect);
        lcd_bus_set_video_rect(0, 0, 480, 320);
    }
}

void action_rescan(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
    ESP_LOGI(TAG, "Action: rescan library...");
    esp_err_t err = media_library_scan();
    if (err == ESP_OK && media_library_count() > 0) {
        action_library_populate(NULL);
        loadScreen(SCREEN_ID_SCR_LIBRARY);
    } else {
        loadScreen(SCREEN_ID_SCR_NO_MEDIA);
        if (objects.chip_err) {
            if (err != ESP_OK) {
                lv_obj_remove_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
                lv_obj_t *lbl = lv_obj_get_child(objects.chip_err, 0);
                if (lbl) {
                    char ebuf[32];
                    snprintf(ebuf, sizeof(ebuf), "Error: 0x%x", err);
                    lv_label_set_text(lbl, ebuf);
                }
            } else {
                lv_obj_add_flag(objects.chip_err, LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
}

void action_library_populate(lv_event_t *e) {
    if (!objects.lib_grid) return;
    lv_obj_clean(objects.lib_grid);

    int count = media_library_count();
    ESP_LOGI(TAG, "Populating library grid: %d items", count);

    for (int i = 0; i < count; i++) {
        const media_item_t *item = media_library_get(i);
        if (!item) continue;

        create_user_widget_uw_video_card(objects.lib_grid, 0);
        lv_obj_t *card = lv_obj_get_child(objects.lib_grid, -1);
        if (!card) continue;

        lv_obj_set_user_data(card, (void *)(uintptr_t)i);

        // Children of card_root:
        // Child 0: img_thumb
        // Child 1: badge_now
        // Child 2: bar_resume
        // Child 3: lbl_card_title
        // Child 4: lbl_card_meta
        lv_obj_t *img_thumb = lv_obj_get_child(card, 0);
        lv_obj_t *badge = lv_obj_get_child(card, 1);
        lv_obj_t *bar_res = lv_obj_get_child(card, 2);
        lv_obj_t *lbl_title = lv_obj_get_child(card, 3);
        lv_obj_t *lbl_meta = lv_obj_get_child(card, 4);

        if (img_thumb) {
            if (item->thumb_dsc) {
                lv_image_set_src(img_thumb, item->thumb_dsc);
            } else {
                lv_image_set_src(img_thumb, &img_film);
            }
        }

        if (lbl_title) {
            lv_label_set_text(lbl_title, item->title[0] ? item->title : item->path);
        }

        if (lbl_meta) {
            if (item->dur_ms > 0) {
                uint32_t s = item->dur_ms / 1000;
                char meta_buf[32];
                snprintf(meta_buf, sizeof(meta_buf), "%lu:%02lu", (unsigned long)(s / 60), (unsigned long)(s % 60));
                lv_label_set_text(lbl_meta, meta_buf);
            }
        }

        if (badge) {
            if (i == s_current_track_idx) {
                lv_obj_remove_flag(badge, LV_OBJ_FLAG_HIDDEN);
            } else {
                lv_obj_add_flag(badge, LV_OBJ_FLAG_HIDDEN);
            }
        }

        if (bar_res) {
            if (item->resume_ms > 0 && item->dur_ms > 0) {
                lv_obj_remove_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
                int32_t pct = (int32_t)(((uint64_t)item->resume_ms * 1000) / item->dur_ms);
                lv_bar_set_value(bar_res, pct, LV_ANIM_OFF);
            } else {
                lv_obj_add_flag(bar_res, LV_OBJ_FLAG_HIDDEN);
            }
        }

        // Dimmed card for incompatible videos (06 §7.2)
        if (!item->compatible) {
            lv_obj_set_style_opa(card, LV_OPA_50, 0);
            if (lbl_meta && item->incompat[0]) {
                lv_label_set_text(lbl_meta, item->incompat);
            }
        } else if (!item->rotated) {
            // Classic 480x320 video notice
            if (lbl_meta) {
                lv_label_set_text(lbl_meta, "Sin girar");
            }
        }
    }
}

void action_set_brightness(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_osd_timeout(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_show_stats(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_mini_progress(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_repeat(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_shuffle(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_resume(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}

void action_set_seek_step(lv_event_t *e) {
    s_last_touch_time = esp_timer_get_time() / 1000;
}
