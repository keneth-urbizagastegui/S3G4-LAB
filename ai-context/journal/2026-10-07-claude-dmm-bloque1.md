# DMM, bloque 1 (bornes y protección): de S11.1 a su cierre (7 oct 2026, Claude Opus 5.5)

## Cambio
- Keneth decidió diseñar por bloques; S11a quedó aparcado.
- Bloque 1 simulado por Codex (gpt-6.1-sol, esfuerzo low) en S11.1–S11.4, cada uno auditado por Opus (esfuerzo medio). Rediseño y estudios pequeños hechos con Sonnet.
- Decisiones de Keneth (todas en DECISIONS.md, 7 oct):
  - relé TQ2SA en la fuente de ohmios (B);
  - RD-10 relajado en ohmios a 60 V, como el ELVIS (O4);
  - prueba de diodo como el ELVIS;
  - GBU808 + Littelfuse 0216 en el borne A;
  - piezas de pulso y GDT + varistor 14D431K para la ESD;
  - bornes Amass 24.245.
- Páginas: `01_diseno/dmm_bloque1.html` (v3) y un aviso en la sección H (v5).

## Evidencia
Actas y auditorías en `03_simulaciones/DMM/`:
- ACTA/AUDITORIA S11_1 … S11_4;
- REDISENO_BLOQUE1.md;
- GDT_SEGUIMIENTO.md.

## Pendientes
- MPN de las resistencias antipulso: ≥ 1.5 kV a 1.2/50 µs en 1206; ≥ 2 kV en 2512.
- La hoja del fabricante del GDT.
- La resistencia de 3 MΩ al 0.1 % del divisor (bloque 2).
- La pieza del derivador.
- En el prototipo: ESD IEC 61000-4-2 y la red a 230/253 Vrms.
- Siguiente bloque: el 2, frontal de tensión.
