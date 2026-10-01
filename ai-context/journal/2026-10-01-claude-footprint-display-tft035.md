# 2026-10-01 — Claude Code — Símbolo y huella del display ER-TFT035IPS-6-4405

**Petición de Keneth:** incluir en KiCad el display de BuyDisplay (solo da el STEP), montado como en el DSO138: zócalo hembra en la placa base, tira macho en el display y separadores en los agujeros del otro lado. Keneth aún está pensando el prototipo: es una propuesta de montaje, no una decisión.

## Cambio (rama `ai/footprint-tft035`, carpeta `S3G4_LAB_rev2.1/04_esquematicos/kicad/`)

- `lib/s3g4.pretty/ER-TFT035IPS-6-4405_PinSocket_2x20_P2.54mm.kicad_mod`: origen en el pin 1; impares en x=0, pares en x=+2.54, numeración hacia -y (vista desde arriba de la placa base = vista frontal del display). Pads 1.7/1.0 como el `PinSocket_2x20` de KiCad. 4 agujeros metalizados Ø2.7 (M2.5) con pad Ø5, sin número (sin red), en (11.0, 7.07), (88.2, 7.07), (11.0, -55.33) y (88.2, -55.33). Contorno del display 96.7 x 66.4 en F.Fab, F.SilkS (cortado en los pads) y F.CrtYd.
- 3D: zócalo de KiCad (`rotate 0 0 180`), tira macho de KiCad invertida (`offset 0 0 11`, `rotate 180 0 0`) y STEP de BuyDisplay `${KIPRJMOD}/lib/3d/ER-TFTM035-6_3D.step` con `offset 95.2 -9.07 11.8`, `rotate 0 0 -90`.
- `lib/s3g4.kicad_sym`: símbolo `ER-TFT035IPS-6-4405` (ref. DS) con los 40 pines de JP1; campos MPN, fabricante, LCSC vacío y datasheet local.
- `fp-lib-table` y `sym-lib-table` del proyecto con la librería `s3g4`. `.gitignore`: se excluye el STEP de 49 MB (copia local en `lib/3d/`, original en Descargas).
- Generadores reproducibles en `lib/gen/`.

## Evidencia

- Cotas: datasheet `TFT_8Bit_Capacitive/ER-TFT035IPS-6-4405_Datasheet.pdf`, p. 9 (3.3, CTP + pin header): PCB 96.70 x 66.40, agujeros 77.20 x 62.40 a 12.50 / 2.00 del borde, R1.40 (Ø2.8 → M2.5), columna impar a 1.50 del borde, fila 39/40 a 9.07, 19 x 2.54 = 48.26. Medidas sobre los vectores del PDF (PyMuPDF): el paso de los pines y la separación de los agujeros cuadran con la escala (error < 0.1 mm).
- Patillaje: p. 11-12 (4.1). El pin 39 es CTP_INT con J7 cerrado (configuración actual del módulo).
- Colocación del STEP: se analizó la estructura del STEP (cuerpo `35-6-1`: PCB centrada en z=0 con 1.6 mm de espesor, agujeros R2 en (2, 7) y (2, 84.2), JP1 en x 9.07…57.33, JP2 en x≈64.5) y se comprobó con `kicad-cli pcb render`: el pin 1 cuadrado del modelo cae sobre el pad 1, y los agujeros y JP2 coinciden con el datasheet. Criterio de KiCad 10 medido: `rotate z` positivo en el archivo = horario visto desde arriba.
- `kicad-cli fp/sym export svg`: los dos archivos se leen sin error. DRC de una placa de prueba con la huella: 0 errores propios.

## Datos para el diseño

- Separación entre placas: 11 mm (zócalo 8.5 + plástico de la tira 2.5). Separadores M2.5 x 11 mm, hembra-hembra o macho-hembra. Los SMD Würth WA-SMSI M2.5 solo llegan a 10 mm.
- Los componentes de la cara trasera del display bajan hasta ≈ 8.9 mm sobre la placa base, así que debajo del display solo caben piezas de ≤ 8 mm.

## Pendientes

- Medir el módulo real con calibre (pin 1 ↔ agujeros): la cadena de cotas del datasheet acumula ±0.3 por cota.
- El 3D no incluye los separadores.
- Decidir si los separadores van a GND (hoy no tienen red).
- Comprobar el acceso a la ranura microSD del módulo una vez montado.
- No se ha tocado `.kicad_sch` ni `.kicad_pcb`.
