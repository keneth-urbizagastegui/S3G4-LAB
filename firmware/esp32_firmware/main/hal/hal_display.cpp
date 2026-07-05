#include "hal_display.h"
#include "FT6X36.h"
#include "sdkconfig.h"
#include "ui_common.h"
#include <driver/gpio.h>
#include <driver/ledc.h>
#include <driver/spi_master.h>
#include <esp_err.h>
#include <esp_lcd_ili9488.h>
#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_log.h>
#include <lvgl.h>
#include <stdio.h>

static const char *TAG = "hal_display";

// Instantiate touch controller in polling mode, mapping CTP_RST to GPIO 7
static FT6X36 touch_controller(-1, 7);

// Callback to read touch events for LVGL 9
static void touch_read_cb(lv_indev_t *indev, lv_indev_data_t *data) {
  TPoint point;
  TEvent event;

  touch_controller.poll(&point, &event);

  static lv_coord_t last_x = 0, last_y = 0;

  if (event == TEvent::TouchStart || event == TEvent::TouchMove) {
    last_x = point.x;
    last_y = point.y;
    data->state = LV_INDEV_STATE_PRESSED;
    data->point.x = last_x;
    data->point.y = last_y;
  } else {
    data->state = LV_INDEV_STATE_RELEASED;
    data->point.x = last_x;
    data->point.y = last_y;
  }
}

static const int DISPLAY_HORIZONTAL_PIXELS = 480;
static const int DISPLAY_VERTICAL_PIXELS = 320;
static const int DISPLAY_COMMAND_BITS = 8;
static const int DISPLAY_PARAMETER_BITS = 8;

static const size_t LV_BUFFER_SIZE = DISPLAY_HORIZONTAL_PIXELS * 40;
static const int SPI_MAX_TRANSFER_SIZE = DISPLAY_HORIZONTAL_PIXELS * 40 * 3;

static const unsigned int DISPLAY_REFRESH_HZ = 40000000;
static const int DISPLAY_SPI_QUEUE_LEN = 10;

#if CONFIG_IDF_TARGET_ESP32S3
static const gpio_num_t SPI_CLOCK = GPIO_NUM_11;
static const gpio_num_t SPI_MOSI = GPIO_NUM_10;
static const gpio_num_t SPI_MISO = GPIO_NUM_13;
static const gpio_num_t TFT_CS = GPIO_NUM_3;
static const gpio_num_t TFT_RESET = GPIO_NUM_46;
static const gpio_num_t TFT_DC = GPIO_NUM_9;
static const gpio_num_t TFT_BACKLIGHT = GPIO_NUM_12;
#else
#error Unsure which GPIO to use for SPI/TFT, please update code accordingly.
#endif

static const lcd_rgb_element_order_t TFT_COLOR_MODE = LCD_RGB_ELEMENT_ORDER_BGR;

static const ledc_mode_t BACKLIGHT_LEDC_MODE = LEDC_LOW_SPEED_MODE;
static const ledc_channel_t BACKLIGHT_LEDC_CHANNEL = LEDC_CHANNEL_0;
static const ledc_timer_t BACKLIGHT_LEDC_TIMER = LEDC_TIMER_1;
static const ledc_timer_bit_t BACKLIGHT_LEDC_TIMER_RESOLUTION = LEDC_TIMER_10_BIT;
static const uint32_t BACKLIGHT_LEDC_FRQUENCY = 5000;

static esp_lcd_panel_io_handle_t lcd_io_handle = NULL;
esp_lcd_panel_handle_t lcd_handle = NULL;
static lv_display_t *lv_display = NULL;
static uint8_t *lv_buf_1 = NULL;
static uint8_t *lv_buf_2 = NULL;

static bool notify_lvgl_flush_ready(esp_lcd_panel_io_handle_t panel_io,
                                    esp_lcd_panel_io_event_data_t *edata,
                                    void *user_ctx) {
  if (lv_display != NULL) {
    lv_display_flush_ready(lv_display);
  }
  return false;
}

static void lvgl_flush_cb(lv_display_t *disp, const lv_area_t *area, uint8_t *px_map) {
  esp_lcd_panel_handle_t panel_handle = (esp_lcd_panel_handle_t)lv_display_get_user_data(disp);
  esp_lcd_panel_draw_bitmap(panel_handle, area->x1, area->y1, area->x2 + 1, area->y2 + 1, px_map);
}

