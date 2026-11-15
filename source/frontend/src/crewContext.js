/** Display-only summaries. None of these are medical baselines or diagnoses. */
const NORMALIZE_ACTIVITY = value => String(value).trim().replace(/[_-]+/g,' ').toLowerCase()
  .replace(/\b\w/g,letter=>letter.toUpperCase());

export function currentActivity(latest,review,training){
  const raw=training?.activity_state || latest?.activity_state || review?.activity_state;
  if(typeof raw!=='string'||!raw.trim())return {value:'Not available',note:'No context'};
  return {value:NORMALIZE_ACTIVITY(raw),note:training?'Scripted':'Declared'};
}

/** A residual is model reconstruction evidence, not an identified diagnosis. */
export function primaryPattern(unified,training){
  const items=training?.model_evidence?.candidate_17ch?.largest_reconstruction_errors ||
    unified?.explanation?.candidate_17ch?.top_reconstruction_residuals;
  const key=Array.isArray(items)?items.find(x=>typeof x?.channel==='string'&&x.channel.trim())?.channel:null;
  if(!key)return {value:'Awaiting model evidence',note:'Not evaluated'};
  const known={
    heart_rate_bpm:'Heart rate',spo2_percent:'Oxygen saturation',
    respiratory_rate_bpm:'Respiratory rate',core_temp_c:'Core temperature',
    hrv_rmssd_ms:'Heart-rate variability'
  };
  return {value:known[key]||NORMALIZE_ACTIVITY(key),note:'Largest residual'};
}

/** A short-term rolling simulator reference, deliberately not APDRA/medical baseline. */
export function recentBaselineComparison(samples,latest){
  const current=latest?.values?.heart_rate_bpm;
  const subject=latest?.subject_id;
  if(!subject||!Number.isFinite(current)||!Number.isInteger(latest.sequence)){
    return {value:'Not available',note:'No valid stream'};
  }
  const valid=(Array.isArray(samples)?samples:[]).filter(packet=>
    packet?.subject_id===subject &&
    Number.isInteger(packet.sequence) && packet.sequence<latest.sequence &&
    Number.isFinite(packet.values?.heart_rate_bpm)
  ).sort((a,b)=>a.sequence-b.sequence);
  const prior=valid.slice(-45);
  if(prior.length<45)return {value:'Building reference',note:prior.length+'/45 packets'};
  const average=prior.reduce((sum,p)=>sum+p.values.heart_rate_bpm,0)/45;
  const diff=current-average;
  const sign=diff>0?'+':'';
  return {value:'HR '+sign+diff.toFixed(1)+' bpm',note:'vs prior 45'};
}
