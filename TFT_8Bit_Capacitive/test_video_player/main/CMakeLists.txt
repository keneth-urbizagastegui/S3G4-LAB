idf_component_register(
    SRCS "media_library.c" "settings_nvs.c" "main.c" "lcd_bus.c" "ili9488_8080.c" "ft6236_i2c.c" "sdcard_spi.c" "avi_player.c" "perf.c" "player.c" "tear_diag.c"
         "ui/images.c" "ui/screens.c" "ui/styles.c" "ui/ui.c"
         "ui/ui_image_back.c" "ui/ui_image_brightness.c" "ui/ui_image_chevron_down.c"
         "ui/ui_image_close.c" "ui/ui_image_film.c" "ui/ui_image_fwd10.c"
         "ui/ui_image_lock.c" "ui/ui_image_lock_big.c" "ui/ui_image_next.c"
         "ui/ui_image_pause.c" "ui/ui_image_play.c" "ui/ui_image_prev.c"
         "ui/ui_image_queue.c" "ui/ui_image_repeat.c" "ui/ui_image_repeat_one.c"
         "ui/ui_image_rescan.c" "ui/ui_image_rew10.c" "ui/ui_image_sdcard.c"
         "ui/ui_image_sdcard_big.c" "ui/ui_image_sdcard_error_big.c"
         "ui/ui_image_seek_back.c" "ui/ui_image_seek_fwd.c" "ui/ui_image_settings.c"
         "ui/ui_image_shuffle.c" "ui/ui_image_warning.c"
         "ui_glue/actions.c" "ui_glue/vars.c"
         "ui_fonts/ui_font_montserrat_12.c" "ui_fonts/ui_font_montserrat_14.c" "ui_fonts/ui_font_montserrat_20.c"
    INCLUDE_DIRS "." "ui" "ui_glue" "ui_fonts"
    REQUIRES esp_lcd driver esp_driver_gpio esp_driver_i2c esp_driver_spi fatfs vfs esp_timer freertos heap lvgl esp_driver_ledc espressif__esp_new_jpeg esp_system nvs_flash espressif__cjson
)

target_compile_definitions(${COMPONENT_LIB} PRIVATE LV_LVGL_H_INCLUDE_SIMPLE)
