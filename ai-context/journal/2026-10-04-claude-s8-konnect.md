# S8: CH1 en KiCad con Konnect (Claude Code, 4 oct 2026, mediodía)

- **Cambio:** hoja plana A2 de CH1 en `S3G4_LAB_rev2.1/04_esquematicos/kicad/s3g4.kicad_sch`, rama `ai/s8-ch1-esquema` (commits b9f1be1, 36ccb06 y fa9dad8, sin push). Primera escritura de Konnect 0.12.1 sobre KiCad 10.0.6: funciona.
- **Evidencia:** `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/INFORME_S8.md`, `s8_ch1.net`, `erc_s8.rpt` y `s8_ch1.pdf`.
- **Pruebas:**
  - `verificar_s8.py` sale con 0: 89 piezas, 229 pines y 56 redes, sin diferencias.
  - ERC: 12 violaciones, todas por bloques ausentes.
- **Pendientes:**
  - Atributo DNP de C103: Konnect no lo expone.
  - Símbolos provisionales de K101, SW101, J101 y VC101.
  - Pinouts NO VERIFICADOS de 2N7002, BAV99 y 1N4148W.
  - Contradicciones C107 (8.7 frente a 8.2 pF) y C125/126 (16 frente a 25 V) entre la tabla y la BOM.
  - Auditoría con kicad-happy.
- **Notas:**
  - No se tocaron STATE ni DECISIONS.
  - El MCP s3g4-context no conectó en esta sesión.
