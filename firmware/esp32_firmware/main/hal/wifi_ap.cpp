/*
 * wifi_ap.cpp
 *
 *  Created on: Jun 11, 2026
 *      Author: Antigravity
 */

#include "wifi_ap.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_http_server.h"
#include "esp_spiffs.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include <string.h>
#include <sys/param.h>
#include <unistd.h>

static const char *TAG = "wifi_sta";
static httpd_handle_t server_handle = NULL;

// WebSocket client management
#define MAX_WS_CLIENTS 8
static int ws_clients[MAX_WS_CLIENTS] = {0};
static SemaphoreHandle_t ws_clients_mutex = NULL;

static bool scan_done = false;
static wifi_ap_record_t ap_records[MAX_SCANNED_APS];
static uint16_t ap_count = 0;
static bool wifi_power_state = true;

static void add_ws_client(int fd) {
    if (ws_clients_mutex == NULL) return;
    xSemaphoreTake(ws_clients_mutex, portMAX_DELAY);
    for (int i = 0; i < MAX_WS_CLIENTS; i++) {
        if (ws_clients[i] == 0) {
            ws_clients[i] = fd;
            ESP_LOGI(TAG, "Added WebSocket client FD: %d", fd);
            break;
        }
    }
    xSemaphoreGive(ws_clients_mutex);
}

static void remove_ws_client(int fd) {
    if (ws_clients_mutex == NULL) return;
    xSemaphoreTake(ws_clients_mutex, portMAX_DELAY);
    for (int i = 0; i < MAX_WS_CLIENTS; i++) {
        if (ws_clients[i] == fd) {
            ws_clients[i] = 0;
            ESP_LOGI(TAG, "Removed WebSocket client FD: %d", fd);
            break;
        }
    }
    xSemaphoreGive(ws_clients_mutex);
}

// Custom socket close callback to self-clean disconnects
static void socket_close_callback(httpd_handle_t hd, int sockfd) {
    remove_ws_client(sockfd);
}

