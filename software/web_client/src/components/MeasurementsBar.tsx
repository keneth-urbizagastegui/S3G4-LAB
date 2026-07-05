import React from 'react';
import type { ScopeData } from '../services/MockDataEngine';

// Helper to convert 8-bit raw sample to mV
function calculateMilliVolts(val8Bit: number, scale: number): number {
  const counts = val8Bit << 4;
  const shift = scale + 13;
  return Math.round((counts * 3300) / Math.pow(2, shift));
}

interface MeasurementsBarProps {
  data: ScopeData | null;
  activeChannel: number;
  gains: number[];
  cursorsVEnabled: boolean;
  setCursorsVEnabled: (val: boolean) => void;
  cursorsHEnabled: boolean;
  setCursorsHEnabled: (val: boolean) => void;
  vcc?: number; // in mV, e.g. 3335
  samplingTimeNs?: number; // e.g. 125
  sequenceNumber?: number; // e.g. 4507
}

export const MeasurementsBar: React.FC<MeasurementsBarProps> = ({
  data,
  activeChannel,
  gains,
  cursorsVEnabled,
  setCursorsVEnabled,
  cursorsHEnabled,
  setCursorsHEnabled,
  vcc = 3300,
  samplingTimeNs = 125,
  sequenceNumber = 1204,
}) => {
  // Format voltage to V or mV
  const formatVolts = (mv: number) => {
    return `${(mv / 1000).toFixed(4)}`;
  };

  // Calculate min and max from raw data if available
  let minMv = 0;
  let maxMv = 0;
  let vppMv = data?.telemetry.vpp ?? 0;
  let vrmsMv = data?.telemetry.vrms ?? 0;
  let vavgMv = data?.telemetry.vavg ?? 0;

  if (data) {
    const activeBuffer =
      activeChannel === 0
        ? data.ch1
        : activeChannel === 1
        ? data.ch2
        : activeChannel === 2
        ? data.ch3
        : data.ch4;

    let minVal = 255;
    let maxVal = 0;
    for (let i = 0; i < activeBuffer.length; i++) {
      const v = activeBuffer[i];
      if (v < minVal) minVal = v;
      if (v > maxVal) maxVal = v;
    }

    const scale = gains[activeChannel];
    minMv = calculateMilliVolts(minVal, scale);
    maxMv = calculateMilliVolts(maxVal, scale);
    
    // Fallbacks or adjustments if data calculations differ from telemetry
    if (vppMv === 0) {
      vppMv = maxMv - minMv;
    }
  }

  return (
    <div className="flex flex-col gap-2 w-full select-none" style={{ color: 'var(--text-secondary)' }}>
      {/* Cajas de Medidas y Cursors */}
      <div className="flex flex-wrap items-stretch gap-4 w-full">
        {/* Caja de Medida del Canal Activo */}
        <div 
          className="flex-1 min-w-[300px] border rounded-xl p-3 flex flex-col justify-between"
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.4)',
            borderColor: 'rgba(255, 255, 255, 0.08)',
          }}
        >
          <span className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
            Measure (Channel {activeChannel + 1})
          </span>
          <div className="grid grid-cols-5 gap-2">
            {/* Vpp */}
            <div className="bg-slate-950/60 border border-white/5 rounded-lg p-2 text-center">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Vpp</div>
              <div className="font-mono text-sm font-bold text-white mt-1">
                {data ? formatVolts(vppMv) : '----'}
              </div>
            </div>
            {/* Vrms */}
            <div className="bg-slate-950/60 border border-white/5 rounded-lg p-2 text-center">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Vrms</div>
              <div className="font-mono text-sm font-bold text-white mt-1">
                {data ? formatVolts(vrmsMv) : '----'}
              </div>
            </div>
            {/* Avg */}
            <div className="bg-slate-950/60 border border-white/5 rounded-lg p-2 text-center">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Avg</div>
              <div className="font-mono text-sm font-bold text-white mt-1">
                {data ? formatVolts(vavgMv) : '----'}
              </div>
            </div>
            {/* Min */}
            <div className="bg-slate-950/60 border border-white/5 rounded-lg p-2 text-center">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Min</div>
              <div className="font-mono text-sm font-bold text-white mt-1">
                {data ? formatVolts(minMv) : '----'}
              </div>
            </div>
            {/* Max */}
            <div className="bg-slate-950/60 border border-white/5 rounded-lg p-2 text-center">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Max</div>
              <div className="font-mono text-sm font-bold text-white mt-1">
                {data ? formatVolts(maxMv) : '----'}
              </div>
            </div>
          </div>
        </div>

        {/* Caja de Control de Cursores */}
        <div 
          className="w-[180px] border rounded-xl p-3 flex flex-col justify-between"
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.4)',
            borderColor: 'rgba(255, 255, 255, 0.08)',
          }}
        >
          <span className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
            Cursors
          </span>
          <div className="flex gap-3 h-full items-center">
            {/* Cursor V (Tiempo) */}
            <button
              onClick={() => setCursorsVEnabled(!cursorsVEnabled)}
              className="flex-1 py-2 rounded-lg border font-bold text-sm cursor-pointer transition-all flex items-center justify-center gap-1.5"
              style={{
                backgroundColor: cursorsVEnabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                borderColor: cursorsVEnabled ? '#10b981' : 'rgba(255, 255, 255, 0.1)',
                color: cursorsVEnabled ? '#10b981' : 'var(--text-secondary)',
                boxShadow: cursorsVEnabled ? '0 0 10px rgba(16, 185, 129, 0.2)' : 'none',
              }}
            >
              <span 
                className="w-2 h-2 rounded-full" 
                style={{ 
                  backgroundColor: cursorsVEnabled ? '#10b981' : '#64748b',
                  boxShadow: cursorsVEnabled ? '0 0 6px #10b981' : 'none'
                }} 
              />
              V
            </button>
            {/* Cursor H (Voltaje) */}
            <button
              onClick={() => setCursorsHEnabled(!cursorsHEnabled)}
              className="flex-1 py-2 rounded-lg border font-bold text-sm cursor-pointer transition-all flex items-center justify-center gap-1.5"
              style={{
                backgroundColor: cursorsHEnabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                borderColor: cursorsHEnabled ? '#10b981' : 'rgba(255, 255, 255, 0.1)',
                color: cursorsHEnabled ? '#10b981' : 'var(--text-secondary)',
                boxShadow: cursorsHEnabled ? '0 0 10px rgba(16, 185, 129, 0.2)' : 'none',
              }}
            >
              <span 
                className="w-2 h-2 rounded-full" 
                style={{ 
                  backgroundColor: cursorsHEnabled ? '#10b981' : '#64748b',
                  boxShadow: cursorsHEnabled ? '0 0 6px #10b981' : 'none'
                }} 
              />
              H
            </button>
          </div>
        </div>
      </div>

      {/* Footer Info / Status Bar */}
      <div 
        className="flex justify-between items-center px-4 py-2 border rounded-lg text-[10px] font-semibold tracking-wide"
        style={{
          backgroundColor: 'rgba(5, 8, 18, 0.5)',
          borderColor: 'rgba(255, 255, 255, 0.05)',
          color: 'var(--text-muted)'
        }}
      >
        <div className="flex gap-4">
          <span>Vcc: <strong className="text-slate-300">{vcc} mV</strong></span>
          <span>|</span>
          <span>Sampling Time: <strong className="text-slate-300">{samplingTimeNs} ns</strong></span>
          <span>|</span>
          <span>Seq. Number: <strong className="text-slate-300">{sequenceNumber}</strong></span>
        </div>
        <div>
          <span>💡 Rueda del ratón para zoom, arrastrar líneas de cursores para medir</span>
        </div>
      </div>
    </div>
  );
};

export default MeasurementsBar;
