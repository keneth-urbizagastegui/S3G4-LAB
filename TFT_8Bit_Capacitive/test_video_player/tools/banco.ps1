# Banco de trabajo del reproductor: compilar, flashear y medir sin depender del PATH del usuario.
#
#   pwsh -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion entorno
#   pwsh -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion build
#   pwsh -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion flash
#   pwsh -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion build-perf
#   pwsh -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion flash-perf
#   pwsh -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion medir -Salida plan_antigravity/mediciones/F6b_run3 -Fase F6b
#
# Motivo: en algunos terminales `python` no esta en el PATH y `export.ps1` no se carga por la politica
# de ejecucion. Este script fija el entorno de ESP-IDF el solo. Usalo siempre en lugar de idf.py suelto.

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('entorno', 'ui', 'build', 'flash', 'build-perf', 'flash-perf', 'medir')]
    [string]$Accion,
    [string]$Puerto = 'COM16',
    [string]$Salida = 'plan_antigravity/mediciones/captura',
    [string]$Fase = 'F6b',
    [int]$Timeout = 900
)

$ErrorActionPreference = 'Stop'
$Proyecto = Split-Path -Parent $PSScriptRoot
$env:IDF_PATH = 'C:\esp\v6.0.1\esp-idf'
$env:IDF_TOOLS_PATH = 'C:\Users\Keneth\.espressif'
$IdfPython = Join-Path $env:IDF_TOOLS_PATH 'python_env\idf6.0_py3.12_env\Scripts\python.exe'
if (-not (Test-Path $IdfPython)) { throw "No existe el Python de ESP-IDF: $IdfPython" }
# export.ps1 invoca `python` durante su inicialización; publíquese antes de cargarlo.
$env:Path = "$(Split-Path -Parent $IdfPython);$env:Path"

Set-Location $Proyecto
. (Join-Path $env:IDF_PATH 'export.ps1') | Out-Null

function Invoke-Idf([string[]]$Argumentos) {
    & idf.py @Argumentos
    if ($LASTEXITCODE -ne 0) { throw "idf.py $($Argumentos -join ' ') fallo con codigo $LASTEXITCODE" }
}

switch ($Accion) {
    'entorno' {
        "IDF_PATH=$env:IDF_PATH"
        & $IdfPython --version
        Invoke-Idf @('--version')
        'OK: entorno listo'
    }
    'ui' {
        # Genera main/ui desde el proyecto EEZ sin abrir la ventana (equivale a pulsar «Build» en EEZ Studio)
        $eez = 'C:\Users\Keneth\AppData\Local\Programs\eezstudio\EEZ Studio.exe'
        if (-not (Test-Path $eez)) { throw "No existe EEZ Studio: $eez" }
        $proy = Join-Path $Proyecto 'video_player\video_player.eez-project'
        if (-not (Test-Path $proy)) { throw "No existe el proyecto EEZ: $proy" }
        # La salida va a un fichero: si el proceso que llama cierra la consola, EEZ se cae con
        # "EPIPE: broken pipe" y muestra un dialogo de error. Con el fichero no puede pasar.
        $log = Join-Path $env:TEMP 'eez_build.log'
        $p = Start-Process -FilePath $eez -ArgumentList "--build-project `"$proy`"" `
            -RedirectStandardOutput $log -RedirectStandardError "$log.err" -PassThru -Wait -WindowStyle Hidden
        $salida = (Get-Content $log -ErrorAction SilentlyContinue) -join "`n"
        $salida
        if ($p.ExitCode -ne 0 -or $salida -notmatch 'Build successfully finished') {
            throw "El Build de EEZ fallo (codigo $($p.ExitCode)). Revisa $log y $log.err"
        }
        'OK: main/ui regenerado desde EEZ'
    }
    'build' { Invoke-Idf @('build'); 'OK: build' }
    'flash' { Invoke-Idf @('-p', $Puerto, 'build', 'flash'); 'OK: firmware normal flasheado' }
    'build-perf' {
        Invoke-Idf @('-B', 'build_perf', '-D', 'SDKCONFIG=sdkconfig.perf',
            '-D', 'SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.perf.defaults', 'build')
        'OK: build de autoprueba'
    }
    'flash-perf' { Invoke-Idf @('-B', 'build_perf', '-p', $Puerto, 'flash'); 'OK: autoprueba flasheada' }
    'medir' {
        & $IdfPython 'tools/perf_capture.py' '--port' $Puerto '--out' $Salida '--phase' $Fase '--timeout' $Timeout
        "perf_capture exit=$LASTEXITCODE"
    }
}