// Embedded Diagnostic Dashboard HTML code (Premium aesthetics)
static const char* diagnostic_html = 
R"html(<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>S3G4_SCOPE | Diagnostic Portal</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --panel-bg: rgba(22, 27, 34, 0.8);
            --border-color: #30363d;
            --text-color: #c9d1d9;
            --accent-cyan: #00eeff;
            --accent-yellow: #ffb700;
            --accent-green: #3fb950;
            --accent-magenta: #ff007f;
            --accent-white: #ffffff;
            --grid-line: #21262d;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 1000px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--accent-cyan);
            padding-bottom: 10px;
        }
        h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(0, 238, 255, 0.5);
        }
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            background-color: #8b0000;
            color: #ffffff;
            border: 1px solid red;
            box-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
        }
        .status-badge.connected {
            background-color: #123512;
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
            box-shadow: 0 0 5px rgba(63, 185, 80, 0.5);
        }
        .dashboard {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        @media(max-width: 800px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
        }
        .panel {
            background-color: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
        }
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: #8b949e;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-left: 3px solid var(--accent-cyan);
            padding-left: 8px;
        }
        .telemetry-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .telemetry-card {
            background-color: rgba(13, 17, 23, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .telemetry-label {
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
        }
        .telemetry-value {
            font-size: 20px;
            font-weight: bold;
            margin-top: 5px;
            font-family: monospace;
        }
        canvas {
            width: 100%;
            height: 380px;
            background-color: #07090e;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            display: block;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            background-color: #21262d;
            border: 1px solid var(--border-color);
            color: #c9d1d9;
            padding: 10px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }
        .btn:hover {
            background-color: #30363d;
            border-color: #8b949e;
            color: #ffffff;
        }
        .btn-primary {
            background-color: #238636;
            border-color: #2ea44f;
            color: #ffffff;
        }
        .btn-primary:hover {
            background-color: #2ea44f;
            box-shadow: 0 0 8px rgba(46, 164, 79, 0.4);
        }
        .btn-danger {
            background-color: #da3637;
            border-color: #f85149;
            color: #ffffff;
        }
        .btn-danger:hover {
            background-color: #f85149;
            box-shadow: 0 0 8px rgba(248, 81, 73, 0.4);
        }
        .legend {
            display: flex;
            justify-content: space-around;
            margin-top: 10px;
            font-size: 12px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>S3G4_SCOPE // Diagnostic Portal</h1>
            <div id="status" class="status-badge">Disconnected</div>
        </header>

        <div class="dashboard">
            <div class="panel">
                <div class="panel-title">Waveform Canvas</div>
                <canvas id="scopeCanvas" width="600" height="380"></canvas>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: var(--accent-yellow)"></div>
                        <span>CH 1</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: var(--accent-cyan)"></div>
                        <span>CH 2</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: var(--accent-green)"></div>
                        <span>CH 3</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: var(--accent-white)"></div>
                        <span>CH 4</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">Telemetry Signal Info</div>
                <div class="telemetry-grid">
                    <div class="telemetry-card">
                        <span class="telemetry-label">Frequency</span>
                        <span id="tel-freq" class="telemetry-value" style="color: var(--accent-cyan)">-- Hz</span>
                    </div>
                    <div class="telemetry-card">
                        <span class="telemetry-label">Vpp (Peak-to-Peak)</span>
                        <span id="tel-vpp" class="telemetry-value" style="color: var(--accent-yellow)">-- mV</span>
                    </div>
                    <div class="telemetry-card">
                        <span class="telemetry-label">Vrms</span>
                        <span id="tel-vrms" class="telemetry-value">-- mV</span>
                    </div>
                    <div class="telemetry-card">
                        <span class="telemetry-label">Vavg</span>
                        <span id="tel-vavg" class="telemetry-value">-- mV</span>
                    </div>
                    <div class="telemetry-card">
                        <span class="telemetry-label">Duty Cycle</span>
                        <span id="tel-duty" class="telemetry-value" style="color: var(--accent-green)">-- %</span>
                    </div>
                    <div class="telemetry-card">
                        <span class="telemetry-label">PGA Gain Scale</span>
                        <span id="tel-gain" class="telemetry-value">--</span>
                    </div>
                </div>

                <div class="panel-title" style="margin-top: 25px;">Scope Controls</div>
                <div class="control-group">
                    <button class="btn btn-primary" onclick="sendCommand(1, 1, 0)">START ACQUISITION</button>
                    <button class="btn btn-danger" onclick="sendCommand(2, 0, 0)">STOP ACQUISITION</button>
                </div>

                <div class="panel-title" style="margin-top: 25px;">WaveGen Controls</div>
                <div class="control-group">
                    <button class="btn" onclick="sendCommand(17, 0, 0)">START GENERATOR CH1</button>
                    <button class="btn" onclick="sendCommand(18, 0, 0)">STOP GENERATOR CH1</button>
                    <button class="btn" onclick="sendCommand(20, 0, 1000 | (0<<8) | (0<<16))">CONFIG: 1000Hz SINE</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const statusBadge = document.getElementById("status");
        const canvas = document.getElementById("scopeCanvas");
        const ctx = canvas.getContext("2d");
        let ws;

        function connect() {
            const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${wsProto}//${window.location.host}/ws`;
            console.log("Connecting WebSocket to " + wsUrl);
            
            ws = new WebSocket(wsUrl);
            ws.binaryType = "arraybuffer";

            ws.onopen = () => {
                statusBadge.textContent = "Connected";
                statusBadge.className = "status-badge connected";
            };

            ws.onclose = () => {
                statusBadge.textContent = "Disconnected";
                statusBadge.className = "status-badge";
                setTimeout(connect, 2000);
            };

            ws.onmessage = (event) => {
                if (event.data instanceof ArrayBuffer) {
                    parseTelemetry(event.data);
                }
            };
        }

        function parseTelemetry(buffer) {
            if (buffer.byteLength < 2064) return;
            const view = new DataView(buffer);
            
            // Header parsing
            const magic = view.getUint16(0, true);
            if (magic !== 0x55AA) return;

            const vpp = view.getUint16(2, true);
            const vrms = view.getUint16(4, true);
            const vavg = view.getUint16(6, true);
            const freq = view.getUint32(8, true);
            const duty = view.getUint8(12);
            const gain = view.getUint8(13);
            const ch_active = view.getUint8(14);

            // Update UI elements
            document.getElementById("tel-freq").textContent = freq >= 1000 ? (freq/1000).toFixed(2) + " kHz" : freq + " Hz";
            document.getElementById("tel-vpp").textContent = vpp + " mV";
            document.getElementById("tel-vrms").textContent = vrms + " mV";
            document.getElementById("tel-vavg").textContent = vavg + " mV";
            document.getElementById("tel-duty").textContent = duty + " %";
            document.getElementById("tel-gain").textContent = "G_" + gain;

            // Draw waveforms
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawGrid();

            // Channels data offset starts at 16
            const chOffset = 16;
            const chLen = 512;
            
            if ((ch_active & 0x01) !== 0) {
                drawChannel(new Uint8Array(buffer, chOffset, chLen), "rgba(255, 183, 0, 0.95)");
            }
            if ((ch_active & 0x02) !== 0) {
                drawChannel(new Uint8Array(buffer, chOffset + chLen, chLen), "rgba(0, 238, 255, 0.95)");
            }
            if ((ch_active & 0x04) !== 0) {
                drawChannel(new Uint8Array(buffer, chOffset + 2*chLen, chLen), "rgba(63, 185, 80, 0.95)");
            }
            if ((ch_active & 0x08) !== 0) {
                drawChannel(new Uint8Array(buffer, chOffset + 3*chLen, chLen), "rgba(255, 255, 255, 0.95)");
            }
        }

        function drawGrid() {
            ctx.strokeStyle = "var(--grid-line)";
            ctx.lineWidth = 1;
            
            // Vertical grid lines
            const divX = canvas.width / 10;
            for (let i = 1; i < 10; i++) {
                ctx.beginPath();
                ctx.moveTo(i * divX, 0);
                ctx.lineTo(i * divX, canvas.height);
                ctx.stroke();
            }

            // Horizontal grid lines
            const divY = canvas.height / 8;
            for (let i = 1; i < 8; i++) {
                ctx.beginPath();
                ctx.moveTo(0, i * divY);
                ctx.lineTo(canvas.width, i * divY);
                ctx.stroke();
            }
        }

        function drawChannel(dataArray, color) {
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            const stepX = canvas.width / dataArray.length;
            for (let i = 0; i < dataArray.length; i++) {
                const y = canvas.height - (dataArray[i] / 255) * canvas.height;
                if (i === 0) {
                    ctx.moveTo(0, y);
                } else {
                    ctx.lineTo(i * stepX, y);
                }
            }
            ctx.stroke();
        }

        function sendCommand(cmd_id, param1, data) {
            const buffer = new ArrayBuffer(8);
            const view = new DataView(buffer);
            view.setUint8(0, 0xAA);
            view.setUint8(1, cmd_id);
            view.setUint8(2, param1);
            view.setUint32(3, data, true);
            
            let checksum = 0xAA + cmd_id + param1;
            checksum += (data & 0xFF) + ((data >> 8) & 0xFF) + ((data >> 16) & 0xFF) + ((data >> 24) & 0xFF);
            view.setUint8(7, checksum & 0xFF);
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(buffer);
                console.log("Sent command to ESP32: ID=" + cmd_id + ", Param=" + param1 + ", Data=" + data);
            } else {
                alert("WebSocket is not connected!");
            }
        }

        connect();
    </script>
</body>
</html>
)html";

static void save_wifi_credentials(const char* ssid, const char* password) {
    nvs_handle_t handle;
    if (nvs_open("wifi_creds", NVS_READWRITE, &handle) == ESP_OK) {
        nvs_set_str(handle, "ssid", ssid);
        nvs_set_str(handle, "pass", password);
        nvs_commit(handle);
        nvs_close(handle);
        ESP_LOGI(TAG, "Saved Wi-Fi credentials to NVS: SSID=%s", ssid);
    }
}

static bool load_wifi_credentials(char* ssid, char* password, size_t len) {
    nvs_handle_t handle;
    bool success = false;
    if (nvs_open("wifi_creds", NVS_READONLY, &handle) == ESP_OK) {
        size_t ssid_len = len;
        size_t pass_len = len;
        if (nvs_get_str(handle, "ssid", ssid, &ssid_len) == ESP_OK &&
            nvs_get_str(handle, "pass", password, &pass_len) == ESP_OK) {
            success = true;
        }
        nvs_close(handle);
    }
    return success;
}

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_SCAN_DONE) {
        ap_count = MAX_SCANNED_APS;
        esp_wifi_scan_get_ap_records(&ap_count, ap_records);
        scan_done = true;
        ESP_LOGI(TAG, "Wi-Fi scan completed. Found %d access points.", ap_count);
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        char saved_ssid[33] = {0};
        char saved_pass[64] = {0};
        if (load_wifi_credentials(saved_ssid, saved_pass, sizeof(saved_ssid))) {
            ESP_LOGI(TAG, "Auto-connecting on startup to SSID: %s", saved_ssid);
            wifi_config_t wifi_config = {};
            strcpy((char*)wifi_config.sta.ssid, saved_ssid);
            strcpy((char*)wifi_config.sta.password, saved_pass);
            esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
            esp_wifi_connect();
        }
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(TAG, "Disconnected from Wi-Fi. Retrying automatically...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        char ip_str[32];
        esp_ip4addr_ntoa(&event->ip_info.ip, ip_str, sizeof(ip_str));
        ESP_LOGI(TAG, "Got IP address: %s", ip_str);
    }
}

