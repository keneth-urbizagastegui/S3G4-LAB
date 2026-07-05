/*
 * comm_spi_master.h
 *
 *  Created on: Jun 11, 2026
 *      Author: Antigravity
 */

#ifndef COMM_SPI_MASTER_H_
#define COMM_SPI_MASTER_H_

#include <stdint.h>
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define SPI_PACKET_MAGIC      0x55AA
#define SPI_CMD_SYNC          0xAA

// Commands sent from ESP32-S3 to STM32
#define CMD_SCOPE_START       0x01
#define CMD_SCOPE_STOP        0x02
#define CMD_SCOPE_CONFIG_HORIZ 0x03
#define CMD_SCOPE_CONFIG_VERT  0x04
#define CMD_SCOPE_CONFIG_TRIG  0x05

#define CMD_WAVEGEN_START     0x11
#define CMD_WAVEGEN_STOP      0x12
#define CMD_WAVEGEN_CONFIG_HORIZ 0x13
#define CMD_WAVEGEN_CONFIG_VERT  0x14

#define COMM_BUFFER_LEN       512
#define COMM_SPI_TX_LEN       (16 + 4 * COMM_BUFFER_LEN) // 2064 Bytes (Received from STM32)
#define COMM_SPI_RX_LEN       8                          // 8 Bytes Command (Sent to STM32)

// Physical Pin configuration for SPI3 (STM32 connection)
#define STM32_SPI_HOST        SPI3_HOST
#define STM32_PIN_MISO        8
#define STM32_PIN_MOSI        17
#define STM32_PIN_CLK         18
#define STM32_PIN_CS          15
#define STM32_PIN_DRDY        4

#pragma pack(push, 1)

/**
 * @brief Structure representing the telemetry data packet header.
 */
struct sPacketHeader {
    uint16_t magic_number; /**< 0x55AA */
    uint16_t vpp;          /**< Calculated Peak-to-Peak Voltage (in mV) */
    uint16_t vrms;         /**< Calculated RMS Voltage (in mV) */
    uint16_t vavg;         /**< Calculated Average Voltage (in mV) */
    uint32_t frequency;    /**< Calculated Frequency (in Hz) */
    uint8_t duty_cycle;    /**< Calculated Duty Cycle (0 - 100%) */
    uint8_t gain_state;    /**< Current gain state index of PGA */
    uint8_t ch_active;     /**< Bit 0: CH1, Bit 1: CH2, Bit 2: CH3, Bit 3: CH4 */
    uint8_t padding;       /**< Padding for 32-bit alignment */
};
typedef struct sPacketHeader tPacketHeader;

/**
 * @brief Structure representing the full SPI transmission data payload.
 */
struct sSpiTxPayload {
    tPacketHeader header;
    uint8_t ch1_data[COMM_BUFFER_LEN];
    uint8_t ch2_data[COMM_BUFFER_LEN];
    uint8_t ch3_data[COMM_BUFFER_LEN];
    uint8_t ch4_data[COMM_BUFFER_LEN];
};
typedef struct sSpiTxPayload tSpiTxPayload;

/**
 * @brief Structure representing the command sent to STM32.
 */
struct sSpiRxCmd {
    uint8_t sync;      /**< Should be 0xAA */
    uint8_t cmd_id;    /**< Command ID */
    uint8_t param1;    /**< Parameter 1 (Channel, etc.) */
    uint32_t data;     /**< 32-bit data payload */
    uint8_t checksum;  /**< Checksum = sum(sync to data) */
};
typedef struct sSpiRxCmd tSpiRxCmd;

#pragma pack(pop)

/**
 * @brief Initializes the SPI Master driver and the DATA_READY GPIO interrupt.
 * @return esp_err_t ESP_OK on success, or error code.
 */
esp_err_t comm_spi_master_init(void);

/**
 * @brief Sends an 8-byte command packet to the STM32 co-processor.
 * @param cmd_id The command identifier.
 * @param param1 The parameter byte.
 * @param data The 32-bit data payload.
 * @return esp_err_t ESP_OK on success, or error code.
 */
esp_err_t comm_spi_master_send_cmd(uint8_t cmd_id, uint8_t param1, uint32_t data);

/**
 * @brief Gets the latest telemetry frame read from the STM32 co-processor.
 * @param dest Pointer to destination payload structure.
 * @return bool True if copy was successful and data is valid, false otherwise.
 */
bool comm_spi_master_get_latest_telemetry(tSpiTxPayload *dest);

/**
 * @brief Wait and dequeue a telemetry frame. Useful for streaming tasks (WebSockets).
 * @param dest Pointer to destination payload structure.
 * @param timeout TickType_t timeout.
 * @return bool True if a frame was successfully read within the timeout.
 */
bool comm_spi_master_queue_pop(tSpiTxPayload *dest, TickType_t timeout);

#endif /* COMM_SPI_MASTER_H_ */
