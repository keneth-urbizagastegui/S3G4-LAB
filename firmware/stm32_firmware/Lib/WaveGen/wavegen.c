/*
 * wavegen.c
 *
 *  Created on: Jul 31, 2023
 *      Author: Keneth / Antigravity
 */

#include <math.h>
#include <stdlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

#include "wavegen.h"

#define DAC_BUFFER_LEN 	(512)

/**
  * @brief  Initializes the WaveGen structure at a low-level.
  * @param  pThis: Pointer to the WaveGen structure.
  * @param  hdac: DAC handle.
  * @param  htim1: TIM4 handle (drives DAC1_CH1).
  * @param  htim2: TIM6 handle (drives DAC1_CH2).
  * @retval None
  */
void wavegen_init_ll(tWaveGen *pThis, DAC_HandleTypeDef *hdac, TIM_HandleTypeDef *htim1, TIM_HandleTypeDef *htim2)
{
    pThis->hdac = hdac;
    pThis->htim1 = htim1;
    pThis->htim2 = htim2;
}

/**
  * @brief  Initializes the WaveGen structure.
  * @param  pThis: Pointer to the WaveGen structure.
  * @param  buffer1: Pointer to the first DAC buffer.
  * @param  buffer2: Pointer to the second DAC buffer.
  * @param  len: Length of the buffers.
  * @retval None
  */
void wavegen_init(tWaveGen *pThis, uint16_t *buffer1, uint16_t *buffer2, uint16_t len)
{
    pThis->buffer1 = buffer1;
    pThis->buffer2 = buffer2;
    pThis->len = len;
}

/**
  * @brief  Starts the waveform generation for the specified channel.
  * @param  pThis: Pointer to the WaveGen structure.
  * @param  channel: WaveGen channel (CHANNEL_1 or CHANNEL_2).
  * @retval None
  */
void wavegen_start(tWaveGen *pThis, enum eWaveGenChannel channel)
{
    if (channel == WAVEGEN_CHANNEL_1)
    {
        HAL_DAC_Stop_DMA(pThis->hdac, DAC_CHANNEL_1);
        HAL_TIM_Base_Stop(pThis->htim1);
        HAL_DAC_Start_DMA(pThis->hdac, DAC_CHANNEL_1, (uint32_t *)pThis->buffer1, pThis->len, DAC_ALIGN_12B_R);
        HAL_TIM_Base_Start(pThis->htim1);
    }
    else if (channel == WAVEGEN_CHANNEL_2)
    {
        HAL_DAC_Stop_DMA(pThis->hdac, DAC_CHANNEL_2);
        HAL_TIM_Base_Stop(pThis->htim2);
        HAL_DAC_Start_DMA(pThis->hdac, DAC_CHANNEL_2, (uint32_t *)pThis->buffer2, pThis->len, DAC_ALIGN_12B_R);
        HAL_TIM_Base_Start(pThis->htim2);
    }
}

/**
  * @brief  Stops the waveform generation for the specified channel.
  * @param  pThis: Pointer to the WaveGen structure.
  * @param  channel: WaveGen channel (CHANNEL_1 or CHANNEL_2).
  * @retval None
  */
void wavegen_stop(tWaveGen *pThis, enum eWaveGenChannel channel)
{
    if (channel == WAVEGEN_CHANNEL_1)
    {
        HAL_DAC_Stop_DMA(pThis->hdac, DAC_CHANNEL_1);
        HAL_TIM_Base_Stop(pThis->htim1);
    }
    else if (channel == WAVEGEN_CHANNEL_2)
    {
        HAL_DAC_Stop_DMA(pThis->hdac, DAC_CHANNEL_2);
        HAL_TIM_Base_Stop(pThis->htim2);
    }
}

/**
  * @brief  Configures the horizontal parameters (frequency) of the waveform.
  * @param  pThis: Pointer to the WaveGen structure.
  * @param  channel: WaveGen channel (CHANNEL_1 or CHANNEL_2).
  * @param  frequency: Waveform frequency (in Hz).
  * @retval None
  */
