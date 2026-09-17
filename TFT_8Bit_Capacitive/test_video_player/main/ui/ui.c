#include "ui.h"
#include "screens.h"
#include "images.h"
#include "actions.h"
#include "vars.h"

#include <string.h>

static int16_t currentScreen = -1;
static lv_obj_t *s_screens[3] = {NULL, NULL, NULL};

static lv_obj_t *getLvglObjectFromIndex(int32_t index) {
    if (index == -1) {
        return 0;
    }
    return ((lv_obj_t **)&objects)[index];
}

void loadScreen(enum ScreensEnum screenId) {
    currentScreen = screenId - 1;
    if (currentScreen >= 0 && currentScreen < 3 && s_screens[currentScreen]) {
        lv_screen_load(s_screens[currentScreen]);
    } else {
        lv_obj_t *screen = getLvglObjectFromIndex(currentScreen);
        lv_screen_load(screen);
    }
}

void ui_init() {
    create_screens();
    s_screens[0] = objects.scr_player;
    s_screens[1] = objects.scr_library;
    s_screens[2] = objects.scr_no_media;
    loadScreen(SCREEN_ID_SCR_PLAYER);
}

void ui_tick() {
    tick_screen(currentScreen);
}