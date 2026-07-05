/*
 * wavegen.h
 *
 *  Created on: Jul 31, 2023
 *      Author: Keneth / Antigravity
 */

#ifndef WAVEGEN_H_
#define WAVEGEN_H_

#include <stdint.h>
#include "stm32g4xx_hal.h"

/**
 * @brief Enumeration of WaveGen channels.
 */
enum eWaveGenChannel
{
    WAVEGEN_CHANNEL_1, /**< WaveGen Channel 1 (DAC1_OUT1) */
    WAVEGEN_CHANNEL_2  /**< WaveGen Channel 2 (DAC1_OUT2) */
};

/**
 * @brief Enumeration of WaveGen waveform types.
 */
enum eWaveGenType
{
    WAVEGEN_TYPE_DC,       /**< DC waveform */
    WAVEGEN_TYPE_SINE,     /**< Sine waveform */
    WAVEGEN_TYPE_SQUARE,   /**< Square waveform */
    WAVEGEN_TYPE_TRIANGLE, /**< Triangle waveform */
    WAVEGEN_TYPE_SAWTOOTH, /**< Sawtooth waveform */
    WAVEGEN_TYPE_PWM,      /**< PWM waveform */
    WAVEGEN_TYPE_NOISE,    /**< Noise waveform */
    WAVEGEN_TYPE_FULLRECT, /**< Full-rectified sine waveform */
    WAVEGEN_TYPE_SINC,     /**< Sinc waveform */
    WAVEGEN_TYPE_HALFRECT, /**< Half-rectified sine waveform */
    WAVEGEN_TYPE_MAX       /**< Maximum waveform type value */
};

/**
 * @brief Structure to hold WaveGen configuration.
 */
struct sWaveGen
{
    DAC_HandleTypeDef *hdac;   /**< DAC handle */
    TIM_HandleTypeDef *htim1;  /**< TIM4 handle for channel 1 */
    TIM_HandleTypeDef *htim2;  /**< TIM6 handle for channel 2 */

    uint16_t *buffer1;         /**< Waveform buffer for channel 1 */
    uint16_t *buffer2;         /**< Waveform buffer for channel 2 */
    uint16_t len;              /**< Buffer length */
};
typedef struct sWaveGen tWaveGen;

/**
 * @brief Initialize the WaveGen module at a low level.
 */
void wavegen_init_ll(tWaveGen *pThis, DAC_HandleTypeDef *hdac, TIM_HandleTypeDef *htim1, TIM_HandleTypeDef *htim2);

/**
 * @brief Initialize the WaveGen module.
 */
void wavegen_init(tWaveGen *pThis, uint16_t *buffer1, uint16_t *buffer2, uint16_t len);

/**
 * @brief Start waveform generation on a specific channel.
 */
void wavegen_start(tWaveGen *pThis, enum eWaveGenChannel channel);

/**
 * @brief Stop waveform generation on a specific channel.
 */
void wavegen_stop(tWaveGen *pThis, enum eWaveGenChannel channel);

/**
 * @brief Configure horizontal parameters (frequency) for a specific channel.
 */
void wavegen_config_horizontal(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t frequency);

/**
 * @brief Configure vertical parameters (type, offset, scale, duty cycle) for a specific channel.
 */
void wavegen_config_vertical(tWaveGen *pThis, enum eWaveGenChannel channel, enum eWaveGenType type, uint16_t offset, uint16_t scale, uint16_t duty_cycle);

/**
 * @brief Build a DC waveform on a specific channel.
 */
void wavegen_build_dc(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset);

/**
 * @brief Build a sine waveform on a specific channel.
 */
void wavegen_build_sine(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a square waveform on a specific channel.
 */
void wavegen_build_square(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a triangle waveform on a specific channel.
 */
void wavegen_build_triangle(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a sawtooth waveform on a specific channel.
 */
void wavegen_build_sawtooth(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a PWM waveform on a specific channel.
 */
void wavegen_build_pwm(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale, uint16_t duty_cycle);

/**
 * @brief Build a noise waveform on a specific channel.
 */
void wavegen_build_noise(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a full-rectified sine waveform on a specific channel.
 */
void wavegen_build_full_rect(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a sinc waveform on a specific channel.
 */
void wavegen_build_sinc(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

/**
 * @brief Build a half-rectified sine waveform on a specific channel.
 */
void wavegen_build_half_rect(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale);

#endif /* WAVEGEN_H_ */
