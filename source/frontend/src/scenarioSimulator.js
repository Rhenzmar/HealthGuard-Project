/**
 * Local, scripted astronaut training scenarios.
 * No NASA OSDR measurements, medical diagnosis, predictive AI inference,
 * or actual spacecraft atmosphere sensors are used by this module.
 * Thresholds are UI training triggers only, NOT clinical limits.
 */
export const SCENARIOS = [
  {
    id: 'oxygenation',
    name: 'Oxygenation decline',
    subtitle: 'Illustrative breathing / oxygenation event',
    triggerLabel: 'SpO₂ below 94% (training trigger)',
    cause: 'A scripted oxygenation decline. Cabin oxygen, CO₂ and suit telemetry are not measured.',
    guidance: 'Training response: stop strenuous activity, notify mission control and the medical officer, verify the pulse oximeter and check approved cabin or suit atmosphere instrumentation. Follow the mission-approved response checklist. Do not use this demonstration as operational guidance.'
  },
  {
    id: 'exertion',
    name: 'Exertion and high heart rate',
    subtitle: 'Rising cardiovascular and respiratory workload',
    triggerLabel: 'Heart rate above 115 bpm (training trigger)',
    cause: 'A scripted high-workload exercise response, not an indication of a specific disease.',
    guidance: 'Training response: stop the exertion, move to a safe position, confirm the readings and inform the medical officer or mission control. Resume tasks only under mission-approved procedures.'
  },
  {
    id: 'thermal',
    name: 'Thermal instability',
    subtitle: 'Rising simulated core temperature',
    triggerLabel: 'Core temperature above 38.0°C (training trigger)',
    cause: 'A scripted thermal-stress pattern. Suit coolant and ambient temperature are not connected.',
    guidance: 'Training response: reduce workload, notify mission control, verify the temperature sensor and check available thermal-control instrumentation. Follow the approved thermal-event checklist.'
  },
  {
    id: 'sensor',
    name: 'Sensor signal anomaly',
    subtitle: 'Inconsistent SpO₂ reading, other channels remain near baseline',
    triggerLabel: 'Inconsistent signal pattern (training trigger)',
    cause: 'An intentionally inconsistent simulated oximeter trace. A bad sensor is a possibility, not a confirmed diagnosis.',
    guidance: 'Training response: check sensor contact and fit, repeat the measurement with approved equipment and report the inconsistency. Avoid treating a single suspect reading as confirmed physiological deterioration.'
  },
  {
    id:'co2',name:'Cabin CO₂ scrubber failure',
    subtitle:'Fictional spacecraft atmosphere disturbance',
    triggerLabel:'Cabin CO₂ rises above 4,000 ppm (illustrative response trigger)',
    cause:'An intentionally scripted carbon-dioxide buildup and respiratory response, not an actual cabin sensor reading.',
    guidance:'Training response: notify mission control and the crew, verify atmospheric monitoring equipment and follow the approved environmental-control and life-support emergency checklist. Do not infer an exact astronaut diagnosis from CO₂ alone.'
  },
  {
    id:'cabin_leak',name:'Cabin pressure leak',
    subtitle:'Fictional spacecraft depressurization exercise',
    triggerLabel:'Cabin pressure drops below 85 kPa (illustrative response trigger)',
    cause:'Scripted habitat pressure loss. Pressure and oxygen reserves are not measured or connected.',
    guidance:'Training response: alert the crew and mission control, verify cabin pressure independently, follow the pressure-leak response checklist and use approved personal protective equipment where instructed.'
  },
  {
    id:'radiation',name:'Solar radiation event',
    subtitle:'Fictional escalating dosimeter reading',
    triggerLabel:'Scripted radiation-rate surge (not a medically validated limit)',
    cause:'Fictional radiation environment increases. The model does not predict radiation sickness or actual biological exposure.',
    guidance:'Training response: notify mission control, confirm readings with mission dosimetry and follow approved radiation shelter and operational procedures. This simulation is not a real exposure calculation.'
  },
  {
    id:'suit_leak',name:'Suit pressure loss',
    subtitle:'Scripted EVA suit pressure-control failure',
    triggerLabel:'Suit pressure below 3.4 psi (training illustration, not an operational limit)',
    cause:'Fictional pressure decrease with an illustrative physiological response, not actual suit telemetry.',
    guidance:'Training response: stop the EVA task, verify the suit pressure reading, notify Mission Control and follow the approved pressure-loss checklist.'
  },
  {
    id:'suit_power',name:'Suit battery failure',
    subtitle:'Scripted EVA battery depletion',
    triggerLabel:'Suit battery reserve below 50% (illustrative training trigger)',
    cause:'Simulated rapid battery loss, not an actual battery controller reading.',
    guidance:'Training response: stop the EVA task, check the power reading, notify Mission Control and follow the approved electrical-power checklist.'
  }
];

