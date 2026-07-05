/*
 * tools.c
 *
 *  Created on: Jul 25, 2023
 *      Author: Keneth / Antigravity
 */

#include "tools.h"
#include <stdlib.h>

uint16_t get_vmin( uint16_t *buffer, uint16_t len )
{
    if (len < 3) return buffer[0];
    uint16_t value = 4095;
    for( uint16_t i = 1 ; i < len - 1 ; i++ )
    {
        uint16_t avg = (buffer[i-1] + buffer[i] + buffer[i+1]) / 3;
        if( avg < value )
        {
            value = avg;
        }
    }
    return value;
}

uint16_t get_vmax( uint16_t *buffer, uint16_t len )
{
    if (len < 3) return buffer[0];
    uint16_t value = 0;
    for( uint16_t i = 1 ; i < len - 1 ; i++ )
    {
        uint16_t avg = (buffer[i-1] + buffer[i] + buffer[i+1]) / 3;
        if( avg > value )
        {
            value = avg;
        }
    }
    return value;
}

uint16_t get_vavg( uint16_t *buffer, uint16_t len )
{
    uint16_t i = 0;
    uint32_t value = 0;

    for( i = 0 ; i < len ; i++ )
    {
        value += buffer[i];
    }

    return value/len;
}

float get_period( uint16_t *buffer, uint16_t len, uint16_t mx, uint16_t mn, uint16_t avg )
{
    float t0 = -1.0f;
    float t1 = -1.0f;
    float t2 = -1.0f;
    uint16_t i = 0;

    uint16_t thr1 = mn + 3*(mx - mn)/4;
    uint16_t thr2 = mn + 1*(mx - mn)/4;

    if( abs(mx - mn) < 40 )
    {
        return 0.0f;
    }

    for( i = 0 ; i < len-1 ; i++ )
    {
        if( buffer[i] > thr1 && buffer[i+1] <= thr1 )
        {
            float diff = (float)(buffer[i] - buffer[i+1]);
            t0 = (float)i + (diff > 0.0f ? (float)(buffer[i] - thr1) / diff : 0.0f);
            
            for( i = (uint16_t)t0 + 1 ; i < len-1 ; i++ )
            {
                if( buffer[i] < thr2 && buffer[i+1] >= thr2 )
                {
                    float diff2 = (float)(buffer[i+1] - buffer[i]);
                    t1 = (float)i + (diff2 > 0.0f ? (float)(thr2 - buffer[i]) / diff2 : 0.0f);
                    
                    for( i = (uint16_t)t1 + 1 ; i < len-1 ; i++ )
                    {
                        if( buffer[i] > thr1 && buffer[i+1] <= thr1 )
                        {
                            float diff3 = (float)(buffer[i] - buffer[i+1]);
                            t2 = (float)i + (diff3 > 0.0f ? (float)(buffer[i] - thr1) / diff3 : 0.0f);
                            return t2 - t0;
                        }
                    }
                }
            }
        }
    }

    return 0.0f;
}

uint16_t get_duty( uint16_t *buffer, uint16_t len, uint16_t mx, uint16_t mn, uint16_t avg )
{
    float t0 = -1.0f;
    float t1 = -1.0f;
    float t2 = -1.0f;
    uint16_t i = 0;

    uint16_t thr1 = mn + 3*(mx - mn)/4;
    uint16_t thr2 = mn + 1*(mx - mn)/4;

    if( abs(mx - mn) < 40 )
    {
        return 0;
    }

    for( i = 0 ; i < len-1 ; i++ )
    {
        if( buffer[i] > thr1 && buffer[i+1] <= thr1 )
        {
            float diff = (float)(buffer[i] - buffer[i+1]);
            t0 = (float)i + (diff > 0.0f ? (float)(buffer[i] - thr1) / diff : 0.0f);
            
            for( i = (uint16_t)t0 + 1 ; i < len-1 ; i++ )
            {
                if( buffer[i] < thr2 && buffer[i+1] >= thr2 )
                {
                    float diff2 = (float)(buffer[i+1] - buffer[i]);
                    t1 = (float)i + (diff2 > 0.0f ? (float)(thr2 - buffer[i]) / diff2 : 0.0f);
                    
                    for( i = (uint16_t)t1 + 1 ; i < len-1 ; i++ )
                    {
                        if( buffer[i] > thr1 && buffer[i+1] <= thr1 )
                        {
                            float diff3 = (float)(buffer[i] - buffer[i+1]);
                            t2 = (float)i + (diff3 > 0.0f ? (float)(buffer[i] - thr1) / diff3 : 0.0f);
                            
                            float period = t2 - t0;
                            float pulse = t1 - t0;
                            if (period > 0.0f) {
                                float duty = 100.0f - (100.0f * pulse) / period;
                                if (duty < 0.0f) return 0;
                                if (duty > 100.0f) return 100;
                                return (uint16_t)duty;
                            }
                            return 0;
                        }
                    }
                }
            }
        }
    }

    return 0;
}

static uint32_t int_sqrt(uint32_t x) {
    uint32_t res = 0;
    uint32_t add = 0x8000;
    for (int i = 0; i < 16; i++) {
        uint32_t temp = res | add;
        if (temp * temp <= x) {
            res = temp;
        }
        add >>= 1;
    }
    return res;
}

uint16_t get_vrms( uint16_t *buffer, uint16_t len, uint16_t avg )
{
    uint32_t sum_squares = 0;
    for( uint16_t i = 0 ; i < len ; i++ )
    {
        int32_t val = (int32_t)buffer[i] - (int32_t)avg;
        sum_squares += val * val;
    }
    return (uint16_t)int_sqrt(sum_squares / len);
}
