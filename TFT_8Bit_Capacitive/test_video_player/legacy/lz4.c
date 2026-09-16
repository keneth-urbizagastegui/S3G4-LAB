#include "lz4.h"
#include <string.h>

int LZ4_decompress_safe(const char* src, char* dst, int compressedSize, int dstCapacity) {
    const uint8_t* ip = (const uint8_t*)src;
    const uint8_t* const iend = ip + compressedSize;

    uint8_t* op = (uint8_t*)dst;
    uint8_t* const oend = op + dstCapacity;

    while (ip < iend) {
        uint8_t token = *ip++;
        size_t literal_len = (token >> 4);

        if (literal_len == 15) {
            uint8_t s;
            do {
                if (ip >= iend) return -1;
                s = *ip++;
                literal_len += s;
            } while (s == 255);
        }

        if (op + literal_len > oend || ip + literal_len > iend) return -2;
        memcpy(op, ip, literal_len);
        op += literal_len;
        ip += literal_len;

        if (ip >= iend) {
            break;
        }

        if (ip + 2 > iend) return -3;
        uint16_t offset = (uint16_t)(ip[0] | (ip[1] << 8));
        ip += 2;
        if (offset == 0) return -4;

        size_t match_len = (token & 0x0F) + 4;
        if ((token & 0x0F) == 15) {
            uint8_t s;
            do {
                if (ip >= iend) return -5;
                s = *ip++;
                match_len += s;
            } while (s == 255);
        }

        if (op + match_len > oend) return -6;

        const uint8_t* match = op - offset;
        if (match < (const uint8_t*)dst) return -7;

        if (offset >= match_len) {
            memcpy(op, match, match_len);
            op += match_len;
        } else {
            while (match_len--) {
                *op++ = *match++;
            }
        }
    }

    return (int)(op - (uint8_t*)dst);
}
