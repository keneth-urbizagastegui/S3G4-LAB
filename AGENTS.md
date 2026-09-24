# S3G4 LAB — inicio de cualquier sesión

Estas instrucciones se aplican a todo el proyecto y a Codex, Claude Code y agy.

1. Antes de trabajar, lee `ai-context/START.md` y `ai-context/STATE.md`. Son el resumen compartido; no cargues el repositorio entero.
2. Para decisiones y detalles, consulta el servidor MCP **s3g4-context** (context-mode): `ctx_search` con preguntas específicas y `sort: "timeline"`. Para normas vigentes usa `source: "S3G4/"`. No confundas esta memoria con el servidor genérico `context-mode` de cada aplicación.
3. Si ese MCP no está conectado, usa `node tools/ai-context/context.mjs search "términos"` o lee el documento puntual indicado en `ai-context/SOURCES.md`. Informa de la falta de conexión, pero no pidas que el usuario repita el contexto.
4. Usa context-mode para analizar salidas grandes y archivos: procesa los datos y devuelve sólo hallazgos. Las ediciones se hacen con las herramientas normales de archivos.
5. Antes de editar un subsistema, consulta sus fuentes rectoras. Separa firmware de producción, bancos de prueba y hardware rev. 2. Las actas históricas no prueban que el hardware esté conectado ni que una prueba se haya repetido hoy.
6. Al terminar trabajo relevante, actualiza `ai-context/STATE.md` y registra un archivo nuevo en `ai-context/journal/` con fecha/hora, agente, cambio, evidencia, pruebas y pendientes. Registra decisiones permanentes en `ai-context/DECISIONS.md` con fuente. No inventes acuerdos ni marques una propuesta como aceptada.
7. Después de cambiar memoria o fuentes, ejecuta `node tools/ai-context/context.mjs sync` o usa `ctx_index(path: ruta_absoluta, source: "S3G4/ruta_relativa")` en **s3g4-context**. El arranque de una nueva conexión también sincroniza las fuentes.
8. Para evitar perder el trabajo de otra IA, relee el archivo compartido justo antes de editarlo y aplica cambios pequeños. Cada sesión crea su propio archivo de diario; no reemplaces el estado completo con un resumen antiguo.

Precedencia: instrucciones actuales del usuario → evidencia y fuentes rectoras vigentes → memoria resumida → actas históricas/README. Si hay contradicción, señala las fuentes y conserva la incertidumbre.

No guardes claves, credenciales ni chats completos en la memoria. No modifiques firmware, PCB o parámetros del banco sólo para mantener el contexto. Los permisos normales de cada herramienta siguen vigentes.
