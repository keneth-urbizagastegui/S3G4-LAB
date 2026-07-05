import React, { useState } from 'react';
import type { Telemetry } from '../services/MockDataEngine';

interface MainMenuProps {
  connectionMode: 'demo' | 'serial' | 'websocket';
  setConnectionMode: (mode: 'demo' | 'serial' | 'websocket') => void;
  connected: boolean;
  onConnect: (ip?: string) => void;
  onDisconnect: () => void;
  onOpenInstrument: (screen: 'scope' | 'multimeter') => void;
  fps: number;
  telemetry: Telemetry | null;
}

export const MainMenu: React.FC<MainMenuProps> = ({
  connectionMode,
  setConnectionMode,
  connected,
  onConnect,
  onDisconnect,
  onOpenInstrument,
  fps,
  telemetry,
}) => {
  const [ip, setIp] = useState('192.168.4.1');

  return (
    <div className="flex flex-col gap-4 w-full h-full overflow-y-auto pr-1 select-none">
      
      {/* HEADER PRINCIPAL */}
      <div className="flex justify-between items-center border-b pb-3 mb-1" style={{ borderColor: 'rgba(255, 255, 255, 0.08)' }}>
        <div>
          <h1 className="text-2xl font-black tracking-wider font-mono">
            ⚡ S3G4_<span style={{ color: 'var(--ch1-color)' }}>SCOPE</span> SYSTEM
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Embedded Oscilloscope, Multimeter & DDS Function Generator Suite
          </p>
        </div>
        <div className="text-right text-[10px] text-slate-500">
          Uptime: <strong className="text-slate-300">Live</strong> | Link: <strong className="text-slate-300">{connectionMode.toUpperCase()}</strong>
        </div>
      </div>

      {/* CONTENEDOR DE DOS COLUMNAS ESTILO EMBO */}
      <div 
        className="grid gap-4 w-full"
        style={{
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          alignItems: 'start'
        }}
      >
        
        {/* COLUMNA IZQUIERDA: CONEXIÓN Y SELECCIÓN DE PUERTO */}
        <div className="glass-panel flex flex-col gap-4 h-full">
          <div>
            <h2 className="text-sm font-bold tracking-wider text-slate-300 mb-1">🔗 CONNECTION SETTINGS</h2>
            <p className="text-[10px] text-slate-400">Select communication interface and start link.</p>
          </div>

          {/* Selector de Modo */}
          <div className="flex flex-col gap-1.5 mt-2">
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Link Interface:</span>
            <div className="flex bg-slate-950 p-1 rounded-lg border border-white/5 w-full">
              <button
                onClick={() => { if (!connected) setConnectionMode('demo'); }}
                disabled={connected}
                className="flex-1 py-2 rounded-md font-bold text-xs cursor-pointer transition-all border-none"
                style={{
                  backgroundColor: connectionMode === 'demo' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                  color: connectionMode === 'demo' ? '#ffffff' : '#64748b',
                  opacity: connected ? 0.5 : 1
                }}
              >
                Demo Mode
              </button>
              <button
                onClick={() => { if (!connected) setConnectionMode('serial'); }}
                disabled={connected}
                className="flex-1 py-2 rounded-md font-bold text-xs cursor-pointer transition-all border-none"
                style={{
                  backgroundColor: connectionMode === 'serial' ? 'var(--ch1-color)' : 'transparent',
                  color: connectionMode === 'serial' ? '#070a13' : '#64748b',
                  opacity: connected ? 0.5 : 1
                }}
              >
                USB Serial
              </button>
              <button
                onClick={() => { if (!connected) setConnectionMode('websocket'); }}
                disabled={connected}
                className="flex-1 py-2 rounded-md font-bold text-xs cursor-pointer transition-all border-none"
                style={{
                  backgroundColor: connectionMode === 'websocket' ? 'var(--multimeter-color)' : 'transparent',
                  color: connectionMode === 'websocket' ? '#ffffff' : '#64748b',
                  opacity: connected ? 0.5 : 1
                }}
              >
                Wi-Fi WS
              </button>
            </div>
          </div>

          {/* Parámetros Dinámicos del puerto */}
          <div className="flex flex-col gap-3 p-3 rounded-lg bg-slate-950/40 border border-white/5 text-xs">
            {connectionMode === 'serial' && (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-400">Port / COM:</span>
                  <span className="font-bold text-white">USB Serial Port (CDC)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Baudrate:</span>
                  <span className="font-mono text-white">921,600 bps</span>
                </div>
              </>
            )}

            {connectionMode === 'websocket' && (
              <div className="flex flex-col gap-2">
                <span className="text-slate-400">Server IP Address:</span>
                <input
                  type="text"
                  value={ip}
                  onChange={(e) => setIp(e.target.value)}
                  disabled={connected}
                  className="w-full bg-slate-950 border border-white/10 text-white font-mono rounded-lg p-2 text-xs outline-none"
                  placeholder="ESP32 IP Address"
                />
              </div>
            )}

            {connectionMode === 'demo' && (
              <div className="flex flex-col gap-1 text-slate-400 italic text-[11px] leading-relaxed">
                💡 <strong>Demo Mode:</strong> Offline real-time signals engine simulation. No physical hardware connection required.
              </div>
            )}

            <div className="flex justify-between border-t border-white/5 pt-2 mt-1">
              <span className="text-slate-400">Status:</span>
              <div className="flex items-center gap-1.5">
                <div 
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: connected ? '#10b981' : '#ef4444',
                    boxShadow: connected ? '0 0 6px #10b981' : '0 0 6px #ef4444',
                  }}
                />
                <strong className={connected ? 'text-emerald-400' : 'text-red-400'}>
                  {connected ? 'CONNECTED' : 'DISCONNECTED'}
                </strong>
              </div>
            </div>
          </div>

          {/* Botón de Conectar / Desconectar */}
          {connected ? (
            <button
              onClick={onDisconnect}
              className="w-full py-2.5 rounded-lg border font-bold text-sm cursor-pointer transition-all bg-red-600 border-red-500 hover:bg-red-500 text-white"
            >
              DISCONNECT LINK
            </button>
          ) : (
            <button
              onClick={() => onConnect(connectionMode === 'websocket' ? ip : undefined)}
              className="w-full py-2.5 rounded-lg border font-bold text-sm cursor-pointer transition-all"
              style={{
                backgroundColor: connectionMode === 'demo' 
                  ? 'rgba(255,255,255,0.1)' 
                  : connectionMode === 'serial' 
                    ? 'var(--ch1-color)' 
                    : 'var(--multimeter-color)',
                borderColor: connectionMode === 'demo' 
                  ? 'rgba(255,255,255,0.2)' 
                  : connectionMode === 'serial' 
                    ? 'var(--ch1-color)' 
                    : 'var(--multimeter-color)',
                color: connectionMode === 'websocket' ? '#ffffff' : '#070a13',
              }}
            >
              ESTABLISH CONNECTION
            </button>
          )}

          {/* Refresh FPS */}
          {connected && (
            <div className="flex justify-between items-center text-[10px] text-slate-500 mt-2 px-1">
              <span>Streaming Refreshrate:</span>
              <span><strong className="text-slate-300">{fps} FPS</strong></span>
            </div>
          )}
        </div>

        {/* COLUMNA DERECHA: PANELES DE DISPOSITIVOS Y TELEMETRÍA */}
        <div className="flex flex-col gap-4">
          
          {/* CARD 1: INFORMACIÓN DEL HARDWARE */}
          <div className="glass-panel p-3 flex flex-col gap-2 bg-slate-900/20" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">📟 MCU & FIRMWARE INFO</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <div className="text-[9px] text-slate-500 font-semibold uppercase">Microcontroller</div>
                <div className="font-bold text-white mt-0.5">STM32G473VET6</div>
              </div>
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <div className="text-[9px] text-slate-500 font-semibold uppercase">Communication Hub</div>
                <div className="font-bold text-white mt-0.5">ESP32-S3 Dual Core</div>
              </div>
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <div className="text-[9px] text-slate-500 font-semibold uppercase">Firmware version</div>
                <div className="font-mono text-emerald-400 font-bold mt-0.5">v1.0.4 (Bare-Metal)</div>
              </div>
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <div className="text-[9px] text-slate-500 font-semibold uppercase">Vcc Voltage</div>
                <div className="font-bold text-white mt-0.5">
                  {connected && telemetry ? '3335 mV' : '--- mV'}
                </div>
              </div>
            </div>
          </div>

          {/* CARD 2: DISPOSITIVOS PRINCIPALES (PRIMARY DEVICES) */}
          <div className="glass-panel p-4 flex flex-col gap-3">
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-300">📊 PRIMARY INSTRUMENTS</h3>
            
            {/* Instrumento 1: Osciloscopio */}
            <div className="border border-white/5 rounded-xl p-3 bg-slate-950/40 flex justify-between items-center gap-4 hover:border-white/10 transition-colors">
              <div>
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span className="text-cyan-400">📊</span> DIGITAL OSCILLOSCOPE + DDS
                </h4>
                <div className="grid grid-cols-3 gap-x-4 gap-y-1 text-[9px] text-slate-500 mt-2 font-mono">
                  <span>Fs: <strong>1 MSps</strong></span>
                  <span>Mem: <strong>512 S</strong></span>
                  <span>Bits: <strong>12-bit</strong></span>
                  <span>Chs: <strong>4 Analog</strong></span>
                  <span>PGA: <strong>X2-X64</strong></span>
                  <span>DDS: <strong>2 Chs</strong></span>
                </div>
              </div>
              <button
                onClick={() => onOpenInstrument('scope')}
                disabled={!connected}
                className="py-2 px-4 rounded-lg font-bold text-xs cursor-pointer border transition-all text-nowrap flex items-center justify-center gap-1"
                style={{
                  backgroundColor: connected ? 'rgba(0, 240, 255, 0.1)' : 'rgba(15, 23, 42, 0.4)',
                  borderColor: connected ? 'var(--ch1-color)' : 'rgba(255, 255, 255, 0.1)',
                  color: connected ? 'var(--ch1-color)' : '#64748b',
                  cursor: connected ? 'pointer' : 'not-allowed',
                  boxShadow: connected ? '0 0 10px rgba(0, 240, 255, 0.15)' : 'none',
                }}
              >
                OPEN OSC
              </button>
            </div>

            {/* Instrumento 2: Multímetro */}
            <div className="border border-white/5 rounded-xl p-3 bg-slate-950/40 flex justify-between items-center gap-4 hover:border-white/10 transition-colors">
              <div>
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span className="text-purple-400">📟</span> DIGITAL MULTIMETER (DMM)
                </h4>
                <div className="grid grid-cols-3 gap-x-4 gap-y-1 text-[9px] text-slate-500 mt-2 font-mono">
                  <span>DC V: <strong>0 - 3.3V</strong></span>
                  <span>Resist: <strong>1M Ω</strong></span>
                  <span>Cap: <strong>100 uF</strong></span>
                  <span>Fs: <strong>100 Sps</strong></span>
                  <span>NPLC: <strong>0.5 - 10</strong></span>
                  <span>State: <strong>Mocked</strong></span>
                </div>
              </div>
              <button
                onClick={() => onOpenInstrument('multimeter')}
                disabled={!connected}
                className="py-2 px-4 rounded-lg font-bold text-xs cursor-pointer border transition-all text-nowrap flex items-center justify-center gap-1"
                style={{
                  backgroundColor: connected ? 'rgba(168, 85, 247, 0.1)' : 'rgba(15, 23, 42, 0.4)',
                  borderColor: connected ? 'var(--multimeter-color)' : 'rgba(255, 255, 255, 0.1)',
                  color: connected ? 'var(--multimeter-color)' : '#64748b',
                  cursor: connected ? 'pointer' : 'not-allowed',
                  boxShadow: connected ? '0 0 10px rgba(168, 85, 247, 0.15)' : 'none',
                }}
              >
                OPEN DMM
              </button>
            </div>
          </div>

          {/* CARD 3: DISPOSITIVOS SECUNDARIOS (SECONDARY DEVICES - MOCKED READONLY) */}
          <div className="glass-panel p-3 flex flex-col gap-2 bg-slate-900/20" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">📐 SECONDARY DEVICES</h3>
            <div className="grid grid-cols-3 gap-2 text-[10px]">
              {/* PWM */}
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <span className="text-[8px] text-slate-500 font-bold uppercase">PWM Generator</span>
                <div className="text-white font-semibold mt-1">2 Channels</div>
                <div className="text-[8px] text-slate-500 mt-0.5">1 Hz - 20 MHz</div>
              </div>
              {/* Counter */}
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <span className="text-[8px] text-slate-500 font-bold uppercase">Freq Counter</span>
                <div className="text-white font-semibold mt-1">0.1Hz - 10MHz</div>
                <div className="text-[8px] text-slate-500 mt-0.5">High precision</div>
              </div>
              {/* Voltmeter logger */}
              <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
                <span className="text-[8px] text-slate-500 font-bold uppercase">Datalogger</span>
                <div className="text-white font-semibold mt-1">100 Sps</div>
                <div className="text-[8px] text-slate-500 mt-0.5">Continuous CSV</div>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default MainMenu;