const BASELINES = {
  SIM_CREW_01: [70, 98.3, 14.0, 36.75, 62],
  SIM_CREW_02: [65, 98.6, 12.8, 36.63, 71],
  SIM_CREW_03: [76, 97.9, 15.5, 36.85, 55],
  SIM_CREW_04: [72, 98.45, 13.5, 36.7, 65]
};

export const SCENARIO_LENGTH = 64;
export const SCENARIO_STAGES = [
  { at: 0, title: 'Baseline', description: 'Training run begins with simulated nominal readings.' },
  { at: 9, title: 'Developing', description: 'The scripted disturbance begins; measurements gradually diverge.' },
  { at: 25, title: 'Peak disturbance', description: 'The strongest simulated deviation is reached.' },
  { at: 44, title: 'Recovery', description: 'The disturbance is removed and the illustrative signals begin to recover.' },
  { at: 64, title: 'Complete', description: 'Training scenario complete. Return to the live simulator to resume its feed.' }
];
const clamp = (x, min = 0, max = 1) => Math.min(max, Math.max(min, x));
const round = (n, places = 1) => Number(n.toFixed(places));

export function scenarioAt(subjectId, scenarioId, second) {
  const scenario = SCENARIOS.find(s => s.id === scenarioId);
  if (!scenario) throw new Error('Unknown training scenario');
  const t = clamp(Math.floor(second), 0, SCENARIO_LENGTH);
  const [hr, spo2, rr, temp, hrv] = BASELINES[subjectId] || BASELINES.SIM_CREW_01;
  // Smooth, deterministic onset and recovery. No jitter or random values
  // that could be confused with real sensor noise.
  const rising = clamp((t - 8) / 18);
  const falling = 1 - clamp((t - 44) / 18);
  const disturbance = rising * falling;
  const wobble = Math.sin(t / 4 + hr / 10) * 0.55;
  const values = {
    heart_rate_bpm: round(hr + wobble, 1),
    spo2_percent: round(spo2 + 0.07 * Math.sin(t / 7), 1),
    respiratory_rate_bpm: round(rr + 0.15 * Math.sin(t / 5), 1),
    core_temp_c: round(temp + 0.025 * Math.sin(t / 9), 2),
    hrv_rmssd_ms: round(hrv + 0.5 * Math.sin(t / 6), 1)
  };
  if (scenarioId === 'oxygenation') {
    values.heart_rate_bpm = round(values.heart_rate_bpm + 29 * disturbance);
    values.spo2_percent = round(values.spo2_percent - 10 * disturbance, 1);
    values.respiratory_rate_bpm = round(values.respiratory_rate_bpm + 10 * disturbance);
    values.hrv_rmssd_ms = round(values.hrv_rmssd_ms - 17 * disturbance);
  } else if (scenarioId === 'exertion') {
    values.heart_rate_bpm = round(values.heart_rate_bpm + 73 * disturbance);
    values.spo2_percent = round(values.spo2_percent - 1.25 * disturbance, 1);
    values.respiratory_rate_bpm = round(values.respiratory_rate_bpm + 17 * disturbance);
    values.core_temp_c = round(values.core_temp_c + 0.45 * disturbance, 2);
    values.hrv_rmssd_ms = round(values.hrv_rmssd_ms - 28 * disturbance);
  } else if (scenarioId === 'thermal') {
    values.heart_rate_bpm = round(values.heart_rate_bpm + 29 * disturbance);
    values.respiratory_rate_bpm = round(values.respiratory_rate_bpm + 8 * disturbance);
    values.core_temp_c = round(values.core_temp_c + 2.1 * disturbance, 2);
    values.hrv_rmssd_ms = round(values.hrv_rmssd_ms - 16 * disturbance);
  } else if (scenarioId === 'co2') {
    values.heart_rate_bpm = round(values.heart_rate_bpm + 17*disturbance);
    values.respiratory_rate_bpm = round(values.respiratory_rate_bpm + 12*disturbance);
  } else if (scenarioId === 'cabin_leak') {
    values.heart_rate_bpm = round(values.heart_rate_bpm + 24*disturbance);
    values.respiratory_rate_bpm = round(values.respiratory_rate_bpm + 13*disturbance);
    values.spo2_percent = round(values.spo2_percent - 7.2*disturbance);
  } else if (scenarioId === 'suit_leak') {
    values.spo2_percent = round(values.spo2_percent - 5 * disturbance, 1);
    values.respiratory_rate_bpm = round(values.respiratory_rate_bpm + 6 * disturbance);
  } else if (scenarioId === 'sensor') {
    values.spo2_percent = round(values.spo2_percent - 16 * disturbance, 1);
    values.heart_rate_bpm = round(values.heart_rate_bpm + 0.7 * disturbance);
  }
  const flags = {
    heart_rate_bpm: scenarioId === 'exertion' && values.heart_rate_bpm > 115,
    spo2_percent: scenarioId === 'cabin_leak' && values.spo2_percent < 94 || scenarioId === 'oxygenation' && values.spo2_percent < 94 ||
      scenarioId === 'sensor' && disturbance > 0.55,
    respiratory_rate_bpm: scenarioId === 'co2' && values.respiratory_rate_bpm > 21 || scenarioId === 'cabin_leak' && values.respiratory_rate_bpm > 22 || scenarioId === 'oxygenation' && values.respiratory_rate_bpm > 20 ||
      scenarioId === 'exertion' && values.respiratory_rate_bpm > 26,
    core_temp_c: scenarioId === 'thermal' && values.core_temp_c > 38,
    hrv_rmssd_ms: false
  };
  const engineering_values={
    cabin_co2_ppm:round(650 + (scenarioId==='co2'?5400*disturbance:0),1),
    cabin_pressure_kpa:round(101.2 - (scenarioId==='cabin_leak'?27*disturbance:0),2),
    cabin_o2_percent:20.9,
    radiation_rate_usv_h:round(.45 + (scenarioId==='radiation'?2200*disturbance:0),2),
    suit_pressure_psi:round(4.3 - (scenarioId==='suit_leak'?2*disturbance:0),2),
    suit_battery_percent:round(Math.max(0,88 - (scenarioId==='suit_power'?70*disturbance:0)),2)
  };
  const engineering_flags={
    cabin_co2_ppm:scenarioId==='co2'&&engineering_values.cabin_co2_ppm>4000,
    cabin_pressure_kpa:scenarioId==='cabin_leak'&&engineering_values.cabin_pressure_kpa<85,
    radiation_rate_usv_h:scenarioId==='radiation'&&disturbance>.55,
    suit_pressure_psi:scenarioId==='suit_leak'&&engineering_values.suit_pressure_psi<3.4,
    suit_battery_percent:scenarioId==='suit_power'&&engineering_values.suit_battery_percent<50
  };
  const alert=Object.values(flags).some(Boolean)||Object.values(engineering_flags).some(Boolean);
  // Severity is a scripted training progression, not a diagnostic score.
  // The status colors describe only scenario intensity; stable, actual
  // physiological baselines and sparse OSDR lab data are not rated.
  const tier = disturbance < 0.12 ? 'OPTIMAL' :
    disturbance < 0.42 ? 'CHECK' :
    disturbance < 0.78 ? 'WARNING' : alert ? 'CRITICAL' : 'WARNING';
  const affected = {
    oxygenation: ['heart_rate_bpm','spo2_percent','respiratory_rate_bpm','hrv_rmssd_ms'],
    exertion: ['heart_rate_bpm','spo2_percent','respiratory_rate_bpm','core_temp_c','hrv_rmssd_ms'],
    thermal: ['heart_rate_bpm','respiratory_rate_bpm','core_temp_c','hrv_rmssd_ms'],
    sensor: ['spo2_percent'],
    co2: ['heart_rate_bpm','respiratory_rate_bpm'],
    cabin_leak: ['heart_rate_bpm','respiratory_rate_bpm','spo2_percent'],
    radiation: [],
    suit_leak:['spo2_percent','respiratory_rate_bpm'],
    suit_power:[]
  }[scenarioId];
  const metric_levels = Object.fromEntries(Object.keys(values).map(key=>[
    key,affected.includes(key) ? tier : 'OPTIMAL'
  ]));
  const stage = t >= 64 ? 'Complete' : t >= 44 ? 'Recovery' :
    t >= 25 ? 'Peak disturbance' : t >= 9 ? 'Developing' : 'Baseline';
  return {
    subject_id: subjectId,
    sequence: t,
    timestamp: null, // This is playback time, not a real acquisition timestamp.
    source: 'SCRIPTED_TRAINING_SCENARIO',
    scenario_id: scenarioId,
    elapsed_seconds: t,
    values, flags, engineering_values, engineering_flags, alert, stage, disturbance, severity:tier, metric_levels,
    reason: alert ? scenario.cause : t > 8 && t < 63 ? 'Scenario values are evolving. Training triggers have not fired at this instant.' :
      'Illustrative baseline or recovered phase; not a clinical clearance.',
    guidance: scenario.guidance,
    trigger: scenario.triggerLabel
  };
}

export function scenarioHistory(subjectId, scenarioId, second) {
  const end = clamp(Math.floor(second), 0, SCENARIO_LENGTH);
  return Array.from({ length: end + 1 }, (_, t) => scenarioAt(subjectId, scenarioId, t));
}
