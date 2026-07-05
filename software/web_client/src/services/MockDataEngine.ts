export interface Telemetry {
  vpp: number;       // Peak-to-peak in mV
  vrms: number;      // RMS in mV
  vavg: number;      // Average in mV
  frequency: number; // Frequency in Hz
  dutyCycle: number; // 0-100 %
  gainState: number; // 0-5 PGA scale
}

export interface ScopeData {
  ch1: Uint8Array;
  ch2: Uint8Array;
  ch3: Uint8Array;
  ch4: Uint8Array;
  telemetry: Telemetry;
}

// Factor de conversión de cuentas ADC a mV según escala
// V_mv = (counts * 3300) >> (scale + 13)
// donde counts = val_8bit << 4 (ya que se decimó de 12 bits a 8 bits)
export function calculateMilliVolts(val8Bit: number, scale: number): number {
  const counts = val8Bit << 4;
  const shift = scale + 13;
  // Simulación del desplazamiento de bits del firmware
  return Math.round((counts * 3300) / Math.pow(2, shift));
}

export class MockDataEngine {
  private len = 512;
  private phase = 0;

  public generateData(
    ch1Enabled: boolean,
    ch2Enabled: boolean,
    ch3Enabled: boolean,
    ch4Enabled: boolean,
    scales: number[], // [scale1, scale2, scale3, scale4]
    timebaseScale: number, // en kHz, ej: 100 para 100kHz
    triggerChannel: number, // 0-3
    _genType: number, // tipo de onda generador: 0=Seno, 1=Cuadrada, etc.
    _genFreq: number, // frecuencia generador en Hz
    _genAmp: number // amplitud generador en mV
  ): ScopeData {
    const ch1 = new Uint8Array(this.len);
    const ch2 = new Uint8Array(this.len);
    const ch3 = new Uint8Array(this.len);
    const ch4 = new Uint8Array(this.len);

    this.phase += 0.05;
    if (this.phase > 2 * Math.PI) this.phase -= 2 * Math.PI;

    // Frecuencias simuladas para cada canal
    // Usamos el timebase para escalar la frecuencia visual
    const timeFactor = timebaseScale / 10.0;
    const f1 = 1.5 * timeFactor;
    const f2 = 2.0 * timeFactor;
    const f3 = 0.8 * timeFactor;
    const f4 = 3.0 * timeFactor;

    // Generar muestras (0-255)
    for (let i = 0; i < this.len; i++) {
      const t = (i / this.len) * 2 * Math.PI;

      // Canal 1: Seno con ruido leve (si está habilitado)
      if (ch1Enabled) {
        const val = 127 + 60 * Math.sin(f1 * t + this.phase) + (Math.random() - 0.5) * 3;
        ch1[i] = Math.max(0, Math.min(255, Math.round(val)));
      } else {
        ch1[i] = 127; // Nivel medio
      }

      // Canal 2: Cuadrada limpia
      if (ch2Enabled) {
        const val = 127 + 50 * (Math.sin(f2 * t - this.phase * 0.5) >= 0 ? 1 : -1);
        ch2[i] = Math.max(0, Math.min(255, Math.round(val)));
      } else {
        ch2[i] = 127;
      }

      // Canal 3: Triángulo
      if (ch3Enabled) {
        const sineRef = Math.sin(f3 * t + this.phase * 1.2);
        const val = 127 + 55 * (2 / Math.PI) * Math.asin(sineRef);
        ch3[i] = Math.max(0, Math.min(255, Math.round(val)));
      } else {
        ch3[i] = 127;
      }

      // Canal 4: Diente de sierra con ruido
      if (ch4Enabled) {
        const sawRef = ((i * f4) % this.len) / this.len; // 0 a 1
        const val = 127 + 65 * (2 * sawRef - 1) + (Math.random() - 0.5) * 6;
        ch4[i] = Math.max(0, Math.min(255, Math.round(val)));
      } else {
        ch4[i] = 127;
      }
    }

    // Determinar canal activo de trigger para telemetría
    let activeBuffer = ch1;
    let activeScale = scales[0];
    if (triggerChannel === 1) {
      activeBuffer = ch2;
      activeScale = scales[1];
    } else if (triggerChannel === 2) {
      activeBuffer = ch3;
      activeScale = scales[2];
    } else if (triggerChannel === 3) {
      activeBuffer = ch4;
      activeScale = scales[3];
    }

    // Calcular parámetros sobre el buffer activo
    let min = 255;
    let max = 0;
    let sum = 0;
    for (let i = 0; i < this.len; i++) {
      const v = activeBuffer[i];
      if (v < min) min = v;
      if (v > max) max = v;
      sum += v;
    }
    const avg = sum / this.len;

    // Calcular Vrms (Root Mean Square) en cuentas
    let sumSq = 0;
    for (let i = 0; i < this.len; i++) {
      const diff = activeBuffer[i] - avg;
      sumSq += diff * diff;
    }
    const rms = Math.sqrt(sumSq / this.len);

    // Calcular periodo/frecuencia y duty cycle básicos por cruces por cero
    let periodSamples = 0;
    let crossings = 0;
    let firstCrossing = -1;
    let lastCrossing = -1;
    let highSamples = 0;

    for (let i = 0; i < this.len - 1; i++) {
      const curr = activeBuffer[i];
      const next = activeBuffer[i + 1];

      if (curr >= avg) {
        highSamples++;
      }

      // Cruce por cero en sentido ascendente
      if (curr < avg && next >= avg) {
        crossings++;
        if (firstCrossing === -1) {
          firstCrossing = i;
        }
        lastCrossing = i;
      }
    }

    if (crossings > 1 && lastCrossing > firstCrossing) {
      periodSamples = (lastCrossing - firstCrossing) / (crossings - 1);
    }

    // Convertir cuentas ADC a milivoltios
    const vpp_mv = calculateMilliVolts(max - min, activeScale);
    const vavg_mv = calculateMilliVolts(avg, activeScale);
    const vrms_mv = calculateMilliVolts(rms, activeScale);

    // Frecuencia real simulada basada en el periodo y el timebase (sample rate)
    // Freq = (timebaseScale * 1000) / period
    let freq_hz = 0;
    if (periodSamples > 0) {
      freq_hz = Math.round((timebaseScale * 1000) / periodSamples);
    }

    // Ciclo de trabajo aproximado
    const duty = periodSamples > 0 ? Math.round((highSamples / this.len) * 100) : 50;

    return {
      ch1,
      ch2,
      ch3,
      ch4,
      telemetry: {
        vpp: vpp_mv,
        vrms: vrms_mv,
        vavg: vavg_mv,
        frequency: freq_hz,
        dutyCycle: Math.min(100, Math.max(0, duty)),
        gainState: activeScale
      }
    };
  }
}
