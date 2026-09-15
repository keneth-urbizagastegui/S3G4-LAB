#include "ft6236_i2c.h"
#include "driver/i2c_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "ft6236_i2c";

#define TOUCH_SDA_IO        GPIO_NUM_6
#define TOUCH_SCL_IO        GPIO_NUM_5
#define TOUCH_RST_IO        GPIO_NUM_7
#define FT6236_I2C_ADDR     0x38

static i2c_master_bus_handle_t s_i2c_bus = NULL;
static i2c_master_dev_handle_t s_i2c_dev = NULL;

static void ft6236_write_reg(uint8_t reg, uint8_t val) {
    uint8_t buf[2] = {reg, val};
    i2c_master_transmit(s_i2c_dev, buf, sizeof(buf), 1000);
}

static esp_err_t ft6236_read_reg(uint8_t reg, uint8_t *val) {
    esp_err_t ret = i2c_master_transmit(s_i2c_dev, &reg, 1, 1000);
    if (ret != ESP_OK) return ret;
    return i2c_master_receive(s_i2c_dev, val, 1, 1000);
}

esp_err_t ft6236_i2c_init(void) {
    ESP_LOGI(TAG, "Configurando bus I2C maestro (SDA: %d, SCL: %d)...", TOUCH_SDA_IO, TOUCH_SCL_IO);
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = TOUCH_SDA_IO,
        .scl_io_num = TOUCH_SCL_IO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags = {
            .enable_internal_pullup = true,
        },
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &s_i2c_bus));

    // Escanear bus I2C para verificar presencia del chip
    ESP_LOGI(TAG, "Escaneando bus I2C (0x08 a 0x77)...");
    uint8_t target_addr = FT6236_I2C_ADDR;
    int found_count = 0;
    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        if (i2c_master_probe(s_i2c_bus, addr, 20) == ESP_OK) {
            ESP_LOGI(TAG, "  -> Dispositivo I2C detectado en direccion: 0x%02X", addr);
            target_addr = addr;
            found_count++;
        }
    }

    if (found_count == 0) {
        ESP_LOGW(TAG, "¡ATENCIÓN! No se detectó respuesta I2C.");
        ESP_LOGW(TAG, "Verifique: Pin 30 (CTP_SCL) -> GPIO 5, Pin 31 (CTP_SDA) -> GPIO 6.");
    }

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = target_addr,
        .scl_speed_hz = 400000, // 400 kHz Fast-Mode (4x velocidad de refresco)
    };
    esp_err_t ret = i2c_master_bus_add_device(s_i2c_bus, &dev_cfg, &s_i2c_dev);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Error agregando dispositivo I2C: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configurar registros de operación estándar FT6236
    ft6236_write_reg(0x00, 0x00); // Normal Operating Mode
    ft6236_write_reg(0x80, 40);   // Threshold = 40
    ft6236_write_reg(0x88, 0x0E); // Active rate = 14 ms

    uint8_t chip_id = 0, vend_id = 0;
    if (ft6236_read_reg(0xA3, &chip_id) == ESP_OK) {
        ESP_LOGI(TAG, "  -> Chip ID verificado: 0x%02X", chip_id);
    }
    if (ft6236_read_reg(0xA8, &vend_id) == ESP_OK) {
        ESP_LOGI(TAG, "  -> Panel/Vendor ID: 0x%02X", vend_id);
    }

    ESP_LOGI(TAG, "Panel táctil inicializado con éxito.");
    return ESP_OK;
}

