#!/usr/bin/env python3
"""
Tableros de estados que faltaban en el canvas (16/09/2026): biblioteca con desplazamiento y tarjetas
no compatibles, avisos emergentes, pantalla «ninguno compatible» y estados de la barra de controles.

    python generar_tableros_estados.py      # escribe los .dc.html junto a este script

Mismos tokens que Tokens.dc.html. Tras ejecutarlo: python exportar_referencia.py
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))

HEAD = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&amp;display=swap">
  <style>
    body { margin: 0; background: #0B0C0F; font-family: Montserrat, "Segoe UI", sans-serif; }
    svg { display: block; }
  </style>
</helmet>
"""
TAIL = "</x-dc>\n</body>\n</html>\n"

# --- iconos (mismos trazos que los tableros originales) -------------------------------------------
def svg(body, size=20, fill=False, sw=2):
    paint = 'fill="currentColor"' if fill else \
        f'fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" {paint}>{body}</svg>'

I_SETTINGS = svg('<path d="M4 7h9M18 7h2M4 17h3M12 17h8"></path><circle cx="15.5" cy="7" r="2.5"></circle><circle cx="9.5" cy="17" r="2.5"></circle>')
I_LOCK = svg('<rect x="5" y="11" width="14" height="10" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path>')
I_REPEAT = svg('<path d="M17 2l3 3-3 3"></path><path d="M4 11V9a4 4 0 0 1 4-4h12"></path><path d="M7 22l-3-3 3-3"></path><path d="M20 13v2a4 4 0 0 1-4 4H4"></path>')
I_REPEAT_ONE = svg('<path d="M17 2l3 3-3 3"></path><path d="M4 11V9a4 4 0 0 1 4-4h12"></path><path d="M7 22l-3-3 3-3"></path><path d="M20 13v2a4 4 0 0 1-4 4H4"></path>'
                   '<text x="12" y="15.2" font-size="8" font-family="Montserrat, sans-serif" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none">1</text>')
I_PREV = svg('<rect x="5" y="5" width="2.5" height="14" rx="1"></rect><path d="M19 5v14L9 12z"></path>', 22, fill=True)
I_NEXT = svg('<rect x="16.5" y="5" width="2.5" height="14" rx="1"></rect><path d="M5 5v14l10-7z"></path>', 22, fill=True)
I_PAUSE = svg('<rect x="6" y="5" width="4" height="14" rx="1"></rect><rect x="14" y="5" width="4" height="14" rx="1"></rect>', fill=True)
I_PLAY = svg('<path d="M7 4v16l13-8z"></path>', fill=True)
I_REW = svg('<path d="M4 12a8 8 0 1 0 2.4-5.7"></path><path d="M4 3v4h4"></path><text x="12" y="15.5" font-size="7.5" font-family="Montserrat, sans-serif" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none">10</text>', 24, sw=1.8)
I_FWD = svg('<path d="M20 12a8 8 0 1 1-2.4-5.7"></path><path d="M20 3v4h-4"></path><text x="12" y="15.5" font-size="7.5" font-family="Montserrat, sans-serif" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none">10</text>', 24, sw=1.8)
I_SHUFFLE = svg('<path d="M3 6h4l10 12h4"></path><path d="M3 18h4l3-3.6"></path><path d="M14 9.6L17 6h4"></path><path d="M18 3l3 3-3 3"></path><path d="M18 15l3 3-3 3"></path>')
I_WARN = svg('<path d="M12 3L2 20h20z"></path><path d="M12 10v4"></path><path d="M12 17h.01"></path>')
I_FILM = svg('<rect x="3" y="6" width="13" height="12" rx="2"></rect><path d="M16 10l5-3v10l-5-3z"></path>', 34, sw=1.5)
I_SD = svg('<path d="M8 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6z"></path><path d="M9 7v3M12 7v3M15 7v3"></path>', 48, sw=1.5)

TEXT, MUTED, ACCENT, DANGER = "#EDEDEA", "#8E929B", "#F2B33D", "#E5484D"
BG, SURF, SURF_HI, LINE = "#0B0C0F", "#15171C", "#1F2228", "#2A2D34"