// Static handler to serve index.html (either from SPIFFS or embedded diagnostic portal fallback)
static esp_err_t serve_diagnostic_page(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, diagnostic_html, strlen(diagnostic_html));
}

static esp_err_t static_file_handler(httpd_req_t *req) {
    char filepath[600];
    if (strcmp(req->uri, "/") == 0) {
        strcpy(filepath, "/spiffs/index.html");
    } else {
        snprintf(filepath, sizeof(filepath), "/spiffs%s", req->uri);
    }

    FILE *f = fopen(filepath, "r");
    if (f == NULL) {
        if (strcmp(filepath, "/spiffs/index.html") == 0) {
            return serve_diagnostic_page(req);
        }
        httpd_resp_send_err(req, HTTPD_404_NOT_FOUND, "File not found");
        return ESP_FAIL;
    }

    const char *type = "text/plain";
    if (strstr(filepath, ".html")) type = "text/html";
    else if (strstr(filepath, ".css")) type = "text/css";
    else if (strstr(filepath, ".js")) type = "application/javascript";
    else if (strstr(filepath, ".png")) type = "image/png";
    else if (strstr(filepath, ".ico")) type = "image/x-icon";
    
    httpd_resp_set_type(req, type);

    char buffer[1024];
    size_t read_bytes;
    while ((read_bytes = fread(buffer, 1, sizeof(buffer), f)) > 0) {
        httpd_resp_send_chunk(req, buffer, read_bytes);
    }
    fclose(f);
    httpd_resp_send_chunk(req, NULL, 0);
    return ESP_OK;
}

