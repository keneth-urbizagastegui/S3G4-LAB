#ifndef S3V_PLAYER_H
#define S3V_PLAYER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define S3V_MAGIC_STR    "S3V1"
#define S3V_BLOCK_SIZE   16
#define S3V_BLOCK_COLS   30  // 480 / 16
#define S3V_BLOCK_ROWS   20  // 320 / 16
#define S3V_TOTAL_BLOCKS (S3V_BLOCK_COLS * S3V_BLOCK_ROWS) // 600
#define S3V_MASK_BYTES   (S3V_TOTAL_BLOCKS / 8)             // 75 bytes

typedef struct __attribute__((packed)) {
    char magic[4];          // "S3V1"
    uint16_t width;         // 480
    uint16_t height;        // 320
    uint16_t fps;           // 30
    uint16_t block_size;    // 16
    uint32_t total_frames;  // Total de cuadros
    uint32_t duration_sec;  // Duración en segundos
    uint32_t index_offset;  // Byte offset a la tabla de índices
    uint8_t reserved[8];
} s3v_header_t;

typedef struct __attribute__((packed)) {
    uint8_t frame_type;      // 1 = I-Frame (Completo), 2 = P-Frame (Delta blocks)
    uint8_t reserved;
    uint16_t changed_blocks; // Cantidad de bloques modificados (0..600)
    uint32_t payload_len;    // Longitud en bytes del payload LZ4
} s3v_frame_header_t;

typedef struct {
    uint32_t width;
    uint32_t height;
    uint32_t fps;
    uint32_t us_per_frame;
    uint32_t total_frames;
    uint32_t duration_sec;
    uint32_t current_frame;
    uint32_t elapsed_sec;
    bool is_open;
    bool is_eof;
} s3v_info_t;

esp_err_t s3v_player_init(void);
esp_err_t s3v_player_open(const char *filepath);
void s3v_player_close(void);

// Decodifica el siguiente cuadro a un búfer RGB565
// scale: 0 = 1:1 (480x320 para Fullscreen), 1 = 1/2 (240x160 para Studio)
esp_err_t s3v_player_read_next_frame(uint16_t *out_rgb565, uint8_t scale);

void s3v_player_seek_percent(int percent);
void s3v_player_restart(void);

const s3v_info_t *s3v_player_get_info(void);

#ifdef __cplusplus
}
#endif

#endif // S3V_PLAYER_H
