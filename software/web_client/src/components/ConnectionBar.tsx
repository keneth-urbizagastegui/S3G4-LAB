import React, { useState } from 'react';
import type { Telemetry } from '../services/MockDataEngine';

interface ConnectionBarProps {
  connectionMode: 'demo' | 'serial' | 'websocket';
  setConnectionMode: (mode: 'demo' | 'serial' | 'websocket') => void;
  connected: boolean;
  onConnect: (ip?: string) => void;
  onDisconnect: () => void;
  telemetry: Telemetry | null;
  fps: number;
}

export const ConnectionBar: React.FC<ConnectionBarProps> = ({
  connectionMode,
  setConnectionMode,
  connected,
  onConnect,
  onDisconnect,
  telemetry,
  fps,
}) => {
  const [ip, setIp] = useState('192.168.4.1'); // IP por defecto en modo AP del ESP32

  const formatFreq = (hz: number) => {
    if (hz === 0) return '---';
    if (hz >= 1000000) return `${(hz / 1000000).toFixed(3)} MHz`;
    if (hz >= 1000) return `${(hz / 1000).toFixed(2)} kHz`;
    return `${hz} Hz`;
  };

  const formatVoltage = (mv: number) => {
    if (mv === undefined || mv === null) return '---';
    if (mv >= 1000) return `${(mv / 1000).toFixed(2)} V`;
    return `${mv} mV`;
  };

  const formatDuty = (duty: number) => {
    if (duty === undefined || duty === null) return '---';
    return `${duty}%`;
  };

  return (
    <div className="glass-panel flex flex-col gap-4 w-full mb-5" style={{ borderRadius: '12px', padding: '16px' }}>
      {/* Sección Superior: Modos de Conectividad */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xl font-black tracking-wider" style={{ fontFamily: 'var(--font-mono)' }}>
            ⚡ S3G4_<span style={{ color: 'var(--ch1-color)' }}>SCOPE</span>
          </span>
          {/* LED de estado */}
          <div className="flex items-center gap-1.5 ml-2">
            <div 
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: connected ? '#10b981' : '#ef4444',
                boxShadow: connected ? '0 0 8px #10b981' : '0 0 8px #ef4444',
                transition: 'all 0.3s'
              }}
            />
            <span className="text-[10px] font-bold text-secondary" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
              {connected ? 'CONECTADO' : 'DESCONECTADO'}
            </span>
          </div>
        </div>

        {/* Botones de Selección de Modo */}
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5" style={{ backgroundColor: 'rgba(5, 8, 18, 0.6)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '2px' }}>
            <button
              onClick={() => { if (!connected) setConnectionMode('demo'); }}
              disabled={connected}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: connected ? 'not-allowed' : 'pointer',
                backgroundColor: connectionMode === 'demo' ? 'var(--text-primary)' : 'transparent',
                color: connectionMode === 'demo' ? '#070a13' : 'var(--text-secondary)',
                opacity: connected ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
            >
              Demo
            </button>
            <button
              onClick={() => { if (!connected) setConnectionMode('serial'); }}
              disabled={connected}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: connected ? 'not-allowed' : 'pointer',
                backgroundColor: connectionMode === 'serial' ? 'var(--ch1-color)' : 'transparent',
                color: connectionMode === 'serial' ? '#070a13' : 'var(--text-secondary)',
                opacity: connected ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
            >
              USB Serial
            </button>
            <button
              onClick={() => { if (!connected) setConnectionMode('websocket'); }}
              disabled={connected}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: connected ? 'not-allowed' : 'pointer',
                backgroundColor: connectionMode === 'websocket' ? 'var(--multimeter-color)' : 'transparent',
                color: connectionMode === 'websocket' ? '#f8fafc' : 'var(--text-secondary)',
                opacity: connected ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
            >
              Wi-Fi WS
            </button>
          </div>

          {/* Input IP para WebSocket */}
          {connectionMode === 'websocket' && (
            <input
              type="text"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              disabled={connected}
              placeholder="IP del ESP32"
              style={{
                backgroundColor: 'rgba(10, 15, 30, 0.8)',
                color: 'var(--text-primary)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: '6px 10px',
                borderRadius: '8px',
                fontSize: '12px',
                width: '120px',
                outline: 'none',
                opacity: connected ? 0.6 : 1,
              }}
            />
          )}

          {/* Botón Conectar / Desconectar */}
          {connected ? (
            <button
              onClick={onDisconnect}
              style={{
                padding: '6px 16px',
                borderRadius: '8px',
                border: 'none',
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'pointer',
                backgroundColor: '#ef4444',
                color: '#fff',
                transition: 'all 0.2s'
              }}
            >
              Desconectar
            </button>
          ) : (
            <button
              onClick={() => onConnect(connectionMode === 'websocket' ? ip : undefined)}
              style={{
                padding: '6px 16px',
                borderRadius: '8px',
                border: 'none',
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'pointer',
                backgroundColor: connectionMode === 'demo' 
                  ? 'rgba(255,255,255,0.15)' 
                  : connectionMode === 'serial' 
                    ? 'var(--ch1-color)' 
                    : 'var(--multimeter-color)',
                color: connectionMode === 'websocket' ? '#fff' : '#070a13',
                transition: 'all 0.2s'
              }}
            >
              Conectar
            </button>
          )}
        </div>
      </div>

      {/* Sección Inferior: Telemetría del Disparo / Señal en tiempo real */}
      <div 
        className="grid grid-cols-5 gap-3 mt-1.5 pt-3 border-t"
        style={{ borderColor: 'rgba(255,255,255,0.05)' }}
      >
        <div className="param-box">
          <span className="param-label">Frecuencia</span>
          <span className="param-value" style={{ color: 'var(--ch4-color)' }}>
            {telemetry ? formatFreq(telemetry.frequency) : '---'}
          </span>
        </div>
        <div className="param-box">
          <span className="param-label">Vpp (Pico-Pico)</span>
          <span className="param-value" style={{ color: 'var(--ch1-color)' }}>
            {telemetry ? formatVoltage(telemetry.vpp) : '---'}
          </span>
        </div>
        <div className="param-box">
          <span className="param-label">Vrms (Eficaz)</span>
          <span className="param-value" style={{ color: 'var(--ch2-color)' }}>
            {telemetry ? formatVoltage(telemetry.vrms) : '---'}
          </span>
        </div>
        <div className="param-box">
          <span className="param-label">Vavg (Medio)</span>
          <span className="param-value" style={{ color: 'var(--ch3-color)' }}>
            {telemetry ? formatVoltage(telemetry.vavg) : '---'}
          </span>
        </div>
        <div className="param-box">
          <span className="param-label">Ciclo Trabajo</span>
          <span className="param-value" style={{ color: 'var(--text-primary)' }}>
            {telemetry ? formatDuty(telemetry.dutyCycle) : '---'}
          </span>
        </div>
      </div>

      {/* FPS de dibujado */}
      <div className="flex justify-end text-[10px]" style={{ color: 'var(--text-muted)' }}>
        Tasa de Refresco: <span style={{ color: 'var(--text-secondary)', marginLeft: '4px', fontWeight: 'bold' }}>{fps} FPS</span>
      </div>
    </div>
  );
};
export default ConnectionBar;
