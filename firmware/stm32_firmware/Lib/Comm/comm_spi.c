/*
 * comm_spi.c
 *
 *  Created on: Jun 10, 2026
 *      Author: Keneth / Antigravity
 */

#include "comm_spi.h"
#include "tools.h"
#include <string.h>

tSpiTxPayload spi_tx_payload;
tSpiRxCmd spi_rx_cmd;
volatile uint8_t spi_cmd_received = 0;

#define CMD_QUEUE_SIZE 8
static tSpiRxCmd cmd_queue[CMD_QUEUE_SIZE];
static volatile uint8_t cmd_queue_head = 0;
static volatile uint8_t cmd_queue_tail = 0;

static SPI_HandleTypeDef *hspi_comm = NULL;
static volatile uint8_t spi_tx_active = 0;

void comm_spi_init(SPI_HandleTypeDef *hspi) {
    hspi_comm = hspi;
    spi_tx_active = 0;
    spi_cmd_received = 0;

    cmd_queue_head = 0;
    cmd_queue_tail = 0;
    memset(cmd_queue, 0, sizeof(cmd_queue));

    // Set DATA_READY pin (PD2) to low initially
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_RESET);

    // Clear structures
    memset(&spi_tx_payload, 0, sizeof(spi_tx_payload));
    memset(&spi_rx_cmd, 0, sizeof(spi_rx_cmd));

    spi_tx_payload.header.magic_number = SPI_PACKET_MAGIC;

    // Start listening for commands from ESP32-S3
    HAL_SPI_Receive_DMA(hspi_comm, (uint8_t*)&spi_rx_cmd, COMM_SPI_RX_LEN);
}