esp_err_t ft6236_i2c_read(ft6236_touch_data_t *data) {
    if (!s_i2c_dev || !data) return ESP_ERR_INVALID_ARG;

    // 1. Enviar dirección de registro 0x02 (TD_STATUS) con condición STOP
    uint8_t reg = 0x02;
    esp_err_t err = i2c_master_transmit(s_i2c_dev, &reg, 1, 1000);
    if (err != ESP_OK) {
        data->touched = false;
        data->touch_count = 0;
        return err;
    }

    // 2. Leer 11 bytes en ráfaga para capturar Point 1 y Point 2 simultáneamente:
    //    buf[0]:  TD_STATUS (número de puntos tocados)
    //    buf[1]:  P1_XH (coordenada X alta + flags de evento P1)
    //    buf[2]:  P1_XL (coordenada X baja P1)
    //    buf[3]:  P1_YH (coordenada Y alta P1 + touch ID)
    //    buf[4]:  P1_YL (coordenada Y baja P1)
    //    buf[5]:  P1_WEIGHT
    //    buf[6]:  P1_MISC
    //    buf[7]:  P2_XH (coordenada X alta + flags de evento P2)
    //    buf[8]:  P2_XL (coordenada X baja P2)
    //    buf[9]:  P2_YH (coordenada Y alta P2 + touch ID)
    //    buf[10]: P2_YL (coordenada Y baja P2)
    uint8_t buf[11] = {0};
    err = i2c_master_receive(s_i2c_dev, buf, sizeof(buf), 1000);
    if (err != ESP_OK) {
        data->touched = false;
        data->touch_count = 0;
        return err;
    }

    static uint16_t s_last_x1 = 0;
    static uint16_t s_last_y1 = 0;
    static bool s_was_touched = false;

    uint8_t touch_count = buf[0] & 0x0F;
    uint8_t p1_event = (buf[1] >> 6) & 0x03; // Bits [7:6]: 0=Press, 1=Lift, 2=Contact, 3=NoEvent

    // Si el controlador reporta 0 toques o el evento es LiftUp (1) o NoEvent (3), descartar
    if (touch_count == 0 || touch_count > 2 || p1_event == 1 || p1_event == 3) {
        data->touched = false;
        data->touch_count = 0;
        s_was_touched = false;
        return ESP_OK;
    }

    // Coordenadas crudas físicas del sensor (X_raw: 0..319, Y_raw: 0..479)
    uint16_t raw_x1 = ((uint16_t)(buf[1] & 0x0F) << 8) | buf[2];
    uint16_t raw_y1 = ((uint16_t)(buf[3] & 0x0F) << 8) | buf[4];

    // Loop Engineering: Mapeo de orientación a Landscape horizontal (480 x 320)
    uint16_t screen_x1 = (raw_y1 < 480) ? raw_y1 : 479;
    uint16_t screen_y1 = (raw_x1 < 320) ? (319 - raw_x1) : 0;

    // Filtro de zona muerta (Deadband Filter) para P1
    if (s_was_touched) {
        int diff_x = (int)screen_x1 - (int)s_last_x1;
        int diff_y = (int)screen_y1 - (int)s_last_y1;
        if (diff_x >= -2 && diff_x <= 2 && diff_y >= -2 && diff_y <= 2) {
            screen_x1 = s_last_x1;
            screen_y1 = s_last_y1;
        }
    }

    s_last_x1 = screen_x1;
    s_last_y1 = screen_y1;
    s_was_touched = true;

    data->x1 = screen_x1;
    data->y1 = screen_y1;
    data->x = screen_x1;
    data->y = screen_y1;

    // Si se detecta un segundo punto de contacto (True Multi-Touch)
    if (touch_count >= 2) {
        uint16_t raw_x2 = ((uint16_t)(buf[7] & 0x0F) << 8) | buf[8];
        uint16_t raw_y2 = ((uint16_t)(buf[9] & 0x0F) << 8) | buf[10];

        data->x2 = (raw_y2 < 480) ? raw_y2 : 479;
        data->y2 = (raw_x2 < 320) ? (319 - raw_x2) : 0;
    } else {
        data->x2 = data->x1;
        data->y2 = data->y1;
    }

    data->touch_count = touch_count;
    data->touched = true;

    return ESP_OK;
}
