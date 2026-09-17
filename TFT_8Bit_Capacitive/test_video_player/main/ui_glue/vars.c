#include "ui/vars.h"
#include "ui_glue.h"
#include "player.h"
#include "settings_nvs.h"
#include "media_library.h"
#include "perf.h"
#include "sdcard_spi.h"
#include <stdio.h>
#include <string.h>

typedef struct {
    char title[64];
    char subtitle[64];
    char pos_text[16];
    char dur_text[16];
    int32_t seek_value;
    bool is_playing;
    int32_t repeat_mode;
    bool shuffle;
    char fps_text[24];
    bool show_stats;
    char library_summary[64];
    int32_t brightness;
    char stats_pres_fps[16];
    char stats_dec_fps[16];
    char stats_dropped[32];
    char stats_read[32];
    char stats_decode[32];
    char stats_blit[24];
    char stats_file[48];
} ui_vars_cache_t;

static ui_vars_cache_t s_cache = {
    .title = "",
    .subtitle = "",
    .pos_text = "0:00",
    .dur_text = "0:00",
    .seek_value = 0,
    .is_playing = false,
    .repeat_mode = 1,
    .shuffle = false,
    .fps_text = "30.0 fps",
    .show_stats = false,
    .library_summary = "0 videos",
    .brightness = 70,
    .stats_pres_fps = "0.0",
    .stats_dec_fps = "0.0",
    .stats_dropped = "0 (0.0 %)",
    .stats_read = "0.0 / 0.0 ms",
    .stats_decode = "0.0 / 0.0 ms",
    .stats_blit = "0.0 ms",
    .stats_file = "320x480 · MJPEG"
};

void ui_glue_update_cache(const player_status_t *st) {
    if (st) {
        if (st->title[0] != '\0') {
            snprintf(s_cache.title, sizeof(s_cache.title), "%s", st->title);
        } else {
            snprintf(s_cache.title, sizeof(s_cache.title), "Track %ld", (long)(st->track_index + 1));
        }

        if (st->subtitle[0] != '\0') {
            snprintf(s_cache.subtitle, sizeof(s_cache.subtitle), "%s", st->subtitle);
        } else {
            snprintf(s_cache.subtitle, sizeof(s_cache.subtitle), "%02ld / %02ld · %.0f fps",
                     (long)(st->track_index + 1), (long)(st->track_count > 0 ? st->track_count : 1),
                     st->fps_milli > 0 ? (st->fps_milli / 1000.0f) : 30.0f);
        }

        uint32_t pos_sec = (uint32_t)(st->pos_ms / 1000);
        uint32_t dur_sec = (uint32_t)(st->dur_ms / 1000);

        if (pos_sec >= 3600) {
            snprintf(s_cache.pos_text, sizeof(s_cache.pos_text), "%lu:%02lu:%02lu",
                     (unsigned long)(pos_sec / 3600), (unsigned long)((pos_sec % 3600) / 60), (unsigned long)(pos_sec % 60));
        } else {
            snprintf(s_cache.pos_text, sizeof(s_cache.pos_text), "%lu:%02lu",
                     (unsigned long)(pos_sec / 60), (unsigned long)(pos_sec % 60));
        }

        if (dur_sec >= 3600) {
            snprintf(s_cache.dur_text, sizeof(s_cache.dur_text), "%lu:%02lu:%02lu",
                     (unsigned long)(dur_sec / 3600), (unsigned long)((dur_sec % 3600) / 60), (unsigned long)(dur_sec % 60));
        } else {
            snprintf(s_cache.dur_text, sizeof(s_cache.dur_text), "%lu:%02lu",
                     (unsigned long)(dur_sec / 60), (unsigned long)(dur_sec % 60));
        }

        if (st->dur_ms > 0) {
            s_cache.seek_value = (int32_t)((st->pos_ms * 1000) / st->dur_ms);
            if (s_cache.seek_value > 1000) s_cache.seek_value = 1000;
        } else {
            s_cache.seek_value = 0;
        }

        s_cache.is_playing = (st->state == PST_PLAYING);
        s_cache.repeat_mode = (int32_t)st->repeat;
        s_cache.shuffle = st->shuffle;

        snprintf(s_cache.fps_text, sizeof(s_cache.fps_text), "%.1f fps", st->pres_fps);

        snprintf(s_cache.stats_pres_fps, sizeof(s_cache.stats_pres_fps), "%.1f fps", st->pres_fps);
        snprintf(s_cache.stats_dec_fps, sizeof(s_cache.stats_dec_fps), "%.1f fps", st->dec_fps);
        snprintf(s_cache.stats_dropped, sizeof(s_cache.stats_dropped), "%lu", (unsigned long)st->dropped);
        snprintf(s_cache.stats_read, sizeof(s_cache.stats_read), "< 15 ms");
        snprintf(s_cache.stats_decode, sizeof(s_cache.stats_decode), "< 20 ms");
        snprintf(s_cache.stats_blit, sizeof(s_cache.stats_blit), "< 20 ms");
        snprintf(s_cache.stats_file, sizeof(s_cache.stats_file), "%ux%u · MJPEG",
                 st->width ? st->width : 320, st->height ? st->height : 480);
    }

    int vcount = media_library_count();
    int ccount = media_library_compatible_count();
    int incount = vcount - ccount;
    if (incount > 0) {
        snprintf(s_cache.library_summary, sizeof(s_cache.library_summary),
                 "%d videos · %d no compatible%s", vcount, incount, incount > 1 ? "s" : "");
    } else {
        snprintf(s_cache.library_summary, sizeof(s_cache.library_summary),
                 "%d videos · todos compatibles", vcount);
    }
}

