import sys, pymupdf
# uso: crop.py pdf pagina nombre x0 y0 x1 y1 dpi   (coordenadas en px del overview a 110 dpi)
pdf, pg, name, x0, y0, x1, y1, dpi = sys.argv[1], int(sys.argv[2]), sys.argv[3], *map(float, sys.argv[4:8]), int(sys.argv[8])
k = 72/110.0
d = pymupdf.open(pdf); p = d[pg]
clip = pymupdf.Rect(x0*k, y0*k, x1*k, y1*k)
pix = p.get_pixmap(dpi=dpi, clip=clip)
out = sys.argv[9] + "/" + name + ".png"; pix.save(out); print(out, pix.width, "x", pix.height)