GRADS = [
    "radial-gradient(120% 90% at 70% 40%, #C9683A 0%, #5B2A3F 45%, #16213A 100%)",
    "linear-gradient(160deg, #3A4A6B 0%, #1B2233 60%, #0E1118 100%)",
    "linear-gradient(200deg, #7A3B5C 0%, #2B1A2E 70%)",
    "linear-gradient(140deg, #2F6B5E 0%, #14302B 70%)",
    "linear-gradient(170deg, #5C5A2E 0%, #25230F 70%)",
    "linear-gradient(120deg, #3D2F6B 0%, #17122B 70%)",
]


def abs_(x, y, w=None, h=None, extra=""):
    s = f"position: absolute; left: {x}px; top: {y}px;"
    if w is not None:
        s += f" width: {w}px;"
    if h is not None:
        s += f" height: {h}px;"
    return s + " " + extra


def icon_btn(x, y, icon, color=TEXT, extra=""):
    return (f'<div style="{abs_(x, y, 44, 44)} display: flex; align-items: center; justify-content: center; '
            f'color: {color}; {extra}">{icon}</div>')


def lib_header(summary):
    return f"""  <div style="{abs_(0, 0, 480, 44)} border-bottom: 1px solid {LINE}; box-sizing: border-box; background: {BG}; z-index: 2;">
    <div style="{abs_(16, 10)} font-size: 20px; font-weight: 700;">Biblioteca</div>
    <div style="{abs_(170, 16, 250)} text-align: right; font-size: 11px; color: {MUTED};">{summary}</div>
    {icon_btn(428, 0, I_SETTINGS)}
  </div>
"""


def card(x, y, title, meta, grad=None, meta_color=MUTED, dim=False, placeholder=False, badge=None):
    """Tarjeta de 144 px. y es la parte superior de la miniatura (144x80)."""
    op = " opacity: 0.45;" if dim else ""
    if placeholder or grad is None:
        thumb = (f'<div style="{abs_(0, 0, 144, 80)} border-radius: 6px; background: {SURF}; display: flex; '
                 f'align-items: center; justify-content: center; color: {MUTED};">{I_FILM}</div>')
    else:
        thumb = f'<div style="{abs_(0, 0, 144, 80)} border-radius: 6px; background: {grad};"></div>'
    b = ""
    if badge:
        b = (f'<div style="{abs_(6, 6)} height: 18px; padding: 0 8px; border-radius: 9px; background: {SURF}; '
             f'color: {badge[1]}; font-size: 10px; font-weight: 600; display: flex; align-items: center;">{badge[0]}</div>')
    tcol = MUTED if dim else TEXT
    return f"""    <div style="{abs_(x, y, 144, 114)}{op}">
      {thumb}{b}
      <div style="{abs_(0, 87, 144)} font-size: 13px; font-weight: 600; color: {tcol}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{title}</div>
      <div style="{abs_(0, 105, 144)} font-size: 11px; color: {meta_color}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{meta}</div>
    </div>
"""


def root(bg=BG, inner=""):
    return (f'<div style="position: relative; width: 480px; height: 320px; overflow: hidden; background: {bg}; '
            f'color: {TEXT};">\n{inner}</div>\n')


def video_bg():
    return (f'  <div style="{abs_(0, 0, 480, 320)} background: radial-gradient(120% 90% at 70% 40%, #C9683A 0%, '
            f'#5B2A3F 38%, #16213A 70%, #07090E 100%);"></div>\n'
            f'  <div style="{abs_(250, 90, 90, 120)} border-radius: 45px 45px 8px 8px; background: #0D0F16; opacity: 0.85;"></div>\n')


