# Instalación del contexto compartido

- Fecha: 2026-09-18, cierre de verificación 21:18 UTC.
- Agente: Codex.
- Pedido: construir contexto unificado dentro de S3G4 LAB para Codex, Claude Code y agy; agy ya tenía instalado context-mode.
- Revisión: estructura del repositorio, README, manifiestos de cliente/firmware, estado de los bancos, mapa firmado y acta de pines, configuraciones existentes de las tres herramientas.
- Cambios: instrucciones comunes; resumen, estado y mapa de fuentes; conexiones MCP locales `s3g4-context`; sincronización al arrancar; fallback de búsqueda por CLI; prueba de integración con almacén separado.
- Decisión: archivos canónicos para decisiones y estado; índice compartido reconstruible. Se conserva el context-mode genérico de las plataformas y no se mezclan sus historiales privados.
- Evidencia: `ai-context/VALIDATION.md`, `.ai-runtime/verification-result.json`; 12 comprobaciones de integración correctas y 103 fuentes indexadas. Codex detecta configuración; Claude conecta; agy 1.2.6 muestra `s3g4-context` activo en `/mcp`, comprobado sin enviar prompts al modelo.
- Pendiente operativo: las sesiones que ya estaban abiertas necesitan reconectar o abrir una nueva sesión para cargar el MCP. La carga de reglas dentro de conversaciones nuevas no se ha probado mediante llamadas a modelos.
- Producto: no se modificó firmware, diseño eléctrico ni aplicaciones; no se asumió como concluido M-09/M-10 ni el front-end rev. 2.
