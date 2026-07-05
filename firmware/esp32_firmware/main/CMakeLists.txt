idf_component_register(
    INCLUDE_DIRS . hal ui ui/screens
    SRCS main.cpp
         hal/hal_display.cpp
         hal/FT6X36.cpp
         hal/comm_spi_master.cpp
         hal/wifi_ap.cpp
         ui/ui_common.cpp
         ui/fondo_utec.c
         ui/screens/ui_splash.cpp
         ui/screens/ui_home.cpp
         ui/screens/ui_scope.cpp
         ui/screens/ui_dmm.cpp
         ui/screens/ui_gen.cpp
         ui/screens/ui_view.cpp
         ui/screens/ui_person.cpp
         ui/screens/ui_connectivity.cpp
    REQUIRES lvgl esp_lcd_ili9488 esp_wifi esp_event nvs_flash esp_http_server spiffs
)

add_compile_definitions(
    CONFIG_TOUCH_SDA=6
    CONFIG_TOUCH_SCL=5
    CONFIG_TOUCH_SDL=5
    CONFIG_I2C_MASTER_FREQUENCY=400000
    CONFIG_FT6X36_DEBUG=0
    CONFIG_FT6X36_DEBUG_EVENTS=0
)