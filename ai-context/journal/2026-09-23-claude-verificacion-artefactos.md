# Verificación de los artefactos publicados y del índice compartido

- Fecha: 2026-09-23, ≈ 18:20 hora local.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: «tenemos 7 artefactos, quiero saber si están guardados y compartidos con los demás agentes».

## Comprobación

- Se descargó la versión publicada de cada artefacto (`Artifact read`, ruta `index.html`) y se comparó con su archivo local, normalizando los saltos de línea. **Los 7 coinciden:** el publicado es el local más el envoltorio que añade la publicación (553 o 4105 bytes, este último en las páginas con diagramas Mermaid).

| Artefacto | Archivo local | Enlace |
|---|---|---|
| Rediseño AFE rev 2.1 | `docs/rediseno_afe_rev21.html` | https://claude.ai/artifact/YLrJwmm5Cz6w864dUYsrBT |
| Anatomía del DSO112 | `docs/analisis_dso112.html` | https://claude.ai/artifact/1Q3Ajh4q39Pdic6AV6w1LR |
| Anatomía del WAVE2 | `docs/analisis_wave2.html` | https://claude.ai/artifact/LgEYV3M8LjE8RqbTvAQMcE |
| Anatomía del OpenScope MZ | `docs/analisis_openscope.html` | https://claude.ai/artifact/8KbSKL4sWnYoQzPJgKsRwf |
| Anatomía de black_scope | `docs/analisis_black_scope.html` | https://claude.ai/artifact/EQGpdo9q4Fu2EkwqAgykAn |
| Periféricos analógicos del G473 | `docs/g473_analogico.html` | https://claude.ai/artifact/8fBAS9Tis7h8yQh9qnSciB |
| Esbozo de hardware S3G4 (rev 2.0) | `docs/esbozo_hardware_s3g4.html` | https://claude.ai/artifact/N2QCUrWegFApQ51QXQWM1u |

- Codex, Claude Code y agy arrancan el mismo `tools/ai-context/server.mjs`, cada uno con su plataforma y todos sobre el mismo almacén `.ai-runtime/`. La validación del 18 sep (`.ai-runtime/verification-result.json`) ya probó que lo que escribe uno lo recupera otro.
- Los enlaces de claude.ai son **privados de Keneth**: los otros agentes no los abren. Leen los archivos de `docs/` y el índice.

## Cambio

- `docs/esbozo_hardware_s3g4.html` **no estaba en `ai-context/index.json`** y su contenido no aparecía en el índice. Se añadió.
- `STATE.md`: enlace del documento vivo y una línea sobre esta verificación.
- `node tools/ai-context/context.mjs sync`: 122 fuentes indexadas, 0 ausentes, 0 retiradas. Las 7 páginas figuran en `.ai-runtime/managed-sources.json`.

## Límites

- `docs/` está en el `.gitignore` confirmado, y `ai-context/` y `Simulation_LTSpice_rev21/` siguen sin confirmar en Git. Todo existe sólo en este disco. No se hizo ningún commit.
- Las páginas HTML se indexan como un solo bloque con su CSS. Para buscar cifras rinden más los diarios en Markdown de cada análisis, que llevan los valores.
