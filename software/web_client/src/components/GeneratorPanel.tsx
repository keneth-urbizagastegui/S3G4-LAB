import React, { useState } from 'react';
import { Knob } from './Knob';

interface GeneratorPanelProps {
  genEnabled: boolean[];
  setGenEnabled: (ch: number, val: boolean) => void;
  genTypes: number[];
  setGenType: (ch: number, val: number) => void;
  genFreqs: number[];
  setGenFreq: (ch: number, val: number) => void;
  genAmps: number[];
  setGenAmp: (ch: number, val: number) => void;
}

const waveTypes = [
  { id: 0, name: 'Seno', icon: '🔊' },
  { id: 1, name: 'Cuadrada', icon: '⏹️' },
  { id: 2, name: 'Triángulo', icon: '🔺' },
  { id: 3, name: 'Diente Sierra', icon: '📈' },
  { id: 4, name: 'DC', icon: '➖' },
  { id: 5, name: 'PWM', icon: '➿' },
  { id: 6, name: 'Ruido', icon: '📻' },
];

export const GeneratorPanel: React.FC<GeneratorPanelProps> = ({
  genEnabled,
  setGenEnabled,
  genTypes,
  setGenType,
  genFreqs,
  setGenFreq,
  genAmps,
  setGenAmp,
}) => {
  const [activeGenCh, setActiveGenCh] = useState<number>(0);

  return (
    <div className="glass-panel" style={{ width: '100%' }}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold neon-gen">⚡ Generador DDS</h2>
        {/* Selector de canal del generador */}
        <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5" style={{ backgroundColor: 'rgba(5, 8, 18, 0.6)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '2px' }}>
          <button
            onClick={() => setActiveGenCh(0)}
            style={{
              padding: '4px 12px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '11px',
              fontWeight: 'bold',
              cursor: 'pointer',
              backgroundColor: activeGenCh === 0 ? 'var(--gen-color)' : 'transparent',
              color: activeGenCh === 0 ? '#070a13' : 'var(--text-secondary)',
              transition: 'all 0.2s',
            }}
          >
            GEN 1
          </button>
          <button
            onClick={() => setActiveGenCh(1)}
            style={{
              padding: '4px 12px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '11px',
              fontWeight: 'bold',
              cursor: 'pointer',
              backgroundColor: activeGenCh === 1 ? 'var(--gen-color)' : 'transparent',
              color: activeGenCh === 1 ? '#070a13' : 'var(--text-secondary)',
              transition: 'all 0.2s',
            }}
          >
            GEN 2
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-5">
        {/* Habilitar / Deshabilitar Salida */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-secondary" style={{ color: 'var(--text-secondary)' }}>Estado de la Salida:</span>
          <div
            className={`switch-container ${genEnabled[activeGenCh] ? 'active' : ''}`}
            onClick={() => setGenEnabled(activeGenCh, !genEnabled[activeGenCh])}
          >
            <div className="switch-track">
              <div 
                className="switch-thumb" 
                style={{ 
                  backgroundColor: genEnabled[activeGenCh] ? 'var(--gen-color)' : '#ffffff' 
                }} 
              />
            </div>
            <span className="text-xs font-semibold" style={{ minWidth: '24px', color: genEnabled[activeGenCh] ? 'var(--gen-color)' : 'inherit' }}>
              {genEnabled[activeGenCh] ? 'ACTIVE' : 'OFF'}
            </span>
          </div>
        </div>

        {/* Tipo de onda */}
        <div className="flex flex-col gap-2">
          <span className="text-xs text-secondary" style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Tipo de Onda:</span>
          <div className="grid grid-cols-4 gap-1.5">
            {waveTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setGenType(activeGenCh, type.id)}
                style={{
                  padding: '6px 4px',
                  borderRadius: '8px',
                  border: genTypes[activeGenCh] === type.id ? '1px solid var(--gen-color)' : '1px solid rgba(255,255,255,0.06)',
                  backgroundColor: genTypes[activeGenCh] === type.id ? 'rgba(255, 95, 0, 0.15)' : 'rgba(10, 15, 30, 0.4)',
                  color: genTypes[activeGenCh] === type.id ? 'var(--gen-color)' : 'var(--text-secondary)',
                  fontSize: '11px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.2s',
                }}
              >
                <span>{type.icon}</span>
                <span>{type.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Perillas del generador */}
        <div className="flex justify-around items-center mt-2">
          <Knob
            value={genFreqs[activeGenCh]}
            min={10}
            max={50000}
            step={10}
            onChange={(val) => setGenFreq(activeGenCh, val)}
            label="Frecuencia"
            unit=" Hz"
            color="var(--gen-color)"
            displayValue={genFreqs[activeGenCh] >= 1000 
              ? `${(genFreqs[activeGenCh] / 1000).toFixed(2)} kHz` 
              : `${genFreqs[activeGenCh]} Hz`}
          />

          <Knob
            value={genAmps[activeGenCh]}
            min={100}
            max={3300}
            step={50}
            onChange={(val) => setGenAmp(activeGenCh, val)}
            label="Amplitud Vpp"
            color="var(--gen-color)"
            displayValue={genAmps[activeGenCh] >= 1000 
              ? `${(genAmps[activeGenCh] / 1000).toFixed(2)} V` 
              : `${genAmps[activeGenCh]} mV`}
          />
        </div>
      </div>
    </div>
  );
};
export default GeneratorPanel;