void comm_spi_prepare_data(tScope *pScope) {
    if (spi_tx_active) {
        // Drop capture if the previous transmission is still in progress
        return;
    }

    // Determine which capture buffers are complete and ready for copy (Ping-Pong buffers)
    uint16_t *buf_ch1 = (pScope->cnt & 0x01) ? pScope->buffer1 : pScope->buffer5;
    uint16_t *buf_ch2 = (pScope->cnt & 0x01) ? pScope->buffer2 : pScope->buffer6;
    uint16_t *buf_ch3 = (pScope->cnt & 0x01) ? pScope->buffer3 : pScope->buffer7;
    uint16_t *buf_ch4 = (pScope->cnt & 0x01) ? pScope->buffer4 : pScope->buffer8;



    // Copy and decimate/scale data to 8-bit resolution for the display.
    // If scale exceeds the ADC hardware limit (2.56 MSPS), perform software zoom-in using linear interpolation.
    float ratio = 1.0f;
    if (pScope->horizontal.scale > 2560) {
        ratio = (float)pScope->horizontal.scale / 2560.0f;
    }

    if (ratio > 1.0f) {
        float start_idx = 256.0f - (256.0f / ratio);
        for (int i = 0; i < COMM_BUFFER_LEN; i++) {
            float idx_f = start_idx + (float)i / ratio;
            int idx = (int)idx_f;
            if (idx < 0) idx = 0;
            if (idx >= COMM_BUFFER_LEN - 1) idx = COMM_BUFFER_LEN - 2;
            
            float frac = idx_f - (float)idx;
            
            if (pScope->vertical.enable1) {
                uint16_t val = (uint16_t)((1.0f - frac) * buf_ch1[idx] + frac * buf_ch1[idx+1]);
                spi_tx_payload.ch1_data[i] = (uint8_t)(val >> 4);
            } else spi_tx_payload.ch1_data[i] = 0;

            if (pScope->vertical.enable2) {
                uint16_t val = (uint16_t)((1.0f - frac) * buf_ch2[idx] + frac * buf_ch2[idx+1]);
                spi_tx_payload.ch2_data[i] = (uint8_t)(val >> 4);
            } else spi_tx_payload.ch2_data[i] = 0;

            if (pScope->vertical.enable3) {
                uint16_t val = (uint16_t)((1.0f - frac) * buf_ch3[idx] + frac * buf_ch3[idx+1]);
                spi_tx_payload.ch3_data[i] = (uint8_t)(val >> 4);
            } else spi_tx_payload.ch3_data[i] = 0;

            if (pScope->vertical.enable4) {
                uint16_t val = (uint16_t)((1.0f - frac) * buf_ch4[idx] + frac * buf_ch4[idx+1]);
                spi_tx_payload.ch4_data[i] = (uint8_t)(val >> 4);
            } else spi_tx_payload.ch4_data[i] = 0;
        }
    } else {
        for (int i = 0; i < COMM_BUFFER_LEN; i++) {
            spi_tx_payload.ch1_data[i] = pScope->vertical.enable1 ? (uint8_t)(buf_ch1[i] >> 4) : 0;
            spi_tx_payload.ch2_data[i] = pScope->vertical.enable2 ? (uint8_t)(buf_ch2[i] >> 4) : 0;
            spi_tx_payload.ch3_data[i] = pScope->vertical.enable3 ? (uint8_t)(buf_ch3[i] >> 4) : 0;
            spi_tx_payload.ch4_data[i] = pScope->vertical.enable4 ? (uint8_t)(buf_ch4[i] >> 4) : 0;
        }
    }

    // Determine the active trigger channel buffer and its vertical scale (gain index)
    uint16_t *trig_buf = buf_ch1;
    uint8_t scale = pScope->vertical.scale1;
    if (pScope->trigger.channel == 1) {
        trig_buf = buf_ch2;
        scale = pScope->vertical.scale2;
    } else if (pScope->trigger.channel == 2) {
        trig_buf = buf_ch3;
        scale = pScope->vertical.scale3;
    } else if (pScope->trigger.channel == 3) {
        trig_buf = buf_ch4;
        scale = pScope->vertical.scale4;
    }

    // Perform signal telemetry calculations on the trigger channel
    uint16_t vmin = get_vmin(trig_buf, pScope->len);
    uint16_t vmax = get_vmax(trig_buf, pScope->len);
    uint16_t vavg = get_vavg(trig_buf, pScope->len);
    uint16_t vrms = get_vrms(trig_buf, pScope->len, vavg);
    float period = get_period(trig_buf, pScope->len, vmax, vmin, vavg);
    uint16_t duty = get_duty(trig_buf, pScope->len, vmax, vmin, vavg);

    // Convert raw ADC counts to physical millivolts (mV) compensating for hardware attenuation.
    // Calibrated with a professional oscilloscope (scale factor corrected from 19620 to 17893 to match Vpp=2.28V).
    // This correction compensates for a real VDDA = 3.01V under USB load and components tolerance.
    // Scaling factor = (3010 * 5.9453) / (2^scale * 4096) = 17893 / 2^(scale + 12)
    uint32_t shift = (uint32_t)scale + 12;
    uint16_t vpp_counts = (vmax > vmin) ? (vmax - vmin) : 0;
    uint16_t vpp_mv = (uint16_t)(((uint32_t)vpp_counts * 17893) >> shift);
    uint16_t vrms_mv = (uint16_t)(((uint32_t)vrms * 17893) >> shift);

    // Average voltage has a DC offset introduced by the 3.3V bias network.
    // Adjusted V_bias_referred to 8947 mV / G and offset to 195 mV.
    int32_t vavg_calc = (int32_t)(((uint32_t)vavg * 17893) >> shift) - (int32_t)(8947 >> scale) - 195;
    if (vavg_calc < 0) vavg_calc = 0;
    uint16_t vavg_mv = (uint16_t)vavg_calc;

    // Calculate signal frequency using the actual physical sampling rate scale.
    uint32_t freq = 0;
    if (period > 0.0f) {
        uint32_t scale_actual = pScope->horizontal.scale;
        if (scale_actual > 2560) {
            scale_actual = 2560;
        }
        freq = (uint32_t)((float)(scale_actual * 1000) / period);
    }

    // Fill telemetry header values
    spi_tx_payload.header.magic_number = SPI_PACKET_MAGIC;
    spi_tx_payload.header.vpp = vpp_mv;
    spi_tx_payload.header.vavg = vavg_mv;
    spi_tx_payload.header.vrms = vrms_mv;
    spi_tx_payload.header.frequency = freq;
    spi_tx_payload.header.duty_cycle = (uint8_t)duty;
    spi_tx_payload.header.gain_state = scale;
    spi_tx_payload.header.ch_active = (pScope->vertical.enable1 ? 1 : 0) |
                                      (pScope->vertical.enable2 ? 2 : 0) |
                                      (pScope->vertical.enable3 ? 4 : 0) |
                                      (pScope->vertical.enable4 ? 8 : 0);
    spi_tx_payload.header.padding = 0;

    // Cancel active SPI command reception to initiate transmission
    HAL_SPI_DMAStop(hspi_comm);

    spi_tx_active = 1;

    // Arm the SPI DMA for telemetry transmission
    HAL_SPI_Transmit_DMA(hspi_comm, (uint8_t*)&spi_tx_payload, COMM_SPI_TX_LEN);

    // Raise DATA_READY pin (PD2) to interrupt the ESP32-S3
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_SET);
}

