idf_component_register(
    SRCS "media_library.c" "settings_nvs.c" "main.c" "lcd_bus.c" "ili9488_8080.c" "ft6236_i2c.c" "sdcard_spi.c" "avi_player.c" "spotify_ui.c" "perf.c" "player.c" "tear_diag.c"
    INCLUDE_DIRS "."
    REQUIRES esp_lcd driver esp_driver_gpio esp_driver_i2c esp_driver_spi fatfs vfs esp_timer freertos heap lvgl esp_driver_ledc espressif__esp_new_jpeg esp_system nvs_flash espressif__cjson
)
