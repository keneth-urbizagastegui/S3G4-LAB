/*
 * comm_spi.h
 *
 *  Created on: Jun 10, 2026
 *      Author: Keneth / Antigravity
 */

#ifndef COMM_SPI_H_
#define COMM_SPI_H_

#include <stdint.h>
#include "stm32g4xx_hal.h"
#include "scope.h"
#include "wavegen.h"

#define SPI_PACKET_MAGIC      0x55AA
#define SPI_CMD_SYNC          0xAA

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
#define COMM_SPI_TX_LEN       (16 + 4 * COMM_BUFFER_LEN) // 2064 Bytes
#define COMM_SPI_RX_LEN       8                          // 8 Bytes Command

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
 * @brief Structure representing the command received from ESP32-S3.
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

extern tSpiTxPayload spi_tx_payload;
extern tSpiRxCmd spi_rx_cmd;
extern volatile uint8_t spi_cmd_received;

/**
 * @brief Initialize SPI Slave communication and setup DMA transfers.
 * @param hspi Pointer to SPI handle (configured as Slave with DMA).
 */
void comm_spi_init(SPI_HandleTypeDef *hspi);

/**
 * @brief Prepares telemetry data and triggers transmit readiness.
 * @param pScope Pointer to scope structure.
 */
void comm_spi_prepare_data(tScope *pScope);

/**
 * @brief Processes the received SPI command packet.
 * @param pScope Pointer to scope structure.
 * @param pWavegen Pointer to wavegen structure.
 */
void comm_spi_process_cmd(tScope *pScope, tWaveGen *pWavegen);

#endif /* COMM_SPI_H_ */