void comm_spi_process_cmd(tScope *pScope, tWaveGen *pWavegen) {
    while (cmd_queue_tail != cmd_queue_head) {
        tSpiRxCmd cmd = cmd_queue[cmd_queue_tail];
        cmd_queue_tail = (cmd_queue_tail + 1) % CMD_QUEUE_SIZE;

        switch (cmd.cmd_id) {
            case CMD_SCOPE_START: {
                uint8_t continuous = (cmd.param1 != 0);
                scope_start(pScope, continuous);
                break;
            }
            case CMD_SCOPE_STOP:
                scope_stop(pScope);
                break;

            case CMD_SCOPE_CONFIG_HORIZ: {
                uint16_t offset = (cmd.data & 0xFFFF);
                uint16_t scale = ((cmd.data >> 16) & 0xFFFF);
                scope_config_horizontal(pScope, offset, scale);
                break;
            }

            case CMD_SCOPE_CONFIG_VERT: {
                uint8_t ch = cmd.param1;
                uint8_t enable = (cmd.data & 0xFF);
                uint8_t gain = ((cmd.data >> 8) & 0xFF);
                uint16_t offset = ((cmd.data >> 16) & 0xFFFF);

                if (ch == 0) {
                    pScope->vertical.enable1 = enable;
                    pScope->vertical.scale1 = gain;
                    pScope->vertical.offset1 = offset;
                } else if (ch == 1) {
                    pScope->vertical.enable2 = enable;
                    pScope->vertical.scale2 = gain;
                    pScope->vertical.offset2 = offset;
                } else if (ch == 2) {
                    pScope->vertical.enable3 = enable;
                    pScope->vertical.scale3 = gain;
                    pScope->vertical.offset3 = offset;
                } else if (ch == 3) {
                    pScope->vertical.enable4 = enable;
                    pScope->vertical.scale4 = gain;
                    pScope->vertical.offset4 = offset;
                }

                scope_config_vertical(pScope, pScope->vertical.offset,
                                      pScope->vertical.scale1, pScope->vertical.scale2,
                                      pScope->vertical.scale3, pScope->vertical.scale4);
                break;
            }

            case CMD_SCOPE_CONFIG_TRIG: {
                uint8_t ch = cmd.param1;
                uint8_t mode = (cmd.data & 0xFF);
                uint8_t slope = ((cmd.data >> 8) & 0xFF);
                uint16_t level = ((cmd.data >> 16) & 0xFFFF);
                scope_config_trigger(pScope, ch, mode, level, slope);
                break;
            }

            case CMD_WAVEGEN_START:
                wavegen_start(pWavegen, (enum eWaveGenChannel)cmd.param1);
                break;

            case CMD_WAVEGEN_STOP:
                wavegen_stop(pWavegen, (enum eWaveGenChannel)cmd.param1);
                break;

            case CMD_WAVEGEN_CONFIG_HORIZ:
                wavegen_config_horizontal(pWavegen, (enum eWaveGenChannel)cmd.param1, (uint16_t)cmd.data);
                break;

            case CMD_WAVEGEN_CONFIG_VERT: {
                enum eWaveGenChannel ch = (enum eWaveGenChannel)cmd.param1;
                uint8_t ui_type = (cmd.data & 0xFF);
                uint8_t duty_cycle = ((cmd.data >> 8) & 0xFF);
                uint16_t amplitude = ((cmd.data >> 16) & 0xFFFF);

                enum eWaveGenType type = WAVEGEN_TYPE_SINE;
                switch (ui_type) {
                    case 0: type = WAVEGEN_TYPE_SINE; break;
                    case 1: type = WAVEGEN_TYPE_PWM; break;
                    case 2: type = WAVEGEN_TYPE_TRIANGLE; break;
                    case 3: type = WAVEGEN_TYPE_SAWTOOTH; break;
                    case 4: type = WAVEGEN_TYPE_HALFRECT; break; // Pulse maps to Half-Wave Rectified Sine
                    case 5: type = WAVEGEN_TYPE_FULLRECT; break;
                    case 6: type = WAVEGEN_TYPE_SINC; break;
                    case 7: type = WAVEGEN_TYPE_NOISE; break;
                    default: type = WAVEGEN_TYPE_SINE; break;
                }

                // Default offset is 1.25V (1551 counts) to keep the signal between 0V and 2.5V
                wavegen_config_vertical(pWavegen, ch, type, 1551, amplitude, duty_cycle);
                break;
            }

            default:
                break;
        }
    }

    spi_cmd_received = 0;
}

