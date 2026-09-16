#!/usr/bin/env python3
"""
Genera los iconos PNG que EEZ Studio necesita y que LVGL no trae como simbolo.

Se dibujan a 8x y se reducen con LANCZOS, en blanco puro con canal alfa, para que
en EEZ se tinten con image_recolor al color del token que toque (c_text o c_accent).

    python generar_iconos.py            # escribe los PNG junto a este script

Salida:
    rew10.png  fwd10.png  lock.png  queue.png  sdcard.png        24x24
    sdcard_big.png  sdcard_error_big.png  film.png               48x48 / 34x34
"""

import math
import os
from PIL import Image, ImageDraw

S = 8            # supermuestreo
W = (255, 255, 255, 255)
T = (255, 255, 255, 0)
HERE = os.path.dirname(os.path.abspath(__file__))


def canvas(size):
    return Image.new("RGBA", (size * S, size * S), T)


def save(img, size, name):
    out = img.resize((size, size), Image.LANCZOS)
    path = os.path.join(HERE, name)
    out.save(path)
    print(f"  {name}  {size}x{size}")


def arrowhead(d, cx, cy, angle, length, width):
    """Triangulo relleno apuntando en 'angle' (radianes)."""
    a = math.radians(140)
    pts = [
        (cx + length * math.cos(angle), cy + length * math.sin(angle)),
        (cx + width * math.cos(angle + a), cy + width * math.sin(angle + a)),
        (cx + width * math.cos(angle - a), cy + width * math.sin(angle - a)),
    ]
    d.polygon(pts, fill=W)


def digits_10(d, cx, cy, h):
    """Dibuja '10' con trazos, para que se lea a 24 px."""
    lw = max(2, int(h * 0.16))
    # 1
    x1 = cx - h * 0.42
    d.line([(x1, cy - h / 2), (x1, cy + h / 2)], fill=W, width=lw)
    d.line([(x1 - h * 0.18, cy - h * 0.30), (x1, cy - h / 2)], fill=W, width=lw)
    # 0
    x0 = cx + h * 0.28
    d.ellipse([x0 - h * 0.30, cy - h / 2, x0 + h * 0.30, cy + h / 2], outline=W, width=lw)


def icon_seek(direction):
    """Flecha circular con '10' dentro. direction: +1 adelante, -1 atras."""
    size = 24
    img = canvas(size)
    d = ImageDraw.Draw(img)
    c = size * S / 2
    r = size * S * 0.40
    lw = int(size * S * 0.085)
    if direction > 0:
        d.arc([c - r, c - r, c + r, c + r], start=-70, end=200, fill=W, width=lw)
        arrowhead(d, c + r * math.cos(math.radians(-70)), c + r * math.sin(math.radians(-70)),
                  math.radians(20), size * S * 0.16, size * S * 0.13)
    else:
        d.arc([c - r, c - r, c + r, c + r], start=-20, end=250, fill=W, width=lw)
        arrowhead(d, c + r * math.cos(math.radians(250)), c + r * math.sin(math.radians(250)),
                  math.radians(160), size * S * 0.16, size * S * 0.13)
    digits_10(d, c, c + size * S * 0.03, size * S * 0.30)
    return img, size


def icon_lock():
    size = 24
    img = canvas(size)
    d = ImageDraw.Draw(img)
    u = size * S
    lw = int(u * 0.085)
    d.rounded_rectangle([u * 0.22, u * 0.45, u * 0.78, u * 0.86], radius=u * 0.09,
                        outline=W, width=lw)
    d.arc([u * 0.33, u * 0.16, u * 0.67, u * 0.58], start=180, end=360, fill=W, width=lw)
    d.ellipse([u * 0.46, u * 0.60, u * 0.54, u * 0.70], fill=W)
    return img, size


def icon_queue():
    size = 24
    img = canvas(size)
    d = ImageDraw.Draw(img)
    u = size * S
    lw = int(u * 0.085)
    for i, y in enumerate((0.26, 0.46, 0.66)):
        x2 = 0.78 if i < 2 else 0.54
        d.line([(u * 0.16, u * y), (u * x2, u * y)], fill=W, width=lw)
    d.polygon([(u * 0.62, u * 0.60), (u * 0.62, u * 0.88), (u * 0.86, u * 0.74)], fill=W)
    return img, size


def icon_sd(size, error=False):
    """Tarjeta microSD: contorno poligonal con la esquina superior izquierda biselada."""
    img = canvas(size)
    d = ImageDraw.Draw(img)
    u = size * S
    lw = max(2, int(u * 0.065))
    body = [
        (u * 0.42, u * 0.12),   # arriba, tras el bisel
        (u * 0.78, u * 0.12),
        (u * 0.78, u * 0.88),
        (u * 0.22, u * 0.88),
        (u * 0.22, u * 0.32),   # inicio del bisel
    ]
    d.polygon(body, outline=W, width=lw)
    # contactos, separados del borde superior
    for x in (0.38, 0.52, 0.66):
        d.line([(u * x, u * 0.26), (u * x, u * 0.42)], fill=W, width=lw)
    if error:
        d.line([(u * 0.50, u * 0.52), (u * 0.50, u * 0.68)], fill=W, width=int(lw * 1.3))
        d.ellipse([u * 0.455, u * 0.735, u * 0.545, u * 0.825], fill=W)
    return img, size


def icon_film():
    """Marcador de posicion de miniatura (03 §10.5)."""
    size = 34
    img = canvas(size)
    d = ImageDraw.Draw(img)
    u = size * S
    lw = max(2, int(u * 0.07))
    d.rounded_rectangle([u * 0.08, u * 0.24, u * 0.62, u * 0.78], radius=u * 0.07,
                        outline=W, width=lw)
    d.polygon([(u * 0.66, u * 0.42), (u * 0.92, u * 0.28), (u * 0.92, u * 0.74), (u * 0.66, u * 0.60)],
              outline=W, fill=None)
    d.line([(u * 0.66, u * 0.42), (u * 0.92, u * 0.28)], fill=W, width=lw)
    d.line([(u * 0.92, u * 0.28), (u * 0.92, u * 0.74)], fill=W, width=lw)
    d.line([(u * 0.92, u * 0.74), (u * 0.66, u * 0.60)], fill=W, width=lw)
    return img, size


def main():
    print("Generando iconos en", HERE)
    img, s = icon_seek(-1); save(img, s, "rew10.png")
    img, s = icon_seek(+1); save(img, s, "fwd10.png")
    img, s = icon_lock(); save(img, s, "lock.png")
    img, s = icon_queue(); save(img, s, "queue.png")
    img, s = icon_sd(24); save(img, s, "sdcard.png")
    img, s = icon_sd(48); save(img, s, "sdcard_big.png")
    img, s = icon_sd(48, error=True); save(img, s, "sdcard_error_big.png")
    img, s = icon_film(); save(img, s, "film.png")
    print("Listo. En EEZ: importar como imagen, formato ARGB8888 o A8, y teñir con image_recolor.")


if __name__ == "__main__":
    main()