def osd_bottom(y, playing=True, repeat=1, shuffle=False, pressed=None, pos_pct=42, disabled=None):
    """Barra inferior del reproductor (84 px). repeat: 0 off, 1 todo, 2 uno. pressed: x del botón pulsado."""
    rep_icon = I_REPEAT_ONE if repeat == 2 else I_REPEAT
    rep_col = MUTED if repeat == 0 else ACCENT
    thumb_x = int(352 * pos_pct / 100) - 6

    def btn(x, icon, color=TEXT):
        extra = f"background: {SURF_HI}; border-radius: 22px;" if pressed == x else ""
        if disabled == x:
            extra += " opacity: 0.4;"
        return icon_btn(x, 36, icon, color, extra)

    return f"""  <div style="{abs_(0, y, 480, 84)} background: {BG}; border-top: 1px solid {LINE}; box-sizing: border-box;">
    <div style="{abs_(8, 7, 48)} text-align: right; font-size: 11px; color: {MUTED};">1:24</div>
    <div style="{abs_(64, 12, 352, 4)} border-radius: 2px; background: {LINE};">
      <div style="width: {pos_pct}%; height: 4px; border-radius: 2px; background: {ACCENT};"></div>
      <div style="{abs_(thumb_x, -4, 12, 12)} border-radius: 6px; background: {ACCENT};"></div>
    </div>
    <div style="{abs_(424, 7, 48)} font-size: 11px; color: {MUTED};">3:21</div>
    {btn(8, I_LOCK)}
    {btn(56, rep_icon, rep_col)}
    {btn(122, I_PREV)}
    {btn(170, I_REW)}
    <div style="{abs_(218, 36, 44, 44)} border-radius: 22px; background: {ACCENT}; display: flex; align-items: center; justify-content: center; color: #1A1204;">{I_PAUSE if playing else I_PLAY}</div>
    {btn(266, I_FWD)}
    {btn(314, I_NEXT)}
    {btn(380, I_SHUFFLE, ACCENT if shuffle else MUTED)}
    {btn(428, I_SETTINGS)}
  </div>
"""


def toast(x, y, w, title, body, icon_color=DANGER):
    return f"""  <div style="{abs_(x, y, w)} box-sizing: border-box; padding: 10px 12px; border-radius: 8px; background: {SURF}; border: 1px solid {LINE}; display: flex; gap: 10px; align-items: flex-start; z-index: 3;">
    <div style="color: {icon_color}; flex: none;">{I_WARN}</div>
    <div>
      <div style="font-size: 13px; font-weight: 600; color: {TEXT};">{title}</div>
      <div style="margin-top: 3px; font-size: 11px; color: {MUTED}; line-height: 15px;">{body}</div>
    </div>
  </div>
"""


# --- tableros ---------------------------------------------------------------------------------------
def biblioteca_llena():
    # Desplazada 40 px: se ve el final de la fila 1, la fila 2 entera y el principio de la fila 3.
    off = -40
    rows = [56 + off, 56 + 126 + off, 56 + 252 + off]
    cards = [
        card(12, rows[0], "Dance No More", "Harry Styles · 3:21", GRADS[0], badge=("Reproduciendo", ACCENT)),
        card(168, rows[0], "hate that i made you love me", "Ariana Grande · 3:02", GRADS[1]),
        card(324, rows[0], "ICONIC BY MISTAKE", "LE SSERAFIM x ILLIT · 3:40", GRADS[2]),
        card(12, rows[1], "HANDS UP", "MEOVV · 2:58", GRADS[3]),
        card(168, rows[1], "clip_viejo", "Sin girar: puede verse corte", GRADS[4],
             badge=("Sin girar", MUTED)),
        card(324, rows[1], "trampa_tamano", "Resolución 240×160", dim=True, meta_color=DANGER, placeholder=True),
        card(12, rows[2], "quinto", "Keneth · 1:05", GRADS[5]),
        card(168, rows[2], "trampa_roto", "Archivo truncado", dim=True, meta_color=DANGER, placeholder=True),
    ]
    grid = (f'  <div style="{abs_(0, 44, 480, 276)} overflow: hidden;">\n'
            f'   <div style="{abs_(0, -44, 480, 440)}">\n' + "".join(cards) + "   </div>\n"
            f'    <div style="{abs_(472, 38, 3, 96)} border-radius: 2px; background: {LINE};"></div>\n'
            "  </div>\n")
    return root(inner=lib_header("6 videos · 2 no compatibles · 29,7 GB libres") + grid)


