#ifndef SDCARD_SPI_H
#define SDCARD_SPI_H

#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// Pines asignados para MicroSD en modo SPI
#define SD_PIN_CS    21
#define SD_PIN_MOSI  11
#define SD_PIN_CLK   13
#define SD_PIN_MISO  15

#define SD_MOUNT_POINT "/sdcard"

esp_err_t sdcard_spi_init(void);
bool sdcard_is_mounted(void);
void sdcard_spi_deinit(void);
void sdcard_list_files(const char *dirpath);

#ifdef __cplusplus
}
#endif

#endif // SDCARD_SPI_H
