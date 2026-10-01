---
trigger: always_on
---

# Inicio y continuidad de S3G4 LAB

Al comenzar una sesión en este proyecto, lee `AGENTS.md`, `ai-context/START.md` y `ai-context/STATE.md`. Consulta los detalles con `ctx_search` del MCP **s3g4-context**, `sort: "timeline"` y `source: "S3G4/"`.

El servidor se define en `.agents/mcp_config.json` y comparte su almacén con Codex y Claude Code. El servidor genérico context-mode del plugin es distinto. Si falta la conexión compartida, usa `node tools/ai-context/context.mjs search "términos"` desde la raíz sin pedir al usuario que repita la información.

Al terminar cambios relevantes actualiza el estado y crea una entrada independiente en `ai-context/journal/` con decisiones, archivos, pruebas y pendientes; sigue el protocolo de `AGENTS.md`. Sincroniza mediante `node tools/ai-context/context.mjs sync`.
