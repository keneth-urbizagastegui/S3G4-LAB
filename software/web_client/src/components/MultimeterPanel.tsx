import React, { useState, useEffect } from 'react';

interface MultimeterPanelProps {
  demoMode: boolean;
}

type MultiMode = 'DCV' | 'ACV' | 'RES' | 'CAP' | 'CONT';

export const MultimeterPanel: React.FC<MultimeterPanelProps> = ({ demoMode }) => {
  const [mode, setMode] = useState<MultiMode>('DCV');
  const [val, setVal] = useState<string>('0.000');

  useEffect(() => {
    if (!demoMode) {
      setVal('---.-');
      return;
    }

    const interval = setInterval(() => {
      let simulated = '';
      switch (mode) {
        case 'DCV':
          simulated = (3.25 + (Math.random() - 0.5) * 0.004).toFixed(4) + ' V';
          break;
        case 'ACV':
          simulated = (1.12 + (Math.random() - 0.5) * 0.008).toFixed(3) + ' Vrms';
          break;
        case 'RES':
          simulated = (982.4 + (Math.random() - 0.5) * 0.2).toFixed(1) + ' Ω';
          break;
        case 'CAP':
          simulated = (4.72 + (Math.random() - 0.5) * 0.02).toFixed(2) + ' μF';
          break;
        case 'CONT':
          simulated = Math.random() > 0.05 ? '0.2 Ω' : 'O.L';
          break;
      }
      setVal(simulated);
    }, 400);

    return () => clearInterval(interval);
  }, [mode, demoMode]);

  return (
    <div className="glass-panel" style={{ width: '100%', borderLeft: '3px solid var(--multimeter-color)' }}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold" style={{ color: 'var(--multimeter-color)', textShadow: '0 0 10px rgba(168, 85, 247, 0.3)' }}>
          📟 Multímetro Digital
        </h2>
        <span 
          className="text-xs font-semibold px-2 py-0.5 rounded" 
          style={{ 
            backgroundColor: demoMode ? 'rgba(168, 85, 247, 0.15)' : 'rgba(255,255,255,0.05)',
            color: demoMode ? 'var(--multimeter-color)' : 'var(--text-muted)'
          }}
        >
          {demoMode ? 'SIMULADO' : 'STANDBY'}
        </span>
      </div>

      {/* Pantalla digital de gran tamaño tipo LCD retroiluminada */}
      <div 
        className="flex items-center justify-end rounded-xl border p-4 mb-4"
        style={{
          backgroundColor: '#030712',
          borderColor: 'rgba(255,255,255,0.06)',
          height: '100px',
          boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.8)'
        }}
      >
        <div className="flex flex-col items-end">
          <span className="text-[10px]" style={{ color: 'var(--multimeter-color)', letterSpacing: '0.1em' }}>
            {mode === 'DCV' ? 'DC VOLTAGE' : mode === 'ACV' ? 'AC VOLTAGE (RMS)' : mode === 'RES' ? 'RESISTANCE' : mode === 'CAP' ? 'CAPACITANCE' : 'CONTINUITY'}
          </span>
          <span 
            style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: '32px', 
              fontWeight: 900,
              color: demoMode ? 'var(--multimeter-color)' : 'var(--text-muted)',
              textShadow: demoMode ? '0 0 15px rgba(168, 85, 247, 0.6)' : 'none'
            }}
          >
            {val}
          </span>
        </div>
      </div>

      {/* Selectores de modo */}
      <div className="grid grid-cols-5 gap-1.5 mb-5">
        {(['DCV', 'ACV', 'RES', 'CAP', 'CONT'] as MultiMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            style={{
              padding: '8px 2px',
              borderRadius: '8px',
              border: mode === m ? '1px solid var(--multimeter-color)' : '1px solid rgba(255,255,255,0.06)',
              backgroundColor: mode === m ? 'rgba(168, 85, 247, 0.15)' : 'rgba(10, 15, 30, 0.4)',
              color: mode === m ? 'var(--multimeter-color)' : 'var(--text-secondary)',
              fontSize: '11px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {m === 'CONT' ? '🔊' : m}
          </button>
        ))}
      </div>

      {/* Visualización de conectores banana en la base */}
      <div className="border-t pt-4" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
        <span className="text-[10px] uppercase block mb-3 text-center" style={{ color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
          Conexión de Sondas recomendada
        </span>
        <div className="flex justify-around items-center">
          {/* Jack COM */}
          <div className="flex flex-col items-center gap-1">
            <div className="w-8 h-8 rounded-full border-4 border-slate-900 bg-black flex items-center justify-center" style={{ boxShadow: '0 0 8px rgba(0,0,0,0.5)' }}>
              <div className="w-3.5 h-3.5 rounded-full bg-slate-950 border border-slate-700" />
            </div>
            <span className="text-[9px] font-bold text-slate-400">COM</span>
          </div>

          {/* Jack V / Ω */}
          <div className="flex flex-col items-center gap-1">
            <div 
              className="w-8 h-8 rounded-full border-4 flex items-center justify-center" 
              style={{ 
                borderColor: mode === 'DCV' || mode === 'ACV' || mode === 'RES' || mode === 'CONT' ? 'rgba(239, 68, 68, 0.8)' : 'var(--bg-color)',
                backgroundColor: '#000',
                boxShadow: '0 0 8px rgba(0,0,0,0.5)'
              }}
            >
              <div 
                className="w-3.5 h-3.5 rounded-full border" 
                style={{ 
                  backgroundColor: mode === 'DCV' || mode === 'ACV' || mode === 'RES' || mode === 'CONT' ? '#ef4444' : '#222',
                  borderColor: '#ef4444'
                }} 
              />
            </div>
            <span className="text-[9px] font-bold text-red-500">V / Ω</span>
          </div>

          {/* Jack CAP */}
          <div className="flex flex-col items-center gap-1">
            <div 
              className="w-8 h-8 rounded-full border-4 flex items-center justify-center" 
              style={{ 
                borderColor: mode === 'CAP' ? 'rgba(239, 68, 68, 0.8)' : 'var(--bg-color)',
                backgroundColor: '#000',
                boxShadow: '0 0 8px rgba(0,0,0,0.5)'
              }}
            >
              <div 
                className="w-3.5 h-3.5 rounded-full border" 
                style={{ 
                  backgroundColor: mode === 'CAP' ? '#ef4444' : '#222',
                  borderColor: '#ef4444'
                }} 
              />
            </div>
            <span className="text-[9px] font-bold text-red-500">CAP</span>
          </div>
        </div>
      </div>
    </div>
  );
};
export default MultimeterPanel;