// WebSocket Route handler
static esp_err_t ws_handler(httpd_req_t *req) {
    if (req->method == HTTP_GET) {
        int fd = httpd_req_to_sockfd(req);
        ESP_LOGI(TAG, "WebSocket handshake completed on FD %d", fd);
        add_ws_client(fd);
        return ESP_OK;
    }

    httpd_ws_frame_t ws_pkt;
    uint8_t *buf = NULL;
    memset(&ws_pkt, 0, sizeof(httpd_ws_frame_t));
    ws_pkt.type = HTTPD_WS_TYPE_TEXT;
    
    esp_err_t ret = httpd_ws_recv_frame(req, &ws_pkt, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "httpd_ws_recv_frame failed: %s", esp_err_to_name(ret));
        return ret;
    }

    if (ws_pkt.len > 0) {
        buf = (uint8_t *)malloc(ws_pkt.len + 1);
        if (buf == NULL) {
            return ESP_ERR_NO_MEM;
        }
        ws_pkt.payload = buf;
        ret = httpd_ws_recv_frame(req, &ws_pkt, ws_pkt.len);
        if (ret != ESP_OK) {
            free(buf);
            return ret;
        }
    }

    if (ws_pkt.type == HTTPD_WS_TYPE_BINARY && ws_pkt.len == sizeof(tSpiRxCmd)) {
        tSpiRxCmd *cmd = (tSpiRxCmd *)ws_pkt.payload;
        uint8_t sum = cmd->sync + cmd->cmd_id + cmd->param1 +
                      (cmd->data & 0xFF) + ((cmd->data >> 8) & 0xFF) +
                      ((cmd->data >> 16) & 0xFF) + ((cmd->data >> 24) & 0xFF);
                      
        if (cmd->sync == SPI_CMD_SYNC && sum == cmd->checksum) {
            comm_spi_master_send_cmd(cmd->cmd_id, cmd->param1, cmd->data);
        }
    } else if (ws_pkt.type == HTTPD_WS_TYPE_CLOSE) {
        int fd = httpd_req_to_sockfd(req);
        remove_ws_client(fd);
    }

    if (buf) {
        free(buf);
    }
    return ESP_OK;
}

