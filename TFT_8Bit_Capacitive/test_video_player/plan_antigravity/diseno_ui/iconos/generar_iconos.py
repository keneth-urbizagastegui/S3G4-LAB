#!/usr/bin/env python3
"""
Genera TODOS los iconos del diseño en PNG a partir de los mismos SVG de los tableros, para que en la
placa se vean idénticos al canvas (sustituye a la versión dibujada a mano del 15/09/2026).

Blanco puro con canal alfa: en EEZ se tiñen con image_recolor (opa 255) al token que toque
(c_text, c_muted, c_accent, c_danger o #1A1204 dentro del botón de reproducir).

    python generar_iconos.py        # necesita Chrome y Pillow

La tabla ICONS dice nombre, tamaño en px y de dónde sale el SVG. Tamaño = el del tablero.
"""

import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BOARDS = os.path.dirname(HERE)
sys.path.insert(0, BOARDS)
import generar_tableros_estados as T  # noqa: E402  (iconos nuevos: repetir uno, aviso, reproducir)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCALE = 4        # se renderiza a 4x y se reduce con LANCZOS

STROKE = 'fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
FILL = 'fill="currentColor"'

# nombre: (tamaño, atributos de pintura, cuerpo SVG en viewBox 24)
ICONS = {
    "back":             (20, STROKE.format(sw=2), '<path d="M15 5l-7 7 7 7"/>'),
    "chevron_down":     (14, STROKE.format(sw=2.5), '<path d="M6 9l6 6 6-6"/>'),
    "queue":            (22, STROKE.format(sw=2), '<path d="M4 6h12M4 12h12M4 18h7"/><path d="M15 15v6l5-3z" fill="currentColor"/>'),
    "settings":         (20, STROKE.format(sw=2), '<path d="M4 7h9M18 7h2M4 17h3M12 17h8"/><circle cx="15.5" cy="7" r="2.5"/><circle cx="9.5" cy="17" r="2.5"/>'),
    "lock":             (20, STROKE.format(sw=2), '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'),
    "lock_big":         (26, STROKE.format(sw=2), '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'),
    "repeat":           (20, STROKE.format(sw=2), '<path d="M17 2l3 3-3 3"/><path d="M4 11V9a4 4 0 0 1 4-4h12"/><path d="M7 22l-3-3 3-3"/><path d="M20 13v2a4 4 0 0 1-4 4H4"/>'),
    "repeat_one":       (20, STROKE.format(sw=2), re.sub(r'^<svg[^>]*>|</svg>$', '', T.I_REPEAT_ONE)),
    "shuffle":          (20, STROKE.format(sw=2), '<path d="M3 6h4l10 12h4"/><path d="M3 18h4l3-3.6"/><path d="M14 9.6L17 6h4"/><path d="M18 3l3 3-3 3"/><path d="M18 15l3 3-3 3"/>'),
    "prev":             (22, FILL, '<rect x="5" y="5" width="2.5" height="14" rx="1"/><path d="M19 5v14L9 12z"/>'),
    "next":             (22, FILL, '<rect x="16.5" y="5" width="2.5" height="14" rx="1"/><path d="M5 5v14l10-7z"/>'),
    "play":             (20, FILL, '<path d="M7 4v16l13-8z"/>'),
    "pause":            (20, FILL, '<rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/>'),
    "rew10":            (24, STROKE.format(sw=1.8), '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 3v4h4"/><text x="12" y="15.5" font-size="7.5" font-family="Montserrat, sans-serif" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none">10</text>'),
    "fwd10":            (24, STROKE.format(sw=1.8), '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 3v4h-4"/><text x="12" y="15.5" font-size="7.5" font-family="Montserrat, sans-serif" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none">10</text>'),
    "seek_fwd":         (24, STROKE.format(sw=2), '<path d="M5 6l6 6-6 6"/><path d="M13 6l6 6-6 6"/>'),
    "seek_back":        (24, STROKE.format(sw=2), '<path d="M19 6l-6 6 6 6"/><path d="M11 6l-6 6 6 6"/>'),
    "brightness":       (20, STROKE.format(sw=2), '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    "close":            (18, STROKE.format(sw=2), '<path d="M6 6l12 12M18 6L6 18"/>'),
    "rescan":           (16, STROKE.format(sw=2), '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 3v4h-4"/>'),
    "warning":          (20, STROKE.format(sw=2), '<path d="M12 3L2 20h20z"/><path d="M12 10v4"/><path d="M12 17h.01"/>'),
    "film":             (34, STROKE.format(sw=1.5), '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3z"/>'),
    "sdcard":           (32, STROKE.format(sw=1.5), '<path d="M8 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6z"/><path d="M9 7v3M12 7v3M15 7v3"/>'),
    "sdcard_big":       (48, STROKE.format(sw=1.5), '<path d="M8 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6z"/><path d="M9 7v3M12 7v3M15 7v3"/>'),
    "sdcard_error_big": (48, STROKE.format(sw=1.5), '<path d="M8 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6z"/><path d="M12 9v4"/><path d="M12 16.5v.01"/>'),
}

CELL = 64 * SCALE


def main():
    names = list(ICONS)
    cols = 8
    rows = (len(names) + cols - 1) // cols
    cells = []
    for i, n in enumerate(names):
        size, paint, body = ICONS[n]
        px = size * SCALE
        x, y = (i % cols) * CELL, (i // cols) * CELL
        cells.append(f'<svg style="position:absolute;left:{x}px;top:{y}px" width="{px}" height="{px}" '
                     f'viewBox="0 0 24 24" {paint}>{body}</svg>')
    page = ('<html><head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap">'
            '</head><body style="margin:0;background:transparent;color:#fff">' + "".join(cells) + "</body></html>")
    fd, src = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(page)
    sheet = src[:-5] + ".png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", "--virtual-time-budget=3000",
                    f"--window-size={cols * CELL},{rows * CELL}", f"--screenshot={sheet}",
                    "file:///" + src.replace("\\", "/")], capture_output=True, timeout=90)
    img = Image.open(sheet).convert("RGBA")
    for i, n in enumerate(names):
        size = ICONS[n][0]
        x, y = (i % cols) * CELL, (i // cols) * CELL
        tile = img.crop((x, y, x + size * SCALE, y + size * SCALE))
        alpha = tile.getchannel("A")
        white = Image.new("RGBA", tile.size, (255, 255, 255, 255))
        white.putalpha(alpha)
        white.resize((size, size), Image.LANCZOS).save(os.path.join(HERE, n + ".png"))
        print(f"  {n + '.png':<22} {size}x{size}")
    os.remove(src)
    os.remove(sheet)


if __name__ == "__main__":
    main()