// SPI Callback functions
void HAL_SPI_RxCpltCallback(SPI_HandleTypeDef *hspi) {
    if (hspi == hspi_comm) {
        // Verify Command Checksum
        uint8_t sum = spi_rx_cmd.sync + spi_rx_cmd.cmd_id + spi_rx_cmd.param1 +
                      (spi_rx_cmd.data & 0xFF) + ((spi_rx_cmd.data >> 8) & 0xFF) +
                      ((spi_rx_cmd.data >> 16) & 0xFF) + ((spi_rx_cmd.data >> 24) & 0xFF);

        if (spi_rx_cmd.sync == SPI_CMD_SYNC && sum == spi_rx_cmd.checksum) {
            uint8_t next_head = (cmd_queue_head + 1) % CMD_QUEUE_SIZE;
            if (next_head != cmd_queue_tail) {
                cmd_queue[cmd_queue_head] = spi_rx_cmd;
                cmd_queue_head = next_head;
                spi_cmd_received = 1;
            }
        }
        
        // Re-arm command listening immediately unless we are transmitting telemetry
        if (!spi_tx_active) {
            HAL_SPI_Receive_DMA(hspi_comm, (uint8_t*)&spi_rx_cmd, COMM_SPI_RX_LEN);
        }
    }
}

void HAL_SPI_TxCpltCallback(SPI_HandleTypeDef *hspi) {
    if (hspi == hspi_comm) {
        // Deassert DATA_READY pin (PD2)
        HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_RESET);
        spi_tx_active = 0;

        // Re-arm command listening
        HAL_SPI_Receive_DMA(hspi_comm, (uint8_t*)&spi_rx_cmd, COMM_SPI_RX_LEN);
    }
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi) {
    if (hspi == hspi_comm) {
        spi_tx_active = 0;
        HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_RESET);
        // Force re-arm listening
        HAL_SPI_DMAStop(hspi_comm);
        HAL_SPI_Receive_DMA(hspi_comm, (uint8_t*)&spi_rx_cmd, COMM_SPI_RX_LEN);
    }
}
