/*
 * comm_spi_master.cpp
 *
 *  Created on: Jun 11, 2026
 *      Author: Antigravity
 */

#include "comm_spi_master.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include <string.h>

static const char *TAG = "comm_spi_master";

static spi_device_handle_t spi_device = NULL;
static SemaphoreHandle_t xCommSpiSem = NULL;
static SemaphoreHandle_t xLatestTelemetryMutex = NULL;
static SemaphoreHandle_t xSpiTransferMutex = NULL;
static QueueHandle_t xTelemetryQueue = NULL;

static tSpiTxPayload *latest_telemetry = NULL;
static bool latest_telemetry_valid = false;

#define TELEMETRY_QUEUE_SIZE 4

// FreeRTOS Task handle
static TaskHandle_t spi_task_handle = NULL;

// ISR Handler for DATA_READY GPIO
static void IRAM_ATTR drdy_gpio_isr_handler(void* arg) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xSemaphoreGiveFromISR(xCommSpiSem, &xHigherPriorityTaskWoken);
    if (xHigherPriorityTaskWoken) {
        portYIELD_FROM_ISR();
    }
}

// SPI Master task running on Core 1
static void comm_spi_master_task(void *pvParameters) {
    ESP_LOGI(TAG, "SPI Master Telemetry task started on core %d", xPortGetCoreID());

    // Allocate receive buffer in DMA-capable memory
    tSpiTxPayload *rx_buf = (tSpiTxPayload *)heap_caps_malloc(sizeof(tSpiTxPayload), MALLOC_CAP_DMA);
    if (rx_buf == NULL) {
        ESP_LOGE(TAG, "Failed to allocate DMA buffer for telemetry!");
        vTaskDelete(NULL);
        return;
    }

    // Dummy TX buffer (we don't need to send anything meaningful during telemetry read, but SPI is full duplex)
    uint8_t *tx_buf = (uint8_t *)heap_caps_malloc(sizeof(tSpiTxPayload), MALLOC_CAP_DMA);
    if (tx_buf == NULL) {
        ESP_LOGE(TAG, "Failed to allocate dummy TX buffer!");
        heap_caps_free(rx_buf);
        vTaskDelete(NULL);
        return;
    }
    memset(tx_buf, 0, sizeof(tSpiTxPayload));

    while (1) {
        // Wait for DATA_READY interrupt
        if (xSemaphoreTake(xCommSpiSem, portMAX_DELAY) == pdTRUE) {
            // Read telemetry packet from STM32 (2064 Bytes)
            spi_transaction_t transaction = {};
            transaction.length = COMM_SPI_TX_LEN * 8; // In bits
            transaction.rx_buffer = rx_buf;
            transaction.tx_buffer = tx_buf;

            xSemaphoreTake(xSpiTransferMutex, portMAX_DELAY);
            esp_err_t err = spi_device_transmit(spi_device, &transaction);
            xSemaphoreGive(xSpiTransferMutex);
            if (err == ESP_OK) {
                // Verify magic number
                if (rx_buf->header.magic_number == SPI_PACKET_MAGIC) {
                    // Update latest telemetry for local display
                    if (xSemaphoreTake(xLatestTelemetryMutex, pdMS_TO_TICKS(5)) == pdTRUE) {
                        memcpy(latest_telemetry, rx_buf, sizeof(tSpiTxPayload));
                        latest_telemetry_valid = true;
                        xSemaphoreGive(xLatestTelemetryMutex);
                    }

                    // Push to queue for WebSockets streaming (drop oldest if full)
                    if (uxQueueMessagesWaiting(xTelemetryQueue) >= TELEMETRY_QUEUE_SIZE) {
                        tSpiTxPayload dummy;
                        xQueueReceive(xTelemetryQueue, &dummy, 0); // Drop oldest frame
                    }
                    xQueueSend(xTelemetryQueue, rx_buf, 0);
                } else {
                    ESP_LOGW(TAG, "Invalid SPI magic number: 0x%04X (expected 0x%04X)",
                             rx_buf->header.magic_number, SPI_PACKET_MAGIC);
                }
            } else {
                ESP_LOGE(TAG, "SPI transmission failed: %s", esp_err_to_name(err));
            }
        }
    }

    heap_caps_free(rx_buf);
    heap_caps_free(tx_buf);
    vTaskDelete(NULL);
}

