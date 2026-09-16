#include "sdcard_spi.h"
#include <stdio.h>
#include <string.h>
#include <sys/unistd.h>
#include <sys/stat.h>
#include <dirent.h>
#include "esp_vfs_fat.h"
#include "sdmmc_cmd.h"
#include "driver/sdspi_host.h"
#include "driver/spi_common.h"
#include "esp_log.h"

static const char *TAG = "SDCARD_SPI";

#include "sdkconfig.h"

static sdmmc_card_t *s_card = NULL;
static bool s_is_mounted = false;
static sdmmc_host_t s_host = SDSPI_HOST_DEFAULT();

#ifndef CONFIG_APP_SD_FREQ_KHZ
#define CONFIG_APP_SD_FREQ_KHZ 20000
#endif

static int s_sd_freq_khz = CONFIG_APP_SD_FREQ_KHZ;

void sdcard_spi_set_freq_khz(int freq_khz) {
    s_sd_freq_khz = freq_khz;
}

int sdcard_spi_get_freq_khz(void) {
    return s_sd_freq_khz;
}

esp_err_t sdcard_spi_init(void) {
    if (s_is_mounted) {
        ESP_LOGI(TAG, "Tarjeta ya montada en %s", SD_MOUNT_POINT);
        return ESP_OK;
    }

    ESP_LOGI(TAG, "Iniciando montaje MicroSD SPI (CS:%d, MOSI:%d, CLK:%d, MISO:%d) @ %d kHz...",
             SD_PIN_CS, SD_PIN_MOSI, SD_PIN_CLK, SD_PIN_MISO, s_sd_freq_khz);

    esp_vfs_fat_sdmmc_mount_config_t mount_config = {
        .format_if_mount_failed = false,
        .max_files = 5,
        .allocation_unit_size = 16 * 1024
    };

    spi_bus_config_t bus_cfg = {
        .mosi_io_num = SD_PIN_MOSI,
        .miso_io_num = SD_PIN_MISO,
        .sclk_io_num = SD_PIN_CLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 65536,
    };

    s_host.slot = SPI2_HOST;
    s_host.max_freq_khz = s_sd_freq_khz;

    esp_err_t ret = spi_bus_initialize(s_host.slot, &bus_cfg, SDSPI_DEFAULT_DMA);
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "Error inicializando bus SPI: %s", esp_err_to_name(ret));
        return ret;
    }

    sdspi_device_config_t slot_config = SDSPI_DEVICE_CONFIG_DEFAULT();
    slot_config.gpio_cs = SD_PIN_CS;
    slot_config.host_id = s_host.slot;

    ret = esp_vfs_fat_sdspi_mount(SD_MOUNT_POINT, &s_host, &slot_config, &mount_config, &s_card);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al montar sistema de archivos FATFS: %s", esp_err_to_name(ret));
        spi_bus_free(s_host.slot);
        return ret;
    }

    s_is_mounted = true;
    ESP_LOGI(TAG, "MicroSD montada con éxito en %s (%d kHz)", SD_MOUNT_POINT, s_sd_freq_khz);
    sdmmc_card_print_info(stdout, s_card);

    sdcard_list_files(SD_MOUNT_POINT);
    return ESP_OK;
}

bool sdcard_is_mounted(void) {
    return s_is_mounted;
}

void sdcard_spi_deinit(void) {
    if (!s_is_mounted) return;
    esp_vfs_fat_sdcard_unmount(SD_MOUNT_POINT, s_card);
    spi_bus_free(s_host.slot);
    s_card = NULL;
    s_is_mounted = false;
    ESP_LOGI(TAG, "MicroSD desmontada.");
}

int sdcard_spi_test_mount_cycles(int cycles, int freq_khz) {
    int successful = 0;
    ESP_LOGI(TAG, "--- Iniciando prueba de %d ciclos de montaje a %d kHz ---", cycles, freq_khz);
    for (int i = 0; i < cycles; i++) {
        sdcard_spi_deinit();
        vTaskDelay(pdMS_TO_TICKS(50));
        s_sd_freq_khz = freq_khz;
        esp_err_t err = sdcard_spi_init();
        if (err == ESP_OK) {
            FILE *tf = fopen("/sdcard/ariana.avi", "rb");
            if (tf) {
                uint8_t dummy[512];
                if (fread(dummy, 1, sizeof(dummy), tf) == sizeof(dummy)) {
                    successful++;
                }
                fclose(tf);
            }
        }
        ESP_LOGI(TAG, "Ciclo %d/%d: %s", i + 1, cycles, (successful == i + 1) ? "OK" : "FALLO");
    }
    ESP_LOGI(TAG, "Prueba montaje: %d/%d ciclos exitosos a %d kHz", successful, cycles, freq_khz);
    return successful;
}

void sdcard_list_files(const char *dirpath) {
    DIR *dir = opendir(dirpath);
    if (!dir) {
        ESP_LOGW(TAG, "No se pudo abrir directorio %s", dirpath);
        return;
    }
    ESP_LOGI(TAG, "--- Contenido del directorio %s ---", dirpath);
    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        char fullpath[300];
        snprintf(fullpath, sizeof(fullpath), "%s/%s", dirpath, entry->d_name);
        struct stat st;
        if (stat(fullpath, &st) == 0) {
            ESP_LOGI(TAG, "  [%c] %s (%ld bytes)",
                     S_ISDIR(st.st_mode) ? 'D' : 'F',
                     entry->d_name, (long)st.st_size);
        } else {
            ESP_LOGI(TAG, "  [?] %s", entry->d_name);
        }
    }
    closedir(dir);
    ESP_LOGI(TAG, "---------------------------------------------");
}