// ----------------- EEZ Native Getters -----------------
const char *get_var_title() { return s_cache.title; }
void set_var_title(const char *value) { if (value) snprintf(s_cache.title, sizeof(s_cache.title), "%s", value); }

const char *get_var_subtitle() { return s_cache.subtitle; }
void set_var_subtitle(const char *value) { if (value) snprintf(s_cache.subtitle, sizeof(s_cache.subtitle), "%s", value); }

const char *get_var_pos_text() { return s_cache.pos_text; }
void set_var_pos_text(const char *value) { if (value) snprintf(s_cache.pos_text, sizeof(s_cache.pos_text), "%s", value); }

const char *get_var_dur_text() { return s_cache.dur_text; }
void set_var_dur_text(const char *value) { if (value) snprintf(s_cache.dur_text, sizeof(s_cache.dur_text), "%s", value); }

int32_t get_var_seek_value() { return s_cache.seek_value; }
void set_var_seek_value(int32_t value) { s_cache.seek_value = value; }

bool get_var_is_playing() { return s_cache.is_playing; }
void set_var_is_playing(bool value) { s_cache.is_playing = value; }

int32_t get_var_repeat_mode() { return s_cache.repeat_mode; }
void set_var_repeat_mode(int32_t value) { s_cache.repeat_mode = value; }

bool get_var_shuffle() { return s_cache.shuffle; }
void set_var_shuffle(bool value) { s_cache.shuffle = value; }

const char *get_var_fps_text() { return s_cache.fps_text; }
void set_var_fps_text(const char *value) { if (value) snprintf(s_cache.fps_text, sizeof(s_cache.fps_text), "%s", value); }

bool get_var_show_stats() { return s_cache.show_stats; }
void set_var_show_stats(bool value) { s_cache.show_stats = value; }

const char *get_var_library_summary() { return s_cache.library_summary; }
void set_var_library_summary(const char *value) { if (value) snprintf(s_cache.library_summary, sizeof(s_cache.library_summary), "%s", value); }

int32_t get_var_brightness() { return s_cache.brightness; }
void set_var_brightness(int32_t value) {
    if (value < 0) value = 0;
    if (value > 100) value = 100;
    s_cache.brightness = value;
}

const char *get_var_stats_pres_fps() { return s_cache.stats_pres_fps; }
void set_var_stats_pres_fps(const char *value) { if (value) snprintf(s_cache.stats_pres_fps, sizeof(s_cache.stats_pres_fps), "%s", value); }

const char *get_var_stats_dec_fps() { return s_cache.stats_dec_fps; }
void set_var_stats_dec_fps(const char *value) { if (value) snprintf(s_cache.stats_dec_fps, sizeof(s_cache.stats_dec_fps), "%s", value); }

const char *get_var_stats_dropped() { return s_cache.stats_dropped; }
void set_var_stats_dropped(const char *value) { if (value) snprintf(s_cache.stats_dropped, sizeof(s_cache.stats_dropped), "%s", value); }

const char *get_var_stats_read() { return s_cache.stats_read; }
void set_var_stats_read(const char *value) { if (value) snprintf(s_cache.stats_read, sizeof(s_cache.stats_read), "%s", value); }

const char *get_var_stats_decode() { return s_cache.stats_decode; }
void set_var_stats_decode(const char *value) { if (value) snprintf(s_cache.stats_decode, sizeof(s_cache.stats_decode), "%s", value); }

const char *get_var_stats_blit() { return s_cache.stats_blit; }
void set_var_stats_blit(const char *value) { if (value) snprintf(s_cache.stats_blit, sizeof(s_cache.stats_blit), "%s", value); }

const char *get_var_stats_file() { return s_cache.stats_file; }
void set_var_stats_file(const char *value) { if (value) snprintf(s_cache.stats_file, sizeof(s_cache.stats_file), "%s", value); }
