# S10 — preparación del esquema de CH2/CH3 (6 oct 2026, Claude Opus 5.5)

- Keneth pidió hacer los esquemas de CH2/CH3. Eligió las opciones recomendadas: una hoja jerárquica por canal, referencias 2xx/3xx y una pareja de piezas *basic* para 2.37 kΩ.
- pcbparts, 6 oct: en 0603 al 1 % no hay 2.37 kΩ ni 180 Ω *basic*; sí 2.2 kΩ (C4190 en la BOM de CH1), 150 Ω (C22808), 120, 200 y 220 Ω. Elegidos 2.2 kΩ + 150 Ω = 2.35 kΩ (−0.84 %). RFILT2 = 1.1 kΩ (C22764), sin pareja: R_38/R_39 desaparecen y quedan 87 piezas por canal.
- `verificar_ch23.py`: CH1 contra s8_ch1.net da 0 diferencias. En una copia sintética de CH2 (refs y redes renombradas, sin cambiar el filtro) salen exactamente las 8 diferencias del filtro.
- Corrección a una respuesta anterior de esta sesión: la huella del TQ2SA **sí** se comprobó contra la p. 11 de C46047. Lo dice la cabecera de `lib/gen/gen_ch1_parts.py`, que añade que coincide con la huella SamacSys 16574131. La nota «[VERIFICAR]» de CH1_PIEZAS_Y_REDES §5 se quedó sin actualizar.
- Pendiente: la sesión de Konnect (encargo S10) y luego la auditoría.

## Auditoría de S10 (Claude, 6 oct)
- Netlist del proyecto reexportada por mi cuenta. `verificar_ch23.py` da código 0: CH1 89, CH2 87 y CH3 87 piezas, sin diferencias.
- ERC reejecutado: 31 = raíz (7 power_pin_not_driven + 3 pin_not_driven + 15 isolated_pin_label) + 3 pin_not_driven en /CH2/ + 3 en /CH3/. No hay tipos nuevos.
- Raíz: el reacomodo de CH1 (286 símbolos movidos, 296 → 274 cables) llegó con 88151ab (guardado de Keneth en KiCad). De 88151ab al final de S10 solo se añaden los 2 símbolos de hoja: 0 símbolos movidos y 0 cables cambiados. La netlist de CH1 sigue igual.
- ch2_completa.png: legible. Textos apretados heredados de CH1 en el bloque 1 (VC201 con C203) y en el filtro (CH2_F1_B junto a R224/R249). Son cosméticos.
- Pendiente de Keneth: abrir y guardar ch2/ch3 (ruta de instancia obsoleta en ch2), el cajetín de las tres hojas y la unión con main.
