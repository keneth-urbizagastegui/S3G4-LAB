# Memoria compartida de S3G4 LAB

Configurada el 18 de septiembre de 2026 para Codex, Claude Code y Antigravity CLI (`agy`) en esta computadora.

## Uso cotidiano

Abre una **sesión nueva sobre la carpeta S3G4 LAB** después de esta instalación. Las conexiones MCP ya abiertas no recargan automáticamente su configuración. Las instrucciones del proyecto indican a la IA que lea `START.md` y `STATE.md`, y consulte la información necesaria en **s3g4-context**. No necesitas volver a explicar el proyecto ni copiar el historial de otro chat.

Puedes comprobarlo con una petición normal: «Retoma el proyecto usando el contexto compartido y dime qué está pendiente». Debe distinguir el cliente avanzado, los pendientes M-09/M-10 y las fuentes del hardware rev. 2; no debe asumir que se hicieron pruebas nuevas.

Al terminar trabajo relevante, las instrucciones piden actualizar el estado, guardar decisiones y crear una entrada en `journal/`. Esta actualización semántica depende de que el agente siga las instrucciones: ningún índice puede deducir por sí solo qué propuesta aprobaste. Lo que no se registre no se garantiza entre chats.

## Dónde está cada cosa

| Ruta | Función |
|---|---|
| `AGENTS.md` | Protocolo común y entrada de Codex |
| `CLAUDE.md` | Importa las instrucciones comunes para Claude |
| `GEMINI.md`, `.agents/rules/s3g4-context.md` | Entrada y regla permanente para agy |
| `ai-context/START.md` | Resumen breve del proyecto y mapa de carpetas |
| `ai-context/STATE.md` | Estado, evidencia y pendientes |
| `ai-context/DECISIONS.md` | Acuerdos permanentes y sus fuentes |
| `ai-context/SOURCES.md`, `index.json` | Fuentes rectoras y selección explícita para indexar |
| `ai-context/journal/` | Una entrada por sesión/cambio relevante |
| `.ai-runtime/` | Índices SQLite, bloqueo de sincronización y pruebas locales; ignorado por Git |
| `tools/ai-context/` | Lanzador, sincronizador y prueba de integración |

## Conexiones

Los tres clientes usan **el mismo runtime de context-mode y el mismo almacén**, con el nombre `s3g4-context`:

- Codex: `.codex/config.toml`.
- Claude Code: `.mcp.json`; habilitación específica en `.claude/settings.local.json`.
- agy: `.agents/mcp_config.json`, configuración oficial de workspace. Conexión confirmada en el panel interactivo `/mcp` de agy 1.2.6. `agy mcp list` no muestra esta conexión local; no usar esa salida como prueba única del workspace.

El plugin general `context-mode` se conserva. Su historial capturado por hooks sigue siendo propio de cada herramienta. Para contexto común del proyecto las instrucciones seleccionan `s3g4-context`. No se migraron ni borraron bases privadas anteriores.

En cada conexión nueva, el lanzador indexa la selección de fuentes antes de servir herramientas. Un bloqueo serializa sincronizaciones concurrentes. context-mode actualiza fuentes respaldadas por archivos al buscar; `sync` incorpora documentos nuevos y sustituye por un aviso las fuentes retiradas de la selección. Los archivos compartidos permiten reconstruir el índice si context-mode elimina contenido antiguo por su política de caducidad.

## Comandos de comprobación

Desde la raíz del proyecto, con Node.js disponible:

```powershell
node tools/ai-context/context.mjs info
node tools/ai-context/context.mjs sync
node tools/ai-context/context.mjs search "M-09 teléfono"
node tools/ai-context/verify.mjs
```

`verify` comprueba el MCP real con tres perfiles de cliente y almacenamiento de prueba separado en `.ai-runtime/verification/`. No llama a modelos ni consume conversaciones de las IA. Resultado más reciente: `.ai-runtime/verification-result.json`.

## Alcance y mantenimiento

- El resumen inicial se basa en una revisión de README, estructura, manifiestos, actas y fuentes rectoras; no es una auditoría línea por línea ni una certificación eléctrica.
- Se incluyen documentos locales ignorados por Git, mediante rutas explícitas. `sync` informa de fuentes ausentes. Copiar sólo el repositorio versionado puede dejar esas fuentes fuera.
- Se excluyen del índice inicial dependencias, builds, archivos binarios y conversaciones completas. Añade nuevas fuentes a `index.json` de forma selectiva.
- Los archivos de memoria y las configuraciones pueden versionarse. `.ai-runtime/` y `runtime.local.json` son locales. No se hizo commit ni se incorporaron al índice Git otros archivos del usuario.
- Las configuraciones MCP contienen rutas absolutas de esta computadora. Si mueves la carpeta o cambias de equipo, actualiza esas tres configuraciones.
- Se reutiliza context-mode **1.0.169** ya instalado en la caché de Codex, fijado en `runtime.local.json`, y Node **24.19.0** del runtime local. No se modificó el plugin. Si se elimina esa versión de la caché, ajusta `contextModeDir` a una instalación compatible y repite `verify`.
- La configuración es para agy CLI. No se afirma haber activado una sesión del antiguo Antigravity IDE.

## Bases de la integración

- [Codex: configuración por proyecto y MCP](https://developers.openai.com/codex/config-reference/).
- [Claude Code: MCP por proyecto](https://code.claude.com/docs/en/mcp).
- [Antigravity: MCP global y de workspace](https://antigravity.google/docs/mcp?tab=cli).
- [Antigravity: reglas de inicio en `.agents/rules`](https://antigravity.google/docs/rules-workflows).
- [context-mode: compatibilidad de plataformas](https://github.com/mksglu/context-mode/blob/main/docs/platform-support.md).
