# Herramientas de la rev 2.1: generadores de dibujos, cálculos y páginas

- `sch.py`: librería de símbolos SVG (la misma del esbozo de la rev 2.0).
- `draw_rev21.py`, `draw_c.py`: esquemas de las secciones B y C de `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html`.
- `draw_dso112.py` + `build_dso112.py`: redibujos del DSO112 y generación de `S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html` (toma el CSS del documento vivo).
- `draw_wave2.py` + `build_wave2.py`: redibujos del WAVE2 y generación de `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html`.
- `draw_openscope.py` + `build_openscope.py`: redibujo del canal del OpenScope y generación de `S3G4_LAB_rev2.1/02_referencias/analisis_openscope.html`.
- `calc_black_scope.py` + `draw_black_scope.py` + `build_black_scope.py`: cifras, redibujo del canal y generación de `S3G4_LAB_rev2.1/02_referencias/analisis_black_scope.html`.
- `calc_g473.py` + `build_g473.py`: cifras y generación de `S3G4_LAB_rev2.1/02_referencias/g473_analogico.html` (partes analógicas del STM32G473).
- `calc_rieles.py` + `seccion_g.py`: presupuesto de energía y parche que insertó la sección G en el documento vivo (23 sep, noche).
- `build_requisitos_dmm_awg.py`: genera `S3G4_LAB_rev2.1/00_requisitos/requisitos_dmm_awg.html` (requisitos del DMM y del AWG, 23 sep).
- `build_requisitos.py`: genera `S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html` (requisitos funcionales acordados el 23 sep).
- `calc_dmm_tida01012.py` + `draw_dmm_tida01012.py` + `build_dmm_tida01012.py`: cifras, redibujos (tensión, corriente y cadena) y generación de `S3G4_LAB_rev2.1/02_referencias/dmm_tida01012.html` (7 oct). `chk_dmm.py <modulo> <funciones>` comprueba los solapes de cualquier redibujo del DMM.
- `calc_dmm_hydrameter.py` + `draw_dmm_hydrameter.py` + `build_dmm_hydrameter.py`: lo mismo para `02_referencias/dmm_hydrameter.html` (7 oct). La netlist se exporta con `kicad-cli` de las fuentes KiCad del proyecto; el generador reutiliza la plantilla de `build_dmm_tida01012.py` (al importarla, regenera también esa página, igual).
- `fix_ruido.py`: parche que corrigió el modelo de ruido (kT/C) en los documentos; se conserva como registro de las cifras.
- **El texto del documento vivo se mantiene editándolo directamente**; los scripts sólo generan los dibujos y las páginas de análisis.
- `chk_c.py`, `chk_d.py`, `chk_w.py`, `chk_o.py`, `chk_b.py`: comprobador geométrico de textos solapados o cruzando cables.
- `render_svg.py <modulo> <funcion...>`: vista previa PNG de un esquema con PyMuPDF (`pip install pymupdf`); los estilos se pasan a atributos porque MuPDF ignora las clases CSS.
- `crop_pdf.py`: recorte de una zona de un PDF a PNG a alta resolución.

Uso: ejecutar desde esta carpeta con Python 3.12. Las rutas son relativas a `S3G4_LAB_rev2.1/`; los scripts se pueden mover con la carpeta.

- **No regenerar** `analisis_dso112.html`, `analisis_wave2.html` ni `analisis_openscope.html` con su `build_*.py`: se corrigieron después (`fix_ruido.py` y otros parches) y el script no lleva esas correcciones.
- `seccion_g.py` y `fix_ruido.py` son parches de una sola vez: se guardan como registro y no se vuelven a ejecutar.