static void display_brightness_init(void) {
  ledc_channel_config_t LCD_backlight_channel = {};
  LCD_backlight_channel.gpio_num = TFT_BACKLIGHT;
  LCD_backlight_channel.speed_mode = BACKLIGHT_LEDC_MODE;
  LCD_backlight_channel.channel = BACKLIGHT_LEDC_CHANNEL;
  LCD_backlight_channel.timer_sel = BACKLIGHT_LEDC_TIMER;
  LCD_backlight_channel.duty = 0;
  LCD_backlight_channel.hpoint = 0;
  LCD_backlight_channel.flags.output_invert = 0;

  ledc_timer_config_t LCD_backlight_timer = {};
  LCD_backlight_timer.speed_mode = BACKLIGHT_LEDC_MODE;
  LCD_backlight_timer.duty_resolution = BACKLIGHT_LEDC_TIMER_RESOLUTION;
  LCD_backlight_timer.timer_num = BACKLIGHT_LEDC_TIMER;
  LCD_backlight_timer.freq_hz = BACKLIGHT_LEDC_FRQUENCY;
  LCD_backlight_timer.clk_cfg = LEDC_AUTO_CLK;

  ESP_LOGI(TAG, "Initializing LEDC for backlight pin: %d", TFT_BACKLIGHT);
  ESP_ERROR_CHECK(ledc_timer_config(&LCD_backlight_timer));
  ESP_ERROR_CHECK(ledc_channel_config(&LCD_backlight_channel));
}

void display_brightness_set(int brightness_percentage) {
  if (brightness_percentage > 100) brightness_percentage = 100;
  if (brightness_percentage < 0) brightness_percentage = 0;
  uint32_t duty_cycle = (1023 * brightness_percentage) / 100;
  ESP_ERROR_CHECK(ledc_set_duty(BACKLIGHT_LEDC_MODE, BACKLIGHT_LEDC_CHANNEL, duty_cycle));
  ESP_ERROR_CHECK(ledc_update_duty(BACKLIGHT_LEDC_MODE, BACKLIGHT_LEDC_CHANNEL));
}

static void initialize_spi() {
  ESP_LOGI(TAG, "Initializing SPI bus (MOSI:%d, MISO:%d, CLK:%d)", SPI_MOSI, SPI_MISO, SPI_CLOCK);
  spi_bus_config_t bus = {};
  bus.mosi_io_num = SPI_MOSI;
  bus.miso_io_num = SPI_MISO;
  bus.sclk_io_num = SPI_CLOCK;
  bus.quadwp_io_num = GPIO_NUM_NC;
  bus.quadhd_io_num = GPIO_NUM_NC;
  bus.max_transfer_sz = SPI_MAX_TRANSFER_SIZE;
  bus.flags = SPICOMMON_BUSFLAG_SCLK | SPICOMMON_BUSFLAG_MISO |
              SPICOMMON_BUSFLAG_MOSI | SPICOMMON_BUSFLAG_MASTER;
  bus.intr_flags = ESP_INTR_FLAG_LOWMED;
  ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO));
}

static void initialize_display() {
  esp_lcd_panel_io_spi_config_t io_config = {};
  io_config.cs_gpio_num = TFT_CS;
  io_config.dc_gpio_num = TFT_DC;
  io_config.spi_mode = 0;
  io_config.pclk_hz = DISPLAY_REFRESH_HZ;
  io_config.trans_queue_depth = DISPLAY_SPI_QUEUE_LEN;
  io_config.on_color_trans_done = notify_lvgl_flush_ready;
  io_config.lcd_cmd_bits = DISPLAY_COMMAND_BITS;
  io_config.lcd_param_bits = DISPLAY_PARAMETER_BITS;
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 4, 0)
  io_config.cs_ena_pretrans = 0;
  io_config.cs_ena_posttrans = 0;