def biblioteca_aviso():
    cards = [
        card(12, 56, "Dance No More", "Harry Styles · 3:21", GRADS[0], badge=("Reproduciendo", ACCENT)),
        card(168, 56, "hate that i made you love me", "Ariana Grande · 3:02", GRADS[1]),
        card(324, 56, "trampa_tamano", "Resolución 240×160", dim=True, meta_color=DANGER, placeholder=True),
        card(12, 182, "HANDS UP", "MEOVV · 2:58", GRADS[3]),
    ]
    inner = lib_header("3 videos · 1 no compatible · 29,7 GB libres") + "".join(cards)
    inner += f'  <div style="{abs_(322, 54, 148, 84)} border-radius: 8px; border: 2px solid {DANGER}; box-sizing: border-box;"></div>\n'
    inner += toast(166, 180, 302, "No se puede reproducir",
                   "Resolución 240×160. Se admiten 320×480 y 480×320.<br>Conviértelo con convert_videos.py")
    return root(inner=inner)


def player_aviso():
    inner = video_bg()
    inner += f'  <div style="{abs_(0, 0, 480, 236)} background: rgba(11,12,15,0.55);"></div>\n'
    inner += f"""  <div style="{abs_(0, 0, 480, 40)} background: {BG}; border-bottom: 1px solid {LINE}; box-sizing: border-box;">
    {icon_btn(0, -2, svg('<path d="M15 5l-7 7 7 7"></path>'))}
    <div style="{abs_(48, 5, 300)} font-size: 14px; font-weight: 600;">clip_danado</div>
    <div style="{abs_(48, 23, 300)} font-size: 11px; color: {MUTED};">05 / 06</div>
  </div>
"""
    inner += toast(90, 150, 300, "No se pudo reproducir",
                   "El video no muestra imagen. Volviendo a la biblioteca…")
    inner += toast(90, 70, 300, "Próximamente", "Esta opción llega en la próxima versión.", icon_color=ACCENT)
    inner += osd_bottom(236, playing=False, repeat=0)
    return root(bg="#000", inner=inner)


def sin_medios_incompatibles():
    return f"""<div style="position: relative; width: 480px; height: 320px; overflow: hidden; background: {BG}; color: {TEXT}; display: flex; flex-direction: column; align-items: center; justify-content: center;">
  <div style="color: {DANGER};">{I_SD}</div>
  <div style="margin-top: 14px; font-size: 20px; font-weight: 700;">Ningún video compatible</div>
  <div style="margin-top: 6px; width: 380px; text-align: center; font-size: 12px; color: {MUTED}; line-height: 17px;">Hay 3 archivos, ninguno compatible.<br>Conviértelos con convert_videos.py (MJPEG 320×480, 30 fps)</div>
  <div style="margin-top: 22px; display: flex; gap: 12px;">
    <div style="width: 120px; height: 44px; border-radius: 8px; background: {SURF}; color: {ACCENT}; font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: center;">Reintentar</div>
    <div style="width: 120px; height: 44px; border-radius: 8px; background: {SURF}; color: {TEXT}; font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: center;">Ajustes</div>
  </div>
</div>
"""


def estados_osd():
    labels = [
        (0, "En pausa · repetir desactivado · aleatorio activo"),
        (107, "Reproduciendo · repetir uno · pulsando «siguiente»"),
        (214, "Último video sin repetir: «siguiente» desactivado (40 %)"),
    ]
    inner = ""
    for y, text in labels:
        inner += f'  <div style="{abs_(12, y + 4)} font-size: 11px; color: {MUTED};">{text}</div>\n'
    inner += osd_bottom(20, playing=False, repeat=0, shuffle=True, pos_pct=18)
    inner += osd_bottom(127, playing=True, repeat=2, pressed=314, pos_pct=60)
    inner += osd_bottom(234, playing=True, repeat=0, pos_pct=75, disabled=314)
    return root(inner=inner)


BOARDS = {
    "BibliotecaLlena": biblioteca_llena,
    "BibliotecaAviso": biblioteca_aviso,
    "PlayerAviso": player_aviso,
    "SinMediosIncompatibles": sin_medios_incompatibles,
    "EstadosOSD": estados_osd,
}


def main():
    for name, fn in BOARDS.items():
        with open(os.path.join(HERE, name + ".dc.html"), "w", encoding="utf-8") as f:
            f.write(HEAD + fn() + TAIL)
        print("  ", name)


if __name__ == "__main__":
    main()