esp_err_t comm_spi_master_init(void) {
    ESP_LOGI(TAG, "Initializing SPI Master (MISO:%d, MOSI:%d, CLK:%d, CS:%d, DRDY:%d)",
             STM32_PIN_MISO, STM32_PIN_MOSI, STM32_PIN_CLK, STM32_PIN_CS, STM32_PIN_DRDY);

    // Initialize synchronization primitives
    xCommSpiSem = xSemaphoreCreateBinary();
    xLatestTelemetryMutex = xSemaphoreCreateMutex();
    xSpiTransferMutex = xSemaphoreCreateMutex();
    xTelemetryQueue = xQueueCreate(TELEMETRY_QUEUE_SIZE, sizeof(tSpiTxPayload));
    
    latest_telemetry = (tSpiTxPayload *)heap_caps_malloc(sizeof(tSpiTxPayload), MALLOC_CAP_SPIRAM);
    if (latest_telemetry == NULL) {
        latest_telemetry = (tSpiTxPayload *)malloc(sizeof(tSpiTxPayload));
    }
    latest_telemetry_valid = false;

    if (xCommSpiSem == NULL || xLatestTelemetryMutex == NULL || xTelemetryQueue == NULL || xSpiTransferMutex == NULL || latest_telemetry == NULL) {
        ESP_LOGE(TAG, "Failed to create FreeRTOS sync objects!");
        return ESP_ERR_NO_MEM;
    }

    // Configure SPI bus
    spi_bus_config_t bus_cfg = {};
    bus_cfg.miso_io_num = STM32_PIN_MISO;
    bus_cfg.mosi_io_num = STM32_PIN_MOSI;
    bus_cfg.sclk_io_num = STM32_PIN_CLK;
    bus_cfg.quadwp_io_num = -1;
    bus_cfg.quadhd_io_num = -1;
    bus_cfg.max_transfer_sz = COMM_SPI_TX_LEN;
    bus_cfg.flags = SPICOMMON_BUSFLAG_MASTER;

    // Use SPI3_HOST since SPI2_HOST is used by LCD display
    esp_err_t ret = spi_bus_initialize(STM32_SPI_HOST, &bus_cfg, SPI_DMA_CH_AUTO);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize SPI bus: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure SPI device
    spi_device_interface_config_t dev_cfg = {};
    dev_cfg.clock_speed_hz = 10000000;          // 10 MHz (Safe for breadboard/jumper wires)
    dev_cfg.mode = 0;                           // CPOL=0, CPHA=0
    dev_cfg.spics_io_num = STM32_PIN_CS;
    dev_cfg.queue_size = 3;
    dev_cfg.flags = 0;

    ret = spi_bus_add_device(STM32_SPI_HOST, &dev_cfg, &spi_device);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to add SPI device: %s", esp_err_to_name(ret));
        spi_bus_free(STM32_SPI_HOST);
        return ret;
    }

    // Configure DATA_READY Pin (Input, Rising Edge Interrupt)
    gpio_config_t io_conf = {};
    io_conf.intr_type = GPIO_INTR_POSEDGE; // Trigger on rising edge
    io_conf.pin_bit_mask = (1ULL << STM32_PIN_DRDY);
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pull_down_en = GPIO_PULLDOWN_ENABLE;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    
    ret = gpio_config(&io_conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure DATA_READY GPIO: %s", esp_err_to_name(ret));
        return ret;
    }

    // Install GPIO ISR service (may already be installed by touch driver)
    gpio_install_isr_service(0);
    
    ret = gpio_isr_handler_add((gpio_num_t)STM32_PIN_DRDY, drdy_gpio_isr_handler, NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to add GPIO ISR handler: %s", esp_err_to_name(ret));
        return ret;
    }

    // Start Real-Time Telemetry Task on Core 0 (Comms Core) with priority 8
    xTaskCreatePinnedToCore(comm_spi_master_task, "spi_master_rt", 4096, NULL, 8, &spi_task_handle, 0);

    return ESP_OK;
}

esp_err_t comm_spi_master_send_cmd(uint8_t cmd_id, uint8_t param1, uint32_t data) {
    if (spi_device == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    // Allocate command buffers in DMA-capable memory
    tSpiRxCmd *cmd_tx = (tSpiRxCmd *)heap_caps_malloc(sizeof(tSpiRxCmd), MALLOC_CAP_DMA);
    tSpiRxCmd *cmd_rx = (tSpiRxCmd *)heap_caps_malloc(sizeof(tSpiRxCmd), MALLOC_CAP_DMA);
    if (cmd_tx == NULL || cmd_rx == NULL) {
        if (cmd_tx) heap_caps_free(cmd_tx);
        if (cmd_rx) heap_caps_free(cmd_rx);
        return ESP_ERR_NO_MEM;
    }

    cmd_tx->sync = SPI_CMD_SYNC;
    cmd_tx->cmd_id = cmd_id;
    cmd_tx->param1 = param1;
    cmd_tx->data = data;
    cmd_tx->checksum = cmd_tx->sync + cmd_tx->cmd_id + cmd_tx->param1 +
                       (cmd_tx->data & 0xFF) + ((cmd_tx->data >> 8) & 0xFF) +
                       ((cmd_tx->data >> 16) & 0xFF) + ((cmd_tx->data >> 24) & 0xFF);

    spi_transaction_t transaction = {};
    transaction.length = COMM_SPI_RX_LEN * 8; // In bits
    transaction.tx_buffer = cmd_tx;
    transaction.rx_buffer = cmd_rx;

    ESP_LOGI(TAG, "Sending command to STM32: ID=0x%02X, Param=0x%02X, Data=0x%08" PRIX32,
             cmd_id, param1, data);

    // Perform SPI transfer
    xSemaphoreTake(xSpiTransferMutex, portMAX_DELAY);
    esp_err_t err = spi_device_transmit(spi_device, &transaction);
    xSemaphoreGive(xSpiTransferMutex);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to send SPI command: %s", esp_err_to_name(err));
    }

    heap_caps_free(cmd_tx);
    heap_caps_free(cmd_rx);
    return err;
}

bool comm_spi_master_get_latest_telemetry(tSpiTxPayload *dest) {
    if (dest == NULL || !latest_telemetry_valid) {
        return false;
    }

    bool success = false;
    if (xSemaphoreTake(xLatestTelemetryMutex, pdMS_TO_TICKS(5)) == pdTRUE) {
        memcpy(dest, latest_telemetry, sizeof(tSpiTxPayload));
        latest_telemetry_valid = false;
        success = true;
        xSemaphoreGive(xLatestTelemetryMutex);
    }
    return success;
}

bool comm_spi_master_queue_pop(tSpiTxPayload *dest, TickType_t timeout) {
    if (dest == NULL || xTelemetryQueue == NULL) {
        return false;
    }
    return (xQueueReceive(xTelemetryQueue, dest, timeout) == pdTRUE);
}
