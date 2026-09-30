# S3G4 LAB rev 2.1 — proyecto KiCad (reglas para IA)

Se aplica a esta carpeta y completa el `AGENTS.md` de la raíz (memoria compartida `ai-context/`, precedencia de fuentes). Si hay contradicción, manda el de la raíz y las instrucciones del usuario.

Proyecto: instrumento con STM32G473 + ESP32-S3, AFE a batería de 3 canales, DMM de baja tensión y AWG de 2 canales. Herramienta: KiCad 10.0.6. Requisitos vigentes: `../../00_requisitos/`. Decisiones de diseño: `../../01_diseno/rediseno_afe_rev21.html` y `ai-context/DECISIONS.md`.

## Reglas

- No edites `.kicad_sch` ni `.kicad_pcb` a mano. Los cambios van por Konnect (MCP) o los hace el humano en KiCad.
- Antes de cualquier cambio: `git status` limpio del proyecto y commit. Trabaja en una rama `ai/<tarea>`; nunca directamente en `rev2.1` ni `main`.
- Prohibido sin petición expresa del usuario:
  - autorruteo (Freerouting u otro),
  - tocar el stackup,
  - mover o rutear el front-end analógico, la partición de tierras analógica/digital, VDDA, VREF+ y la zona de antena.
  - Cuando existan las clases de red y zonas del AFE, anótalas aquí con sus nombres reales.
- Toda afirmación sobre un componente cita datasheet (página) y MPN/LCSC. Si no se verifica, márcala «NO VERIFICADO».
- Tras cada cambio: `kicad-cli sch erc` y `kicad-cli pcb drc`, e informa del diff de netlist.
- Cierra el esquemático en la GUI (o recárgalo) antes de que Konnect escriba el `.kicad_sch`; guarda siempre antes de una sesión de IA.
- Un solo actuador MCP a la vez. No instales `nevenfo/kicad-agentic-mcp` ni `KiCAD-MCP-Server` junto a Konnect.
- Fabricación sólo desde un tag `release/*`, nunca desde ramas `ai/*`.
- La IA revisa y propone; las reglas DRC (clearance, creepage, clases de red) las decide y escribe el humano en `s3g4.kicad_dru`.

## Estructura

| Ruta | Uso |
|---|---|
| `s3g4.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | Proyecto (se crean con *Archivo → Nuevo proyecto* en esta carpeta, nombre `s3g4`) |
| `s3g4.kicad_dru` | Reglas DRC personalizadas |
| `lib/s3g4.pretty/` | Huellas propias del proyecto (verificadas a mano contra datasheet) |
| `lib/s3g4.kicad_sym` | Símbolos propios (campos MPN, LCSC, Datasheet en cada pieza) |
| `lib/3d/` | Modelos 3D propios; rutas con `${KIPRJMOD}` |
| `output/`, `production/` | Salidas generadas; no se versionan |
