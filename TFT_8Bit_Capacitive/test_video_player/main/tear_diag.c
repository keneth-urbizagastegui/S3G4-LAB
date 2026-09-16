#include "tear_diag.h"
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <unistd.h>
#include <fcntl.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "sdkconfig.h"

static const char *TAG = "TEAR_DIAG";

#if CONFIG_APP_TEAR_DIAG
static volatile tear_diag_mode_t s_diag_mode = (tear_diag_mode_t)CONFIG_APP_TEAR_DIAG_MODE;
#else
static volatile tear_diag_mode_t s_diag_mode = TEAR_DIAG_OFF;
#endif

tear_diag_mode_t tear_diag_get_mode(void) {
    return s_diag_mode;
}

const char *tear_diag_get_mode_name(tear_diag_mode_t mode) {
    switch (mode) {
        case TEAR_DIAG_MODE_A: return "A (medio fotograma)";
        case TEAR_DIAG_MODE_B: return "B (franja unica)";
        case TEAR_DIAG_MODE_C: return "C (patron rojo/azul)";
        case TEAR_DIAG_OFF:
        default:               return "OFF (normal)";
    }
}

void tear_diag_set_mode(tear_diag_mode_t mode) {
    s_diag_mode = mode;
    ESP_LOGI(TAG, "Modo de diagnostico cambiado a: %s", tear_diag_get_mode_name(mode));
    printf("DIAG_MODE,mode=%s\n", tear_diag_get_mode_name(mode));
    fflush(stdout);
}

static void tear_diag_cmd_task(void *arg) {
    int flags = fcntl(fileno(stdin), F_GETFL);
    fcntl(fileno(stdin), F_SETFL, flags | O_NONBLOCK);

    char line_buf[64];
    int line_len = 0;

    while (1) {
        char ch;
        int n = read(fileno(stdin), &ch, 1);
        if (n > 0) {
            if (ch == '\r' || ch == '\n') {
                if (line_len > 0) {
                    line_buf[line_len] = '\0';
                    if (strcasecmp(line_buf, "DIAG A") == 0 || strcasecmp(line_buf, "A") == 0 || strcmp(line_buf, "1") == 0) {
                        tear_diag_set_mode(TEAR_DIAG_MODE_A);
                    } else if (strcasecmp(line_buf, "DIAG B") == 0 || strcasecmp(line_buf, "B") == 0 || strcmp(line_buf, "2") == 0) {
                        tear_diag_set_mode(TEAR_DIAG_MODE_B);
                    } else if (strcasecmp(line_buf, "DIAG C") == 0 || strcasecmp(line_buf, "C") == 0 || strcmp(line_buf, "3") == 0) {
                        tear_diag_set_mode(TEAR_DIAG_MODE_C);
                    } else if (strcasecmp(line_buf, "DIAG OFF") == 0 || strcasecmp(line_buf, "OFF") == 0 || strcmp(line_buf, "0") == 0) {
                        tear_diag_set_mode(TEAR_DIAG_OFF);
                    } else if (strcasecmp(line_buf, "DIAG ?") == 0 || strcasecmp(line_buf, "DIAG") == 0) {
                        printf("DIAG_MODE,current=%s\n", tear_diag_get_mode_name(s_diag_mode));
                        fflush(stdout);
                    }
                    line_len = 0;
                }
            } else if (line_len < (int)(sizeof(line_buf) - 1)) {
                line_buf[line_len++] = ch;
            }
        } else {
            vTaskDelay(pdMS_TO_TICKS(50));
        }
    }
}

void tear_diag_init(void) {
    ESP_LOGI(TAG, "Inicializando diagnostico de tearing. Modo inicial: %s", tear_diag_get_mode_name(s_diag_mode));
    printf("TEAR_DIAG,mode=%s\n", tear_diag_get_mode_name(s_diag_mode));
    fflush(stdout);

    xTaskCreatePinnedToCore(tear_diag_cmd_task, "tear_diag_cmd", 3072, NULL, 2, NULL, 0);
}
