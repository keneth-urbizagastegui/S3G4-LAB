# Entorno KiCad 10.0.6 + IA para la rev 2.1

- Fecha: 2026-09-30, noche.
- Agente: Claude Code (Sonnet 5.5).
- Pedido de Keneth: configurar, paso a paso, el entorno del informe «KiCad 10.0.6 + IA» (kicad-happy, Konnect, plugins de fabricación, MCP de componentes y SPICE) para dejar Altium y diseñar la rev 2.1 en KiCad.
- Rama de trabajo: `ai/prueba-konnect` (creada desde `rev2.1`).

## Cambio

- **Entorno:** `C:\Program Files\KiCad\10.0\bin` añadido al PATH de usuario; `uv` 0.12.21 instalado con winget. Ya estaban Git, Python 3.12, Java 21, `gh` y `claude`. Node no se instaló (no hace falta).
- **KiCad:** API IPC habilitada (Preferencias → Complementos), intérprete Python de KiCad 3.11.5.
- **Plugins del PCM:** Interactive Html BOM 2.12.0, Fabrication Toolkit **5.3.0** (la 5.3.1 corrige «duplicate footprint» de KiCad 10; el PCM no ofreció otra) y KiKit plugin 1.6.0.
- **KiKit backend:** `pip install --user kikit` con el Python de KiCad → 1.8.1, en `Documents\KiCad\10.0\3rdparty\Python311\site-packages`. Resuelve el aviso «KiKit installation not found». `kikit.exe` queda fuera del PATH.
- **Claude Code:** plugin `kicad-happy` 2.2.1 (alcance usuario). MCP de alcance usuario: `pcbparts` (HTTP, https://pcbparts.dev/mcp) y `ltspice` (`ltspice-mcp` 0.6.1 ya instalado con uv). LTspice está en `AppData\Local\Programs\ADI\LTspice`.
- **Konnect 0.12.1:** no está en el catálogo del PCM; se instaló con «Instalar desde archivo» usando `konnect-pcm-v0.12.1-windows.zip` (15,1 MB, SHA-256 coincide con el digest de la release de GitHub). MCP de alcance proyecto en `S3G4_LAB_rev2.1/04_esquematicos/kicad/.mcp.json` (pendiente de que Keneth lo apruebe al abrir `claude` en esa carpeta).
- **Esqueleto del proyecto** `S3G4_LAB_rev2.1/04_esquematicos/kicad/`: `.gitignore`, `AGENTS.md`/`CLAUDE.md` con reglas para IA, `s3g4.kicad_dru` (vacío a propósito), `lib/s3g4.pretty/`, `lib/3d/` y el proyecto `s3g4` creado por Keneth en KiCad.
- Commits en `rev2.1`: `890ed1a` (esqueleto) y `a880570` (MCP de Konnect).

## Evidencia y pruebas

- `kicad-cli version` = 10.0.6; ERC del esquemático vacío: 0 violaciones; DRC del PCB vacío: 1 (`invalid_outline`, sin contorno en Edge.Cuts, esperable).
- Konnect, hablado por stdio sin pasar por el cliente MCP: `initialize` correcto (0.12.1), 21 herramientas base, 21 toolsets bajo demanda (incluye `pcb_board`, `verification`, `design_review`, `manufacturing`). `get_installation_info` ve KiCad 10.0.6, `kicad-cli` y el socket IPC. `get_project_info` y `get_board_info` (vía IPC, `source: ipc`) leen el proyecto `s3g4`. Ningún archivo cambió.
- `get_layer_list` falla con «No (layers) section» porque el `.kicad_pcb` recién creado no tiene sección de capas; es esperable hasta que se guarde con contenido.
- El PCB nuevo es de **2 capas de cobre**. Las 4 capas y el stackup son decisión de Keneth y se fijan a mano en KiCad (Configuración de la placa); Konnect no debe tocar el stackup.
- No probado: escritura con Konnect, kicad-happy sobre un diseño real, pcbparts y ltspice con consultas reales.

## Pendientes

1. Keneth: abrir `claude` en `04_esquematicos/kicad/` y aprobar el servidor `konnect`.
2. Decidir número de capas y stackup; dibujar el contorno (Edge.Cuts).
3. Escribir las reglas DRC reales (clearance/creepage de la entrada según RF-xx) y las clases de red en `s3g4.kicad_dru`.
4. `s3g4.kicad_pro` aparece modificado sin commit (lo reescribe KiCad).
5. No probado aún: `incidencia #610` de Konnect (`set_active_layer` puede dejar la placa ilegible en 10.0.6); no usarla.
6. Opcional: añadir `Scripts` de KiKit al PATH; JLCPCB Tools de Bouni (no instalar junto a Fabrication Toolkit sin decidir); pcb-inspector; KiBot/CI.
