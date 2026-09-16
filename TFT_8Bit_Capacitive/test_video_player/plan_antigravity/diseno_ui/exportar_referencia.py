#!/usr/bin/env python3
"""
Exporta los tableros del diseño a referencias que Antigravity puede seguir al pie de la letra:

    referencia/png/<Tablero>.png        captura 480x320 (1:1 con el panel) y @2x para ver detalle
    referencia/widgets/<Tablero>.md     tabla por elemento: x, y, ancho, alto, colores, fuente, texto
    referencia/widgets.json             lo mismo en JSON

    python exportar_referencia.py

Usa Chrome sin ventana. Las medidas salen del navegador (getBoundingClientRect), no a ojo.
"""

import html
import json
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "referencia")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SKIP = {"Componentes", "Tokens"}          # no son pantallas de 480x320

EXTRACT_JS = r"""
<script>
window.addEventListener('load', () => setTimeout(() => {
  const root = [...document.querySelectorAll('div')].find(d =>
      d.style.width === '480px' && d.style.height === '320px');
  const R = root.getBoundingClientRect();
  const rgb = c => {
    const m = c.match(/rgba?\(([\d.]+), ([\d.]+), ([\d.]+)(?:, ([\d.]+))?\)/);
    if (!m) return '';
    const a = m[4] === undefined ? 1 : +m[4];
    if (a === 0) return '';
    const hx = '#' + [m[1], m[2], m[3]].map(v => (+v).toString(16).padStart(2, '0')).join('').toUpperCase();
    return a < 1 ? hx + ' @' + Math.round(a * 100) + '%' : hx;
  };
  const ownText = el => [...el.childNodes].filter(n => n.nodeType === 3)
      .map(n => n.textContent.trim()).join(' ').trim();
  const rows = [];
  const walk = (el, depth) => {
    for (const c of el.children) {
      const tag = c.tagName.toLowerCase();
      const r = c.getBoundingClientRect();
      const s = getComputedStyle(c);
      if (s.display === 'none' || r.width === 0 || r.height === 0) continue;
      const bg = s.backgroundImage !== 'none' ? 'degradado (imagen)' : rgb(s.backgroundColor);
      const border = parseFloat(s.borderTopWidth) || parseFloat(s.borderBottomWidth) ||
                     parseFloat(s.borderLeftWidth) || parseFloat(s.borderRightWidth);
      const text = tag === 'svg' ? '' : ownText(c);
      const isIcon = tag === 'svg' || tag === 'img';
      const radius = s.borderTopLeftRadius;
      const opacity = +s.opacity;
      const interesting = isIcon || text || bg || border || opacity < 1 || s.position === 'absolute';
      if (interesting) rows.push({
        depth, kind: isIcon ? 'icono' : (text ? 'texto' : (bg || border ? 'caja' : 'grupo')),
        x: Math.round(r.left - R.left), y: Math.round(r.top - R.top),
        w: Math.round(r.width), h: Math.round(r.height),
        bg, fg: (text || isIcon) ? rgb(s.color) : '',
        border: (() => {
          const sides = ['Top','Right','Bottom','Left'].filter(k => parseFloat(s['border'+k+'Width']));
          if (!sides.length) return '';
          const k = sides[0];
          const where = sides.length === 4 ? '' : ' (' + sides.join('/').toLowerCase() + ')';
          return parseFloat(s['border'+k+'Width']) + 'px ' + rgb(s['border'+k+'Color']) + where;
        })(),
        radius: radius !== '0px' ? radius : '',
        opacity: opacity < 1 ? Math.round(opacity * 100) + '%' : '',
        font: text ? s.fontSize + ' ' + s.fontWeight : '',
        align: text ? s.textAlign : '',
        text,
        icon: tag === 'img' ? c.getAttribute('src') :
              (tag === 'svg' ? (c.getAttribute('data-icon') || c.getAttribute('aria-label') || 'svg ' + Math.round(r.width) + 'px') : ''),
      });
      if (tag !== 'svg') walk(c, depth + (interesting ? 1 : 0));
    }
  };
  walk(root, 0);
  document.documentElement.setAttribute('data-widgets', JSON.stringify(rows));
}, 600));
</script>
"""


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                           "--virtual-time-budget=3000", *args],
                          capture_output=True, text=True, encoding="utf-8", timeout=90)


def page_for(src, inject):
    """Copia del tablero sin support.js, con el fondo pegado a la esquina y, si se pide, el extractor."""
    body = open(src, encoding="utf-8").read()
    body = re.sub(r'<script src="\./support\.js"></script>', "", body)
    body = body.replace("<body>", '<body style="margin:0">', 1)
    if inject:
        body = body.replace("</body>", EXTRACT_JS + "</body>")
    fd, path = tempfile.mkstemp(suffix=".html", dir=tempfile.gettempdir())
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def md_table(name, rows):
    cols = ["#", "tipo", "x", "y", "ancho", "alto", "fondo", "texto/icono color", "borde", "radio",
            "opac.", "fuente", "alin.", "contenido"]
    out = [f"# {name} — medidas por elemento (480×320, origen arriba a la izquierda)", "",
           f"Referencia visual: `../png/{name}.png` (1:1) y `../png/{name}@2x.png`.",
           "Sangría del contenido = anidamiento (hijo del elemento de arriba). Las coordenadas son",
           "**absolutas en pantalla**; en EEZ, réstales las del contenedor padre.", "",
           "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for i, r in enumerate(rows, 1):
        content = r["text"] or r["icon"]
        content = ("· " * r["depth"]) + html.escape(content).replace("|", "\\|")
        out.append("| " + " | ".join(str(v) for v in [
            i, r["kind"], r["x"], r["y"], r["w"], r["h"], r["bg"], r["fg"], r["border"],
            r["radius"], r["opacity"], r["font"], r["align"], content]) + " |")
    return "\n".join(out) + "\n"


def main():
    os.makedirs(os.path.join(OUT, "png"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "widgets"), exist_ok=True)
    everything = {}
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".dc.html"):
            continue
        name = fn[:-len(".dc.html")]
        if name in SKIP:
            continue
        src = os.path.join(HERE, fn)

        shot = page_for(src, inject=False)
        url = "file:///" + shot.replace("\\", "/")
        chrome("--window-size=480,320", f"--screenshot={os.path.join(OUT, 'png', name + '.png')}", url)
        chrome("--window-size=480,320", "--force-device-scale-factor=2",
               f"--screenshot={os.path.join(OUT, 'png', name + '@2x.png')}", url)
        os.remove(shot)

        page = page_for(src, inject=True)
        dom = chrome("--dump-dom", "file:///" + page.replace("\\", "/")).stdout
        os.remove(page)
        m = re.search(r'data-widgets="([^"]*)"', dom)
        if not m:
            print(f"  {name}: SIN MEDIDAS")
            continue
        rows = json.loads(html.unescape(m.group(1)))
        everything[name] = rows
        with open(os.path.join(OUT, "widgets", name + ".md"), "w", encoding="utf-8") as f:
            f.write(md_table(name, rows))
        print(f"  {name:<24} {len(rows):3d} elementos")

    with open(os.path.join(OUT, "widgets.json"), "w", encoding="utf-8") as f:
        json.dump(everything, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
