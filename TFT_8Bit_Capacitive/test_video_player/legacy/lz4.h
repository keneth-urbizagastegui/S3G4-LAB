#ifndef LZ4_H
#define LZ4_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int LZ4_decompress_safe(const char* src, char* dst, int compressedSize, int dstCapacity);

#ifdef __cplusplus
}
#endif

#endif // LZ4_H
