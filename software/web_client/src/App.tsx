import React, { useState, useEffect, useRef } from 'react';
import { ConnectionBar } from './components/ConnectionBar';
import { MainMenu } from './components/MainMenu';
import { OscilloscopeCanvas } from './components/OscilloscopeCanvas';
import { MeasurementsBar } from './components/MeasurementsBar';
import { ControlPanel } from './components/ControlPanel';
import { GeneratorPanel } from './components/GeneratorPanel';
import { MultimeterPanel } from './components/MultimeterPanel';
import { MockDataEngine } from './services/MockDataEngine';
import type { ScopeData, Telemetry } from './services/MockDataEngine';
import { useWebSerial } from './hooks/useWebSerial';
import { useWebSockets } from './hooks/useWebSockets';

// Command Constants (matching STM32 firmware)
const CMD_SCOPE_START = 0x01;
const CMD_SCOPE_STOP = 0x02;
const CMD_SCOPE_CONFIG_HORIZ = 0x03;
const CMD_SCOPE_CONFIG_VERT = 0x04;
const CMD_SCOPE_CONFIG_TRIG = 0x05;

const CMD_WAVEGEN_START = 0x11;
const CMD_WAVEGEN_STOP = 0x12;
const CMD_WAVEGEN_CONFIG_HORIZ = 0x13;
const CMD_WAVEGEN_CONFIG_VERT = 0x14;

