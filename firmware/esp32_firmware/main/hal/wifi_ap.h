/*
 * wifi_ap.h
 *
 *  Created on: Jun 11, 2026
 *      Author: Antigravity
 */

#ifndef WIFI_AP_H_
#define WIFI_AP_H_

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "comm_spi_master.h"

// Max APs to scan
#define MAX_SCANNED_APS 15

typedef struct {
    char ssid[33];
    int rssi;
    int authmode;
} wifi_scan_result_t;

/**
 * @brief Initializes the Wi-Fi in STA mode and prepares for connection.
 * @return esp_err_t ESP_OK on success, or error code.
 */
esp_err_t wifi_ap_init(void);

/**
 * @brief Broadcasts telemetry data to all connected WebSocket clients.
 * @param payload Pointer to the telemetry payload.
 */
void wifi_ap_broadcast_telemetry(const tSpiTxPayload *payload);

// STA functions
void wifi_sta_start_scan(void);
bool wifi_sta_is_scan_done(void);
int wifi_sta_get_scan_results(wifi_scan_result_t *results, int max_results);

esp_err_t wifi_sta_connect(const char* ssid, const char* password);
void wifi_sta_disconnect(void);
bool wifi_sta_is_connected(void);
void wifi_sta_get_ip(char *ip_buf, size_t buf_len);
void wifi_sta_get_ssid(char *ssid_buf, size_t buf_len);
void wifi_sta_set_power(bool power);
bool wifi_sta_get_power(void);

// Web Server controls
esp_err_t webserver_start(void);
void webserver_stop(void);
bool webserver_is_running(void);

#endif /* WIFI_AP_H_ */
