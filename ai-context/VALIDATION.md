# Validación de la memoria compartida

Fecha: 2026-09-18. Runtime: context-mode 1.0.169; Node.js 24.19.0; Windows.

## Comprobado

- Sincronización final: **103 archivos, 0 ausentes**, incluida la guía y el diario de instalación.
- Prueba de integración: **12 comprobaciones pasaron en 22 segundos**, resultado de 2026-09-18 21:18 UTC. Script: `tools/ai-context/verify.mjs`.
- Tres procesos MCP independientes, inicializados con nombres/perfiles `codex`, `claude-code` y `agy`, arrancan simultáneamente desde `firmware/` y comparten el mismo almacén de prueba.
- Exposición de `ctx_search`, `ctx_index`, `ctx_execute` y `ctx_execute_file`; esquema de herramientas compatible con el perfil Gemini/agy.
- Un proceso con perfil Codex escribe una fuente que los otros dos recuperan. El proceso con perfil Claude la actualiza y el de agy ve la nueva versión.
- Una fuente respaldada por archivo refleja los cambios al consultar, sin reindexación manual.
- Escrituras concurrentes, persistencia después de cerrar todos los procesos, recuperación de M-09/M-10 y retirada de fuentes obsoletas funcionan.
- El comando nativo `codex mcp get s3g4-context --json` reconoce la configuración local como habilitada.
- El comando nativo `claude mcp get s3g4-context` informa **Connected**, con ámbito de proyecto.
- Antigravity CLI **1.2.6**, abierto sobre S3G4 LAB: el panel interactivo `/mcp` muestra **✓ s3g4-context** y sus herramientas `ctx_execute`, `ctx_execute_file`, `ctx_index`, `ctx_search`, `ctx_fetch_and_index` y otras seis. Confirma que la configuración de workspace sí se carga. Se cerró la sesión sin enviar un prompt al modelo.

## Límites de la comprobación

Los perfiles de la prueba automatizada son clientes del protocolo MCP. Además se verificó el panel nativo de agy y los comandos de configuración de Codex/Claude. No se ejecutaron prompts de prueba con modelos. Se configuraron las entradas de inicio documentadas; la obediencia semántica a las instrucciones no es una garantía del protocolo MCP.

Para agy se escribió `.agents/mcp_config.json` y una regla `always_on`. Su comando `mcp list` devolvió el inventario global vacío, incluso al especificar el proyecto; en cambio, el panel `/mcp` de una sesión abierta sobre la carpeta sí confirmó el servidor local conectado.

No se compiló ni programó firmware, no se conectaron instrumentos, y no se repitieron las pruebas de producto citadas en actas. La memoria las identifica como evidencia documental histórica.