export const App: React.FC = () => {
  // Screens: 'menu' | 'scope' | 'multimeter'
  const [currentScreen, setCurrentScreen] = useState<'menu' | 'scope' | 'multimeter'>('menu');

  // Connection State
  const [connectionMode, setConnectionMode] = useState<'demo' | 'serial' | 'websocket'>('demo');
  const [connected, setConnected] = useState(false);
  const [fps, setFps] = useState(0);
  const [scopeData, setScopeData] = useState<ScopeData | null>(null);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);

  // Run State
  const [running, setRunningState] = useState(true);

  // Cursors State
  const [cursorsVEnabled, setCursorsVEnabled] = useState(false);
  const [cursorsHEnabled, setCursorsHEnabled] = useState(false);
  const [cursorV1, setCursorV1] = useState(0.25);
  const [cursorV2, setCursorV2] = useState(0.75);
  const [cursorH1, setCursorH1] = useState(0.25);
  const [cursorH2, setCursorH2] = useState(0.75);

  // Zoom Mode
  const [zoomMode, setZoomMode] = useState<'H' | 'V'>('H');

  // Utilities State
  const [average, setAverage] = useState(1); // 1 = OFF
  const [adcBits, setAdcBits] = useState(12); // 8 or 12
  const [fftEnabled, setFftEnabled] = useState(false);

  // Horizontal Auto Mode
  const [horizAutoMode, setHorizAutoMode] = useState(false);

  // Oscilloscope Settings State
  const [activeChannel, setActiveChannel] = useState(0);
  const [chEnabled, setChEnabledState] = useState<boolean[]>([true, false, false, false]);
  const [gains, setGainsState] = useState<number[]>([0, 0, 0, 0]); // Index 0-5 (X2 to X64)
  const [offsets, setOffsetsState] = useState<number[]>([127, 127, 127, 127]); // 0-255 (Center ground)
  const [couplings, setCouplingsState] = useState<string[]>(['DC', 'DC', 'DC', 'DC']);
  const [timebase, setTimebaseState] = useState(100); // kHz
  const [horizOffset, setHorizOffsetState] = useState(0);

  // Trigger Settings State
  const [triggerLevel, setTriggerLevelState] = useState(2048); // 0-4095
  const [triggerChannel, setTriggerChannelState] = useState(0); // CH1-CH4
  const [triggerSlope, setTriggerSlopeState] = useState(0); // 0=Rising, 1=Falling
  const [triggerMode, setTriggerModeState] = useState(0); // 0=Auto, 1=Normal, 2=Single
  const [triggerEnabled, setTriggerEnabledState] = useState(true);

  // Generator Settings State
  const [genEnabled, setGenEnabledState] = useState<boolean[]>([false, false]);
  const [genTypes, setGenTypesState] = useState<number[]>([0, 0]); // 0=Sine, etc.
  const [genFreqs, setGenFreqsState] = useState<number[]>([1000, 1000]); // 1 kHz
  const [genAmps, setGenAmpsState] = useState<number[]>([2000, 2000]); // 2.0 Vpp in mV

  // Mock Engine Ref
  const mockEngineRef = useRef<MockDataEngine>(new MockDataEngine());
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(performance.now());
  const animationFrameIdRef = useRef<number | null>(null);

  // Data Callback
  const handleIncomingData = (data: ScopeData) => {
    setScopeData(data);
    setTelemetry(data.telemetry);
    frameCountRef.current++;
  };

  // Drivers
  const serial = useWebSerial(handleIncomingData);
  const ws = useWebSockets(handleIncomingData);

  // Activa la conectividad según modo
  const handleConnect = async (ip?: string) => {
    if (connectionMode === 'demo') {
      setConnected(true);
    } else if (connectionMode === 'serial') {
      const ok = await serial.connectSerial();
      if (ok) {
        setConnected(true);
        // Enviar configuraciones iniciales
        setTimeout(() => syncInitialSettings('serial'), 500);
      }
    } else if (connectionMode === 'websocket' && ip) {
      const ok = ws.connectWebSocket(ip);
      if (ok) {
        setConnected(true);
        setTimeout(() => syncInitialSettings('websocket'), 500);
      }
    }
  };

  const handleDisconnect = () => {
    if (connectionMode === 'demo') {
      setConnected(false);
      setScopeData(null);
      setTelemetry(null);
    } else if (connectionMode === 'serial') {
      serial.sendCommand(CMD_SCOPE_STOP, 0, 0);
      serial.disconnectSerial();
      setConnected(false);
    } else if (connectionMode === 'websocket') {
      ws.sendCommand(CMD_SCOPE_STOP, 0, 0);
      ws.disconnectWebSocket();
      setConnected(false);
    }
    setCurrentScreen('menu'); // Retornar automáticamente al portal inicial
  };

  // Sincronizar todos los ajustes actuales con el hardware
  const syncInitialSettings = (mode: 'serial' | 'websocket') => {
    const send = mode === 'serial' ? serial.sendCommand : ws.sendCommand;
    
    // Iniciar/Detener osciloscopio según estado run
    if (running) {
      send(CMD_SCOPE_START, 1, 0); // 1 = Continuo
    } else {
      send(CMD_SCOPE_STOP, 0, 0);
    }

    // Sincronizar Horiz
    send(CMD_SCOPE_CONFIG_HORIZ, 0, (timebase << 16) | (horizOffset & 0xFFFF));

    // Sincronizar Verticales
    chEnabled.forEach((en, i) => {
      const pData = (offsets[i] << 16) | (gains[i] << 8) | (en ? 1 : 0);
      send(CMD_SCOPE_CONFIG_VERT, i, pData);
    });

    // Sincronizar Trigger
    send(CMD_SCOPE_CONFIG_TRIG, triggerChannel, (triggerLevel << 16) | (triggerSlope << 8) | triggerMode);

    // Sincronizar Generadores
    genEnabled.forEach((en, i) => {
      if (en) {
        send(CMD_WAVEGEN_CONFIG_HORIZ, i, genFreqs[i]);
        send(CMD_WAVEGEN_CONFIG_VERT, i, (genAmps[i] << 16) | (genTypes[i] & 0xFF));
        send(CMD_WAVEGEN_START, i, 0);
      } else {
        send(CMD_WAVEGEN_STOP, i, 0);
      }
    });
  };

  // Wrapper para enviar comandos
  const sendCmd = (cmdId: number, param1: number, dataVal: number) => {
    if (!connected) return;
    if (connectionMode === 'serial') {
      serial.sendCommand(cmdId, param1, dataVal);
    } else if (connectionMode === 'websocket') {
      ws.sendCommand(cmdId, param1, dataVal);
    }
  };

  // Setters que sincronizan automáticamente con el hardware
  const setChEnabled = (ch: number, val: boolean) => {
    const updated = [...chEnabled];
    updated[ch] = val;
    setChEnabledState(updated);
    
    const pData = (offsets[ch] << 16) | (gains[ch] << 8) | (val ? 1 : 0);
    sendCmd(CMD_SCOPE_CONFIG_VERT, ch, pData);
  };

  const setGain = (ch: number, val: number) => {
    const updated = [...gains];
    updated[ch] = val;
    setGainsState(updated);

    const pData = (offsets[ch] << 16) | (val << 8) | (chEnabled[ch] ? 1 : 0);
    sendCmd(CMD_SCOPE_CONFIG_VERT, ch, pData);
  };

  const setOffset = (ch: number, val: number) => {
    const updated = [...offsets];
    updated[ch] = val;
    setOffsetsState(updated);

    const pData = (val << 16) | (gains[ch] << 8) | (chEnabled[ch] ? 1 : 0);
    sendCmd(CMD_SCOPE_CONFIG_VERT, ch, pData);
  };

  const setCoupling = (ch: number, val: string) => {
    const updated = [...couplings];
    updated[ch] = val;
    setCouplingsState(updated);
  };

  const setTimebase = (val: number) => {
    setTimebaseState(val);
    sendCmd(CMD_SCOPE_CONFIG_HORIZ, 0, (val << 16) | (horizOffset & 0xFFFF));
  };

  const setHorizOffset = (val: number) => {
    setHorizOffsetState(val);
    sendCmd(CMD_SCOPE_CONFIG_HORIZ, 0, (timebase << 16) | (val & 0xFFFF));
  };

  const setTriggerLevel = (val: number) => {
    setTriggerLevelState(val);
    sendCmd(CMD_SCOPE_CONFIG_TRIG, triggerChannel, (val << 16) | (triggerSlope << 8) | triggerMode);
  };

  const setTriggerChannel = (val: number) => {
    setTriggerChannelState(val);
    sendCmd(CMD_SCOPE_CONFIG_TRIG, val, (triggerLevel << 16) | (triggerSlope << 8) | triggerMode);
  };

  const setTriggerSlope = (val: number) => {
    setTriggerSlopeState(val);
    sendCmd(CMD_SCOPE_CONFIG_TRIG, triggerChannel, (triggerLevel << 16) | (val << 8) | triggerMode);
  };

  const setTriggerMode = (val: number) => {
    setTriggerModeState(val);
    sendCmd(CMD_SCOPE_CONFIG_TRIG, triggerChannel, (triggerLevel << 16) | (triggerSlope << 8) | val);
  };

  const setTriggerEnabled = (val: boolean) => {
    setTriggerEnabledState(val);
  };

  const setGenEnabled = (ch: number, val: boolean) => {
    const updated = [...genEnabled];
    updated[ch] = val;
    setGenEnabledState(updated);

    if (val) {
      sendCmd(CMD_WAVEGEN_CONFIG_HORIZ, ch, genFreqs[ch]);
      sendCmd(CMD_WAVEGEN_CONFIG_VERT, ch, (genAmps[ch] << 16) | (genTypes[ch] & 0xFF));
      sendCmd(CMD_WAVEGEN_START, ch, 0);
    } else {
      sendCmd(CMD_WAVEGEN_STOP, ch, 0);
    }
  };

  const setGenType = (ch: number, val: number) => {
    const updated = [...genTypes];
    updated[ch] = val;
    setGenTypesState(updated);
    
    if (genEnabled[ch]) {
      sendCmd(CMD_WAVEGEN_CONFIG_VERT, ch, (genAmps[ch] << 16) | (val & 0xFF));
    }
  };

  const setGenFreq = (ch: number, val: number) => {
    const updated = [...genFreqs];
    updated[ch] = val;
    setGenFreqsState(updated);

    if (genEnabled[ch]) {
      sendCmd(CMD_WAVEGEN_CONFIG_HORIZ, ch, val);
    }
  };

  const setGenAmp = (ch: number, val: number) => {
    const updated = [...genAmps];
    updated[ch] = val;
    setGenAmpsState(updated);

    if (genEnabled[ch]) {
      sendCmd(CMD_WAVEGEN_CONFIG_VERT, ch, (val << 16) | (genTypes[ch] & 0xFF));
    }
  };

  // Wrapper for run state
  const setRunning = (val: boolean) => {
    setRunningState(val);
    if (connected) {
      if (val) {
        sendCmd(CMD_SCOPE_START, 1, 0);
      } else {
        sendCmd(CMD_SCOPE_STOP, 0, 0);
      }
    }
  };

  // Single trigger shot helper
  const handleSingle = () => {
    setTriggerModeState(2); // 2 = Single
    setRunningState(true);
    if (connected) {
      sendCmd(CMD_SCOPE_CONFIG_TRIG, triggerChannel, (triggerLevel << 16) | (triggerSlope << 8) | 2);
      sendCmd(CMD_SCOPE_START, 1, 0);
    }
  };

  // Reset offset and zoom settings
  const handleResetZoom = () => {
    setHorizOffsetState(0);
    setTimebaseState(100);
    const defaultOffsets = [127, 127, 127, 127];
    const defaultGains = [0, 0, 0, 0];
    setOffsetsState(defaultOffsets);
    setGainsState(defaultGains);
    setCursorV1(0.25);
    setCursorV2(0.75);
    setCursorH1(0.25);
    setCursorH2(0.75);

    if (connected) {
      sendCmd(CMD_SCOPE_CONFIG_HORIZ, 0, (100 << 16) | 0);
      defaultOffsets.forEach((off, i) => {
        const pData = (off << 16) | (defaultGains[i] << 8) | (chEnabled[i] ? 1 : 0);
        sendCmd(CMD_SCOPE_CONFIG_VERT, i, pData);
      });
    }
  };

  // Loop de datos de simulación (Demo Mode)
  useEffect(() => {
    if (connectionMode !== 'demo' || !connected || !running) {
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
      return;
    }

    const renderLoop = () => {
      const simulatedData = mockEngineRef.current.generateData(
        chEnabled[0], chEnabled[1], chEnabled[2], chEnabled[3],
        gains,
        timebase,
        triggerChannel,
        genTypes[0],
        genFreqs[0],
        genAmps[0]
      );

      handleIncomingData(simulatedData);
      animationFrameIdRef.current = requestAnimationFrame(renderLoop);
    };

    renderLoop();

    return () => {
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
    };
  }, [connectionMode, connected, running, chEnabled, gains, timebase, triggerChannel, genTypes, genFreqs, genAmps]);

  // Medidor de FPS
  useEffect(() => {
    const calculateFps = () => {
      const now = performance.now();
      const elapsed = now - lastFpsTimeRef.current;
      
      const currentFps = Math.round((frameCountRef.current * 1000) / elapsed);
      setFps(currentFps);

      frameCountRef.current = 0;
      lastFpsTimeRef.current = now;
    };

    const fpsInterval = setInterval(calculateFps, 1000);
    return () => clearInterval(fpsInterval);
  }, []);

  return (
    <div className="app-container">
      {currentScreen === 'menu' ? (
        <MainMenu
          connectionMode={connectionMode}
          setConnectionMode={setConnectionMode}
          connected={connected}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
          onOpenInstrument={(screen) => setCurrentScreen(screen)}
          fps={fps}
          telemetry={telemetry}
        />
      ) : (
        <>
          {/* Cabecera Principal / Telemetría */}
          <ConnectionBar
            connectionMode={connectionMode}
            setConnectionMode={setConnectionMode}
            connected={connected}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            telemetry={telemetry}
            fps={fps}
          />

          {/* Botón de Retorno */}
          <div className="flex justify-start">
            <button
              className="px-4 py-2 rounded-lg font-bold text-xs cursor-pointer border bg-slate-950/60 border-white/10 text-slate-300 hover:text-white hover:border-white/20 transition-all flex items-center gap-1.5"
              onClick={() => setCurrentScreen('menu')}
            >
              ◀ BACK TO MAIN MENU
            </button>
          </div>

          {/* Grid del Dashboard Fullscreen */}
          <div className="instrument-container">
            {currentScreen === 'scope' ? (
              <>
                {/* Columna Izquierda: El Gráfico del Osciloscopio Canvas y el Generador DDS */}
                <div className="left-column">
                  <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <OscilloscopeCanvas
                      data={scopeData}
                      ch1Enabled={chEnabled[0]}
                      ch2Enabled={chEnabled[1]}
                      ch3Enabled={chEnabled[2]}
                      ch4Enabled={chEnabled[3]}
                      offsets={offsets}
                      triggerLevel={triggerLevel}
                      triggerChannel={triggerChannel}
                      triggerEnabled={triggerEnabled}
                      // Cursors
                      activeChannel={activeChannel}
                      gains={gains}
                      timebase={timebase}
                      cursorsVEnabled={cursorsVEnabled}
                      cursorsHEnabled={cursorsHEnabled}
                      cursorV1={cursorV1}
                      setCursorV1={setCursorV1}
                      cursorV2={cursorV2}
                      setCursorV2={setCursorV2}
                      cursorH1={cursorH1}
                      setCursorH1={setCursorH1}
                      cursorH2={cursorH2}
                      setCursorH2={setCursorH2}
                      fftEnabled={fftEnabled}
                    />
                    <MeasurementsBar
                      data={scopeData}
                      activeChannel={activeChannel}
                      gains={gains}
                      cursorsVEnabled={cursorsVEnabled}
                      setCursorsVEnabled={setCursorsVEnabled}
                      cursorsHEnabled={cursorsHEnabled}
                      setCursorsHEnabled={setCursorsHEnabled}
                      vcc={telemetry ? 3335 : 0}
                      samplingTimeNs={125}
                      sequenceNumber={telemetry ? 4507 : 0}
                    />
                  </div>
                  <div style={{ flexShrink: 0 }}>
                    <GeneratorPanel
                      genEnabled={genEnabled}
                      setGenEnabled={setGenEnabled}
                      genTypes={genTypes}
                      setGenType={setGenType}
                      genFreqs={genFreqs}
                      setGenFreq={setGenFreq}
                      genAmps={genAmps}
                      setGenAmp={setGenAmp}
                    />
                  </div>
                </div>

                {/* Columna Derecha: Panel de Control del Osciloscopio */}
                <div className="right-column">
                  <ControlPanel
                    running={running}
                    setRunning={setRunning}
                    onSingle={handleSingle}
                    onResetZoom={handleResetZoom}
                    zoomMode={zoomMode}
                    setZoomMode={setZoomMode}
                    activeChannel={activeChannel}
                    setActiveChannel={setActiveChannel}
                    chEnabled={chEnabled}
                    setChEnabled={setChEnabled}
                    gains={gains}
                    setGain={setGain}
                    offsets={offsets}
                    setOffset={setOffset}
                    couplings={couplings}
                    setCoupling={setCoupling}
                    timebase={timebase}
                    setTimebase={setTimebase}
                    horizOffset={horizOffset}
                    setHorizOffset={setHorizOffset}
                    horizAutoMode={horizAutoMode}
                    setHorizAutoMode={setHorizAutoMode}
                    triggerLevel={triggerLevel}
                    setTriggerLevel={setTriggerLevel}
                    triggerChannel={triggerChannel}
                    setTriggerChannel={setTriggerChannel}
                    triggerSlope={triggerSlope}
                    setTriggerSlope={setTriggerSlope}
                    triggerMode={triggerMode}
                    setTriggerMode={setTriggerMode}
                    triggerEnabled={triggerEnabled}
                    setTriggerEnabled={setTriggerEnabled}
                    average={average}
                    setAverage={setAverage}
                    adcBits={adcBits}
                    setAdcBits={setAdcBits}
                    fftEnabled={fftEnabled}
                    setFftEnabled={setFftEnabled}
                  />
                </div>
              </>
            ) : (
              <div className="left-column" style={{ overflowY: 'auto' }}>
                <MultimeterPanel demoMode={connected && connectionMode === 'demo'} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
export default App;