void wavegen_config_horizontal(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t frequency)
{
    if (frequency == 0)
    {
        frequency = 1;
    }

    // Dynamic length selection to maximize frequency accuracy and support up to 250 kHz
    uint16_t len = 512;
    if (frequency >= 100000)     // >= 100 kHz
    {
        len = 16;
    }
    else if (frequency >= 20000) // 20 kHz - 100 kHz
    {
        len = 32;
    }
    else if (frequency >= 5000)  // 5 kHz - 20 kHz
    {
        len = 128;
    }
    else if (frequency >= 1000)  // 1 kHz - 5 kHz
    {
        len = 256;
    }
    else                         // < 1 kHz
    {
        len = 512;
    }

    pThis->len = len;

    // Optimal timer prescaler and period calculation to minimize frequency error
    uint32_t total_div = (uint32_t)(170000000.0f / ((uint32_t)frequency * pThis->len) + 0.5f);
    if (total_div == 0)
    {
        total_div = 1;
    }

    uint32_t prescaler = 0;
    uint32_t period = 0;
    if (total_div <= 65536)
    {
        prescaler = 0;
        period = total_div - 1;
    }
    else
    {
        prescaler = (total_div + 65535) / 65536 - 1;
        period = (total_div / (prescaler + 1)) - 1;
    }

    if (channel == WAVEGEN_CHANNEL_1)
    {
        pThis->htim1->Init.Prescaler = prescaler;
        pThis->htim1->Init.Period = period;
        HAL_TIM_Base_Init(pThis->htim1);
    }
    else if (channel == WAVEGEN_CHANNEL_2)
    {
        pThis->htim2->Init.Prescaler = prescaler;
        pThis->htim2->Init.Period = period;
        HAL_TIM_Base_Init(pThis->htim2);
    }
}

/**
  * @brief  Configures the vertical parameters of the waveform.
  */
void wavegen_config_vertical(tWaveGen *pThis, enum eWaveGenChannel channel, enum eWaveGenType type, uint16_t offset, uint16_t scale, uint16_t duty_cycle)
{
    switch (type)
    {
    case WAVEGEN_TYPE_DC:
        wavegen_build_dc(pThis, channel, offset);
        break;
    case WAVEGEN_TYPE_SINE:
        wavegen_build_sine(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_SQUARE:
        wavegen_build_square(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_TRIANGLE:
        wavegen_build_triangle(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_SAWTOOTH:
        wavegen_build_sawtooth(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_PWM:
        wavegen_build_pwm(pThis, channel, offset, scale, duty_cycle);
        break;
    case WAVEGEN_TYPE_NOISE:
        wavegen_build_noise(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_FULLRECT:
        wavegen_build_full_rect(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_SINC:
        wavegen_build_sinc(pThis, channel, offset, scale);
        break;
    case WAVEGEN_TYPE_HALFRECT:
        wavegen_build_half_rect(pThis, channel, offset, scale);
        break;
    default:
        break;
    }
}

/**
  * @brief  Generates a DC waveform with the specified offset.
  */
void wavegen_build_dc(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = offset;
    }
}

/**
  * @brief  Generates a sine waveform with the specified offset and scale.
  */
void wavegen_build_sine(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = sinf(2 * M_PI * i / pThis->len) * scale + offset;
    }
}

/**
  * @brief  Generates a square waveform with the specified offset and scale.
  */
void wavegen_build_square(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = (i < pThis->len / 2) ? offset + scale : offset - scale;
    }
}

/**
  * @brief  Generates a triangle waveform with the specified offset and scale.
  */
void wavegen_build_triangle(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        if (i < pThis->len / 2)
        {
            buffer[i] = offset - scale + (uint16_t)(((float)i / (pThis->len / 2)) * (2 * scale));
        }
        else
        {
            buffer[i] = offset + scale - (uint16_t)(((float)(i - pThis->len / 2) / (pThis->len / 2)) * (2 * scale));
        }
    }
}

/**
  * @brief  Generates a sawtooth waveform with the specified offset and scale.
  */
void wavegen_build_sawtooth(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = offset - scale + i * 2 * scale / pThis->len;
    }
}

/**
  * @brief  Generates a PWM waveform with the specified offset, scale, and duty cycle.
  */
void wavegen_build_pwm(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale, uint16_t duty_cycle)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = (i < pThis->len * duty_cycle / 100) ? offset + scale : offset - scale;
    }
}

/**
  * @brief  Generates a noise waveform with the specified offset and scale.
  */
void wavegen_build_noise(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = rand() % scale + offset;
    }
}

/**
  * @brief  Generates a full-wave rectified sine waveform.
  */
void wavegen_build_full_rect(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        buffer[i] = fabsf(sinf(M_PI * i / pThis->len)) * scale * 2 + offset - scale;
    }
}

/**
  * @brief  Generates a sinc waveform.
  */
void wavegen_build_sinc(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        float x = (float)(i - pThis->len / 2) / (pThis->len / 2) * (4.0f * M_PI);
        float val = (x == 0.0f) ? 1.0f : sinf(x) / x;
        buffer[i] = val * scale + offset;
    }
}

/**
  * @brief  Generates a half-wave rectified sine waveform.
  */
void wavegen_build_half_rect(tWaveGen *pThis, enum eWaveGenChannel channel, uint16_t offset, uint16_t scale)
{
    uint16_t i;
    uint16_t *buffer = (channel == WAVEGEN_CHANNEL_1) ? pThis->buffer1 : pThis->buffer2;
    for (i = 0; i < pThis->len; i++)
    {
        if (i < pThis->len / 2)
        {
            buffer[i] = sinf(2.0f * M_PI * i / pThis->len) * scale * 2 + offset - scale;
        }
        else
        {
            buffer[i] = offset - scale;
        }
    }
}