// Global SPIFFS Initialization
static esp_err_t init_spiffs(void) {
    ESP_LOGI(TAG, "Mounting SPIFFS filesystem on /spiffs");
    esp_vfs_spiffs_conf_t conf = {
        .base_path = "/spiffs",
        .partition_label = "storage",
        .max_files = 5,
        .format_if_mount_failed = true
    };
    esp_err_t ret = esp_vfs_spiffs_register(&conf);
    if (ret != ESP_OK) {
        return ret;
    }
    return ESP_OK;
}

esp_err_t wifi_ap_init(void) {
    ESP_LOGI(TAG, "Initializing Wi-Fi STA mode...");

    // Mount SPIFFS
    init_spiffs();

    // Create clients list mutex
    ws_clients_mutex = xSemaphoreCreateMutex();
    if (ws_clients_mutex == NULL) {
        return ESP_ERR_NO_MEM;
    }

    esp_err_t ret = esp_netif_init();
    if (ret != ESP_OK) return ret;

    ret = esp_event_loop_create_default();
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) return ret;

    esp_netif_t *sta_netif = esp_netif_create_default_wifi_sta();
    assert(sta_netif != NULL);

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ret = esp_wifi_init(&cfg);
    if (ret != ESP_OK) return ret;

    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));

    ret = esp_wifi_set_mode(WIFI_MODE_STA);
    if (ret != ESP_OK) return ret;

    ret = esp_wifi_start();
    if (ret != ESP_OK) return ret;

    ESP_LOGI(TAG, "Wi-Fi STA mode started successfully.");
    return ESP_OK;
}

void wifi_ap_broadcast_telemetry(const tSpiTxPayload *payload) {
    if (server_handle == NULL || ws_clients_mutex == NULL) {
        return;
    }

    xSemaphoreTake(ws_clients_mutex, portMAX_DELAY);
    for (int i = 0; i < MAX_WS_CLIENTS; i++) {
        int fd = ws_clients[i];
        if (fd != 0) {
            httpd_ws_frame_t ws_frame = {};
            ws_frame.payload = (uint8_t *)payload;
            ws_frame.len = sizeof(tSpiTxPayload);
            ws_frame.type = HTTPD_WS_TYPE_BINARY;

            esp_err_t err = httpd_ws_send_frame_async(server_handle, fd, &ws_frame);
            if (err != ESP_OK) {
                ws_clients[i] = 0;
                close(fd);
            }
        }
    }
    xSemaphoreGive(ws_clients_mutex);
}

void wifi_sta_start_scan(void) {
    scan_done = false;
    ap_count = 0;
    wifi_scan_config_t scan_config = {};
    scan_config.show_hidden = false;
    scan_config.scan_type = WIFI_SCAN_TYPE_ACTIVE;
    scan_config.scan_time.active.min = 100;
    scan_config.scan_time.active.max = 300;
    ESP_LOGI(TAG, "Starting Wi-Fi network scan...");
    esp_wifi_scan_start(&scan_config, false); // non-blocking scan
}

bool wifi_sta_is_scan_done(void) {
    return scan_done;
}

int wifi_sta_get_scan_results(wifi_scan_result_t *results, int max_results) {
    int count = (ap_count < max_results) ? ap_count : max_results;
    for (int i = 0; i < count; i++) {
        strncpy(results[i].ssid, (const char*)ap_records[i].ssid, sizeof(results[i].ssid) - 1);
        results[i].ssid[sizeof(results[i].ssid) - 1] = '\0';
        results[i].rssi = ap_records[i].rssi;
        results[i].authmode = ap_records[i].authmode;
    }
    return count;
}

esp_err_t wifi_sta_connect(const char* ssid, const char* password) {
    wifi_config_t wifi_config = {};
    strncpy((char*)wifi_config.sta.ssid, ssid, sizeof(wifi_config.sta.ssid) - 1);
    strncpy((char*)wifi_config.sta.password, password, sizeof(wifi_config.sta.password) - 1);
    
    // Save to NVS
    save_wifi_credentials(ssid, password);

    ESP_LOGI(TAG, "Connecting to SSID: %s...", ssid);
    esp_wifi_disconnect();
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    return esp_wifi_connect();
}

