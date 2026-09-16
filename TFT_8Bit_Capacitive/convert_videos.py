#!/usr/bin/env python3
"""
Conversor unificado de video para el reproductor S3G4 (ESP32-S3 + ILI9488 480x320).

Sustituye a convert_to_s3v.py y a la version antigua de este fichero (ambos en legacy/).
Por cada .mp4/.mkv/.mov de la carpeta de origen genera, en la de destino:

    nombre.avi   MJPEG 480x320 4:2:0 a los fps pedidos (sin audio)
    nombre.jpg   miniatura 144x81 4:2:0 para la biblioteca
    nombre.json  {"title": ..., "subtitle": ...}

Al terminar mide, LEYENDO EL FICHERO GENERADO (tabla idx1), el tamano medio y maximo
de fotograma, y avisa si el maximo supera el limite del bufer del firmware.

Uso tipico:
    python convert_videos.py --src Videos --dst D:\\videos
    python convert_videos.py --src Videos --dst D:\\videos --fps 30 --q 8 --fit crop

Requiere ffmpeg en el PATH, o --ffmpeg "C:\\ruta\\ffmpeg.exe".
"""

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys

VIDEO_EXT = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v")

# Limite del bufer de entrada JPEG del firmware (main/avi_player.c, F4: crece hasta 128 KB).
CHUNK_WARN_BYTES = 128 * 1024


def find_ffmpeg(explicit):
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        sys.exit(f"ERROR: no existe {explicit}")
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # opcional
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    sys.exit(
        "ERROR: no encuentro ffmpeg.\n"
        "  Opciones: instalarlo (winget install Gyan.FFmpeg), pasar --ffmpeg <ruta>,\n"
        "  o instalar el paquete imageio-ffmpeg (pip install imageio-ffmpeg)."
    )


def title_from_filename(stem):
    """'Harry Styles - Dance No More' -> ('Dance No More', 'Harry Styles')."""
    m = re.match(r"^\s*(.+?)\s+[-–]\s+(.+?)\s*$", stem)
    if m:
        artist, title = m.group(1), m.group(2)
        return title.strip().strip("'\""), artist.strip()
    return stem.strip().strip("'\""), ""


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    return res.returncode, res.stderr[-800:]


def scale_filter(fit, w, h):
    if fit == "crop":
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black")


def measure_avi(path):
    """Recorre idx1 del AVI y devuelve (frames, chunk_avg, chunk_max). Todo contado."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        tail_len = min(size, 8 * 1024 * 1024)
        f.seek(size - tail_len)
        tail = f.read(tail_len)
        pos = tail.rfind(b"idx1")
        if pos < 0:
            return 0, 0, 0
        idx_size = struct.unpack_from("<I", tail, pos + 4)[0]
        idx_start = (size - tail_len) + pos + 8
        f.seek(idx_start)
        total = 0
        count = 0
        cmax = 0
        left = idx_size
        while left >= 16:
            chunk = f.read(min(left, 64 * 1024) // 16 * 16)
            if len(chunk) < 16:
                break
            for off in range(0, len(chunk) - 15, 16):
                if chunk[off:off + 4] in (b"00dc", b"00db"):
                    clen = struct.unpack_from("<I", chunk, off + 12)[0]
                    total += clen
                    count += 1
                    cmax = max(cmax, clen)
            left -= len(chunk)
        avg = total // count if count else 0
        return count, avg, cmax


def main():
    ap = argparse.ArgumentParser(description="Conversor de video para el reproductor S3G4")
    ap.add_argument("--src", required=True, help="carpeta con los videos de origen")
    ap.add_argument("--dst", required=True, help="carpeta de destino (la microSD, p. ej. D:\\videos)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--q", type=int, default=8, help="calidad MJPEG de ffmpeg (2 mejor, 31 peor)")
    ap.add_argument("--fit", choices=("crop", "pad"), default="crop",
                    help="crop recorta para llenar la pantalla; pad deja bandas negras")
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--height", type=int, default=320)
    ap.add_argument("--thumb-at", type=float, default=5.0, help="segundo del que se saca la miniatura")
    ap.add_argument("--ffmpeg", default=None)
    ap.add_argument("--force", action="store_true", help="rehacer aunque el .avi ya exista")
    args = ap.parse_args()

    ffmpeg = find_ffmpeg(args.ffmpeg)
    src = os.path.abspath(args.src)
    dst = os.path.abspath(args.dst)
    if not os.path.isdir(src):
        sys.exit(f"ERROR: no existe la carpeta de origen {src}")
    os.makedirs(dst, exist_ok=True)

    sources = sorted(f for f in os.listdir(src) if f.lower().endswith(VIDEO_EXT))
    if not sources:
        sys.exit(f"ERROR: no hay videos en {src}")

    print(f"ffmpeg: {ffmpeg}")
    print(f"{len(sources)} videos en {src} -> {dst}  ({args.width}x{args.height}, {args.fps} fps, q={args.q}, {args.fit})\n")

    ok, failed, warnings = 0, 0, []
    for name in sources:
        stem = os.path.splitext(name)[0]
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_").lower()[:24] or "video"
        in_path = os.path.join(src, name)
        avi = os.path.join(dst, safe + ".avi")
        jpg = os.path.join(dst, safe + ".jpg")
        js = os.path.join(dst, safe + ".json")

        print(f"- {name}  ->  {safe}.avi")
        if os.path.exists(avi) and not args.force:
            print("    ya existe, se omite (usa --force para rehacer)")
        else:
            code, err = run([
                ffmpeg, "-y", "-i", in_path,
                "-vf", f"{scale_filter(args.fit, args.width, args.height)},fps={args.fps}",
                "-c:v", "mjpeg", "-pix_fmt", "yuvj420p", "-q:v", str(args.q), "-an", avi,
            ])
            if code != 0:
                print(f"    ERROR de ffmpeg:\n{err}")
                failed += 1
                continue

        code, err = run([
            ffmpeg, "-y", "-ss", str(args.thumb_at), "-i", in_path, "-frames:v", "1",
            "-vf", scale_filter(args.fit, 144, 81),
            "-pix_fmt", "yuvj420p", "-q:v", "4", jpg,
        ])
        if code != 0:
            print("    AVISO: no se pudo generar la miniatura (el firmware usara el marcador)")

        title, subtitle = title_from_filename(stem)
        with open(js, "w", encoding="utf-8") as fh:
            json.dump({"title": title, "subtitle": subtitle}, fh, ensure_ascii=False, indent=1)

        frames, avg, cmax = measure_avi(avi)
        mb = os.path.getsize(avi) / (1024 * 1024)
        dur = frames / args.fps if frames else 0
        print(f"    {mb:.1f} MB · {frames} fotogramas · {int(dur // 60)}:{int(dur % 60):02d} · "
              f"medio {avg / 1024:.1f} KB · maximo {cmax / 1024:.1f} KB · titulo \"{title}\"")
        if cmax > CHUNK_WARN_BYTES:
            warnings.append(f"{safe}.avi tiene un fotograma de {cmax / 1024:.1f} KB "
                            f"(> {CHUNK_WARN_BYTES // 1024} KB): baja la calidad con --q {args.q + 2}")
        ok += 1

    print(f"\nListos: {ok} · fallidos: {failed}")
    for w in warnings:
        print("AVISO: " + w)
    print("\nCopia los tres ficheros de cada video (.avi, .jpg, .json) a la microSD, "
          "en /videos o en la raiz.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
