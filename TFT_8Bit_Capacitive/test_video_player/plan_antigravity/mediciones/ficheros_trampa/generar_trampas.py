#!/usr/bin/env python3
"""
Genera los ficheros trampa que exige el criterio de F5b §7.3: el escaneo debe marcarlos
como no compatibles, con el motivo correcto, y sin colgarse ni reiniciar la placa.

    python generar_trampas.py           # escribe los .avi junto a este script

Sale (todos pequenos, se copian a la microSD junto a los videos buenos):

    trampa_codec.avi    AVI bien formado pero con codec XVID (no MJPEG)
    trampa_tamano.avi   MJPEG correcto, pero de 240x160 en vez de 480x320 / 320x480
    trampa_roto.avi     fichero .avi que en realidad esta truncado a la mitad de un chunk

No necesita ffmpeg: los JPEG los genera Pillow y el contenedor AVI se escribe a mano.
"""

import io
import os
import struct
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
N_FRAMES = 60          # 2 segundos: suficiente para que el escaneo lo lea


def jpeg_frame(w, h, i, subsampling=2):
    """Un fotograma JPEG sintetico (barras que se mueven) para que cada uno pese distinto."""
    img = Image.new("RGB", (w, h), (12, 14, 20))
    d = ImageDraw.Draw(img)
    for k in range(8):
        x = (i * 4 + k * w // 8) % w
        d.rectangle([x, 0, x + w // 16, h], fill=(242, 179, 61) if k % 2 else (40, 60, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80, subsampling=subsampling)
    return buf.getvalue()


def write_avi(path, w, h, frames, fourcc=b"MJPG", truncate=False):
    """Escribe un AVI RIFF minimo con lista movi e indice idx1."""
    us_per_frame = 1000000 // FPS
    movi = bytearray()
    index = []
    for data in frames:
        if len(data) & 1:
            data += b"\x00"
        index.append((len(movi) + 4, len(data)))   # offset relativo a 'movi'
        movi += b"00dc" + struct.pack("<I", len(data)) + data

    idx1 = bytearray()
    for off, ln in index:
        idx1 += b"00dc" + struct.pack("<III", 0x10, off, ln)

    strf = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, int.from_bytes(fourcc, "little"),
                       w * h * 3, 0, 0, 0, 0)
    strh = (b"vids" + fourcc + struct.pack("<IHHIIIIIIIiHHHH", 0, 0, 0, 0, 1, FPS, 0,
                                           len(frames), 0, 0, -1, 0, 0, w, h))
    avih = struct.pack("<IIIIIIIIIIIIII", us_per_frame, w * h * 3 * FPS, 0, 0x10,
                       len(frames), 0, 1, 0, w, h, 0, 0, 0, 0)

    strl = b"LIST" + struct.pack("<I", 4 + 8 + len(strh) + 8 + len(strf)) + b"strl" \
        + b"strh" + struct.pack("<I", len(strh)) + strh \
        + b"strf" + struct.pack("<I", len(strf)) + strf
    hdrl = b"LIST" + struct.pack("<I", 4 + 8 + len(avih) + len(strl)) + b"hdrl" \
        + b"avih" + struct.pack("<I", len(avih)) + avih + strl
    movi_chunk = b"LIST" + struct.pack("<I", 4 + len(movi)) + b"movi" + bytes(movi)
    idx_chunk = b"idx1" + struct.pack("<I", len(idx1)) + bytes(idx1)

    body = b"AVI " + hdrl + movi_chunk + idx_chunk
    blob = b"RIFF" + struct.pack("<I", len(body)) + body
    if truncate:
        blob = blob[:len(blob) * 2 // 3]        # corta a media lista movi

    with open(path, "wb") as f:
        f.write(blob)
    print(f"  {os.path.basename(path):<20} {len(blob) / 1024:7.1f} KB  "
          f"{w}x{h}  {fourcc.decode()}{'  (truncado)' if truncate else ''}")


def main():
    print("Generando ficheros trampa en", HERE)
    frames_ok = [jpeg_frame(480, 320, i) for i in range(N_FRAMES)]

    # 1. Codec que no es MJPEG: cabecera XVID y fotogramas que NO son JPEG (como un XVID real).
    #    Correccion del 16/09/2026: la primera version llevaba fotogramas JPEG de verdad y el
    #    firmware la acepto con razon (la regla admite el fichero si el primer fotograma es JPEG).
    fake = [bytes([0x00, 0x00, 0x01, 0xB6]) + os.urandom(4000) for _ in range(N_FRAMES)]
    write_avi(os.path.join(HERE, "trampa_codec.avi"), 480, 320, fake, fourcc=b"XVID")

    # 2. MJPEG correcto pero de otra resolucion
    write_avi(os.path.join(HERE, "trampa_tamano.avi"), 240, 160,
              [jpeg_frame(240, 160, i) for i in range(N_FRAMES)])

    # 3. Fichero truncado a media lista movi (sin idx1)
    write_avi(os.path.join(HERE, "trampa_roto.avi"), 480, 320, frames_ok, truncate=True)

    print("\nCopia los tres a la microSD junto a los videos buenos.")
    print("Esperado en el escaneo: 'No es MJPEG', 'Resolucion 240x160' y un fichero ilegible,")
    print("los tres marcados como no compatibles y SIN reiniciar la placa.")


if __name__ == "__main__":
    main()