void wifi_sta_disconnect(void) {
    ESP_LOGI(TAG, "Disconnecting from current Wi-Fi network...");
    esp_wifi_disconnect();
}

void wifi_sta_set_power(bool power) {
    if (wifi_power_state == power) return;
    
    wifi_power_state = power;
    if (power) {
        ESP_LOGI(TAG, "Enabling Wi-Fi...");
        esp_wifi_start();
        char saved_ssid[33] = {0};
        char saved_pass[64] = {0};
        if (load_wifi_credentials(saved_ssid, saved_pass, sizeof(saved_ssid))) {
            wifi_config_t wifi_config = {};
            strcpy((char*)wifi_config.sta.ssid, saved_ssid);
            strcpy((char*)wifi_config.sta.password, saved_pass);
            esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
            esp_wifi_connect();
        }
    } else {
        ESP_LOGI(TAG, "Disabling Wi-Fi...");
        esp_wifi_disconnect();
        esp_wifi_stop();
    }
}

bool wifi_sta_get_power(void) {
    return wifi_power_state;
}

bool wifi_sta_is_connected(void) {
    wifi_ap_record_t info;
    return (esp_wifi_sta_get_ap_info(&info) == ESP_OK);
}

void wifi_sta_get_ip(char *ip_buf, size_t buf_len) {
    esp_netif_ip_info_t ip_info;
    esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    if (netif && esp_netif_get_ip_info(netif, &ip_info) == ESP_OK) {
        esp_ip4addr_ntoa(&ip_info.ip, ip_buf, buf_len);
    } else {
        strncpy(ip_buf, "0.0.0.0", buf_len - 1);
        ip_buf[buf_len - 1] = '\0';
    }
}

void wifi_sta_get_ssid(char *ssid_buf, size_t buf_len) {
    wifi_ap_record_t info;
    if (esp_wifi_sta_get_ap_info(&info) == ESP_OK) {
        strncpy(ssid_buf, (const char*)info.ssid, buf_len - 1);
        ssid_buf[buf_len - 1] = '\0';
    } else {
        strncpy(ssid_buf, "Desconectado", buf_len - 1);
        ssid_buf[buf_len - 1] = '\0';
    }
}

esp_err_t webserver_start(void) {
    if (server_handle != NULL) {
        return ESP_OK;
    }
    
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.core_id = 0;
    config.close_fn = socket_close_callback;
    config.lru_purge_enable = true;
    config.uri_match_fn = httpd_uri_match_wildcard;

    ESP_LOGI(TAG, "Starting HTTP/WebSocket Server on port %d...", config.server_port);
    esp_err_t ret = httpd_start(&server_handle, &config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start HTTP server: %s", esp_err_to_name(ret));
        return ret;
    }

    // Register WebSockets route `/ws`
    httpd_uri_t ws_uri = {};
    ws_uri.uri = "/ws";
    ws_uri.method = HTTP_GET;
    ws_uri.handler = ws_handler;
    ws_uri.user_ctx = NULL;
    ws_uri.is_websocket = true;
    httpd_register_uri_handler(server_handle, &ws_uri);

    // Register static file route for index.html / resources
    httpd_uri_t static_uri = {};
    static_uri.uri = "/*";
    static_uri.method = HTTP_GET;
    static_uri.handler = static_file_handler;
    static_uri.user_ctx = NULL;
    httpd_register_uri_handler(server_handle, &static_uri);

    return ESP_OK;
}

void webserver_stop(void) {
    if (server_handle == NULL) {
        return;
    }
    ESP_LOGI(TAG, "Stopping HTTP/WebSocket Server...");
    
    if (ws_clients_mutex != NULL) {
        xSemaphoreTake(ws_clients_mutex, portMAX_DELAY);
        for (int i = 0; i < MAX_WS_CLIENTS; i++) {
            if (ws_clients[i] != 0) {
                close(ws_clients[i]);
                ws_clients[i] = 0;
            }
        }
        xSemaphoreGive(ws_clients_mutex);
    }

    httpd_stop(server_handle);
    server_handle = NULL;
}

bool webserver_is_running(void) {
    return (server_handle != NULL);
}