#endif
  io_config.flags.dc_low_on_data = 0;
  io_config.flags.octal_mode = 0;
  io_config.flags.sio_mode = 0;
  io_config.flags.lsb_first = 0;
  io_config.flags.cs_high_active = 0;

  esp_lcd_panel_dev_config_t lcd_config = {};
  lcd_config.reset_gpio_num = TFT_RESET;
  lcd_config.rgb_ele_order = TFT_COLOR_MODE;
  lcd_config.bits_per_pixel = 18;
  lcd_config.flags.reset_active_high = 0;
  lcd_config.vendor_config = NULL;

  ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI2_HOST, &io_config, &lcd_io_handle));
  ESP_ERROR_CHECK(esp_lcd_new_panel_ili9488_ips(lcd_io_handle, &lcd_config, LV_BUFFER_SIZE, &lcd_handle));

  ESP_ERROR_CHECK(esp_lcd_panel_reset(lcd_handle));
  ESP_ERROR_CHECK(esp_lcd_panel_init(lcd_handle));

  // Vendor recommended register tunings
  const uint8_t vcom_data[] = {0x00, 0x4D, 0x80};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xC5, vcom_data, sizeof(vcom_data));
  const uint8_t f7_data[] = {0xA9, 0x51, 0x2C, 0x82};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xF7, f7_data, sizeof(f7_data));
  const uint8_t c0_data[] = {0x0F, 0x0F};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xC0, c0_data, sizeof(c0_data));
  const uint8_t c1_data[] = {0x47};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xC1, c1_data, sizeof(c1_data));
  const uint8_t b1_data[] = {0xB0, 0x11};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xB1, b1_data, sizeof(b1_data));
  const uint8_t b4_data[] = {0x02};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xB4, b4_data, sizeof(b4_data));

  // Gamma Settings for IPS
  const uint8_t e0_data[] = {0x00, 0x07, 0x0B, 0x03, 0x0F, 0x05, 0x30, 0x56,
                             0x47, 0x04, 0x0B, 0x0A, 0x2D, 0x37, 0x0F};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xE0, e0_data, sizeof(e0_data));
  const uint8_t e1_data[] = {0x00, 0x0E, 0x13, 0x04, 0x11, 0x07, 0x39, 0x45,
                             0x50, 0x07, 0x10, 0x0D, 0x32, 0x36, 0x0F};
  esp_lcd_panel_io_tx_param(lcd_io_handle, 0xE1, e1_data, sizeof(e1_data));

  ESP_ERROR_CHECK(esp_lcd_panel_invert_color(lcd_handle, true));
  ESP_ERROR_CHECK(esp_lcd_panel_swap_xy(lcd_handle, true));
  ESP_ERROR_CHECK(esp_lcd_panel_mirror(lcd_handle, false, false));
  ESP_ERROR_CHECK(esp_lcd_panel_set_gap(lcd_handle, 0, 0));
  ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(lcd_handle, true));
}

static void initialize_lvgl() {
  ESP_LOGI(TAG, "Initializing LVGL");
  lv_init();

  size_t buffer_size_bytes = LV_BUFFER_SIZE * 2;
  lv_buf_1 = (uint8_t *)heap_caps_malloc(buffer_size_bytes, MALLOC_CAP_DMA);
  assert(lv_buf_1 != NULL);
  lv_buf_2 = (uint8_t *)heap_caps_malloc(buffer_size_bytes, MALLOC_CAP_DMA);
  assert(lv_buf_2 != NULL);

  lv_display = lv_display_create(DISPLAY_HORIZONTAL_PIXELS, DISPLAY_VERTICAL_PIXELS);
  assert(lv_display != NULL);

  lv_display_set_user_data(lv_display, lcd_handle);
  lv_display_set_buffers(lv_display, lv_buf_1, lv_buf_2, buffer_size_bytes, LV_DISPLAY_RENDER_MODE_PARTIAL);
  lv_display_set_flush_cb(lv_display, lvgl_flush_cb);
}

static void initialize_touch() {
  ESP_LOGI(TAG, "Initializing Touch Controller");
  if (touch_controller.begin(FT6X36_DEFAULT_THRESHOLD, DISPLAY_VERTICAL_PIXELS, DISPLAY_HORIZONTAL_PIXELS)) {
    ESP_LOGI(TAG, "Touch controller initialized successfully");
    touch_controller.setRotation(1);
  } else {
    ESP_LOGE(TAG, "Touch controller initialization failed!");
  }

  lv_indev_t *indev = lv_indev_create();
  lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);
  lv_indev_set_read_cb(indev, touch_read_cb);
}

void hal_display_init(void) {
  display_brightness_init();
  display_brightness_set(0);
  initialize_spi();
  initialize_display();
  initialize_lvgl();
  initialize_touch();
}

void update_display_inversion(void) {
  if (lcd_handle != NULL) {
    esp_lcd_panel_invert_color(lcd_handle, !opt_disp_inver);
  }
}
