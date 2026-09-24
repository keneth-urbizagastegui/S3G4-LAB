# Contexto compartido de S3G4 LAB para agy

Lee y aplica `AGENTS.md`, `ai-context/START.md` y `ai-context/STATE.md` antes de trabajar. Son los mismos archivos que usan Codex y Claude Code.

Usa **s3g4-context**, definido en `.agents/mcp_config.json`, para consultar y actualizar la memoria compartida mediante las herramientas `ctx_*`. El plugin context-mode ya instalado se conserva. Al cerrar trabajo relevante registra decisiones, evidencia y pendientes según `AGENTS.md`; no dependas de que un hook capture toda la conversación.
