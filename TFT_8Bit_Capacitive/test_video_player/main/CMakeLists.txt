idf_component_register(
    SRCS "media_library.c" "settings_nvs.c" "main.c" "lcd_bus.c" "ili9488_8080.c" "ft6236_i2c.c" "sdcard_spi.c" "avi_player.c" "perf.c" "player.c" "tear_diag.c"
         "ui/images.c" "ui/screens.c" "ui/styles.c" "ui/ui.c"
         "ui/ui_image_film.c" "ui/ui_image_fwd10.c" "ui/ui_image_lock.c"
         "ui/ui_image_queue.c" "ui/ui_image_rew10.c" "ui/ui_image_sdcard.c"
         "ui/ui_image_sdcard_big.c" "ui/ui_image_sdcard_error_big.c"
         "ui_glue/actions.c" "ui_glue/vars.c"
    INCLUDE_DIRS "." "ui" "ui_glue"
    REQUIRES esp_lcd driver esp_driver_gpio esp_driver_i2c esp_driver_spi fatfs vfs esp_timer freertos heap lvgl esp_driver_ledc espressif__esp_new_jpeg esp_system nvs_flash espressif__cjson
)
