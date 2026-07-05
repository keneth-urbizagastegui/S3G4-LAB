/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dac.h"
#include "dma.h"
#include "opamp.h"
#include "spi.h"
#include "tim.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "scope.h"
#include "wavegen.h"
#include "comm_spi.h"
#include "stm32g4xx_ll_adc.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
#define ADC_BUFFER_LEN (512)
uint16_t buffer1[ADC_BUFFER_LEN];
uint16_t buffer2[ADC_BUFFER_LEN];
uint16_t buffer3[ADC_BUFFER_LEN];
uint16_t buffer4[ADC_BUFFER_LEN];
uint16_t buffer5[ADC_BUFFER_LEN];
uint16_t buffer6[ADC_BUFFER_LEN];
uint16_t buffer7[ADC_BUFFER_LEN];
uint16_t buffer8[ADC_BUFFER_LEN];

#define DAC_BUFFER_LEN (512)
uint16_t dac1_buffer[DAC_BUFFER_LEN];
uint16_t dac2_buffer[DAC_BUFFER_LEN];

tScope scope;
tWaveGen wavegen;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static void scope_force_trigger(tScope *pThis) {
    if (pThis->state == SCOPE_STATE_WAIT_FOR_CONVERSION_COMPLETE ||
        pThis->state == SCOPE_STATE_WAIT_FOR_ARM ||
        pThis->state == SCOPE_STATE_WAIT_FOR_TRIGGER) {
        
        // Clear relevant TIM interrupts and flags
        __HAL_TIM_CLEAR_IT(pThis->horizontal.htim_stop, TIM_IT_CC1);
        __HAL_TIM_CLEAR_IT(pThis->horizontal.htim_stop, TIM_IT_CC2);
        __HAL_TIM_CLEAR_IT(pThis->horizontal.htim_stop, TIM_IT_UPDATE);
        __HAL_TIM_CLEAR_FLAG(pThis->horizontal.htim_stop, TIM_FLAG_CC1);
        __HAL_TIM_CLEAR_FLAG(pThis->horizontal.htim_stop, TIM_FLAG_CC2);
        __HAL_TIM_CLEAR_FLAG(pThis->horizontal.htim_stop, TIM_FLAG_UPDATE);

        // Start the horizontal timer for triggering
        HAL_TIM_Base_Start(pThis->horizontal.htim_stop);
        HAL_TIM_OnePulse_Start_IT(pThis->horizontal.htim_stop, TIM_CHANNEL_1);

        // Disable ADC analog watchdogs
        LL_ADC_DisableIT_AWD1(pThis->trigger.hadc1->Instance);
        LL_ADC_DisableIT_AWD2(pThis->trigger.hadc1->Instance);

        // Transition the scope state to waiting for stop
        pThis->state = SCOPE_STATE_WAIT_FOR_STOP;
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_ADC1_Init();
  MX_OPAMP1_Init();
  MX_OPAMP3_Init();
  MX_OPAMP5_Init();
  MX_OPAMP6_Init();
  MX_ADC3_Init();
  MX_ADC4_Init();
  MX_ADC5_Init();
  MX_SPI3_Init();
  MX_DAC1_Init();
  MX_TIM2_Init();
  MX_TIM3_Init();
  MX_DAC2_Init();
  MX_TIM4_Init();
  MX_TIM6_Init();
  /* USER CODE BEGIN 2 */
  pScope = &scope;

  // Initialize scope library and link hardware drivers
  scope_init_ll(&scope,
      &htim2,   // clock timer
      &htim3,   // stop timer (one-pulse)
      &hdac2,   // offset DAC (DAC2_OUT1)
      &hopamp1, // PGA Channel 1
      &hopamp3, // PGA Channel 2
      &hopamp5, // PGA Channel 3
      &hopamp6, // PGA Channel 4
      &hadc1,   // ADC Channel 1 (VOPAMP1)
      &hadc3,   // ADC Channel 2 (VOPAMP3)
      &hadc5,   // ADC Channel 3 (VOPAMP5)
      &hadc4    // ADC Channel 4 (VOPAMP6)
  );

  // Bind memory buffers for double-buffering
  scope_init(&scope,
      buffer1, buffer2, buffer3, buffer4,
      buffer5, buffer6, buffer7, buffer8,
      ADC_BUFFER_LEN
  );

  // Set default configurations
  scope_config_horizontal(&scope, 0, 100); // offset = 0, scale = 100kHz
  scope_config_vertical(&scope, 2048, 0, 0, 0, 0); // offset = 1.65V, all gains to x2 (index 0)
  
  scope.vertical.enable1 = 1;
  scope.vertical.scale1 = 0; // gain index 0
  scope.vertical.offset1 = 192; // display midpoint
  
  scope_config_trigger(&scope, 0, 0, 2048, 0); // CH1, Auto mode, level 2048, Rising edge

  // Initialize wave generator (DDS)
  wavegen_init_ll(&wavegen, &hdac1, &htim4, &htim6);
  wavegen_init(&wavegen, dac1_buffer, dac2_buffer, DAC_BUFFER_LEN);
  
  wavegen_config_horizontal(&wavegen, WAVEGEN_CHANNEL_1, 1000); // 1 kHz
  wavegen_config_vertical(&wavegen, WAVEGEN_CHANNEL_1, WAVEGEN_TYPE_SINE, 1551, 1551, 0);
  wavegen_config_horizontal(&wavegen, WAVEGEN_CHANNEL_2, 1000); // 1 kHz
  wavegen_config_vertical(&wavegen, WAVEGEN_CHANNEL_2, WAVEGEN_TYPE_SINE, 1551, 1551, 0);

  // Initialize SPI Slave communication with ESP32-S3
  comm_spi_init(&hspi3);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  tScopeState prev_state = SCOPE_STATE_IDLE;
  uint32_t capture_start_tick = 0;

  while (1)
  {
      // Process commands received from ESP32-S3
      comm_spi_process_cmd(&scope, &wavegen);

      // Detect start of capture to record timestamp
      if (scope.state != SCOPE_STATE_IDLE && prev_state == SCOPE_STATE_IDLE) {
          capture_start_tick = HAL_GetTick();
      }
      prev_state = scope.state;

      // Auto trigger timeout (100 ms)
      if (scope.trigger.mode == 0) { // AUTO Mode
          if (scope.state == SCOPE_STATE_WAIT_FOR_CONVERSION_COMPLETE ||
              scope.state == SCOPE_STATE_WAIT_FOR_ARM ||
              scope.state == SCOPE_STATE_WAIT_FOR_TRIGGER) {
              if (HAL_GetTick() - capture_start_tick > 100) {
                  scope_force_trigger(&scope);
              }
          }
      }

      // If scope is in continuous mode and idle, trigger next capture
      if (scope_is_continuous(&scope) && scope.state == SCOPE_STATE_IDLE) {
          scope_start(&scope, scope.continuous);
      }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV4;
  RCC_OscInitStruct.PLL.PLLN = 85;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
