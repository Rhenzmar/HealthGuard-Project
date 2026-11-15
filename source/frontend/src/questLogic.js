/** Fictional astronaut routine. Never treat a completion as sensor/medical verification. */
export const QUESTS=Object.freeze([
  {id:'morning',name:'Morning physiological check-in',category:'MEASUREMENT',icon:'heart',route:'dashboard',action:'Review crew dashboard',xp:20,summary:'Check the selected crew member’s simulated vital-sign snapshot.',instructions:'Open Mission Dashboard and inspect the latest available simulated physiological readings. Confirm the selected crew member and data-source label. If the stream is unavailable, defer the task instead of inventing a reading.',caution:'Readings are fictional simulator data. This does not establish personal health status.'},
  {id:'quality',name:'Measurement quality review',category:'SENSOR LITERACY',icon:'shield',route:'telemetry',action:'Inspect telemetry evidence',xp:15,summary:'Check measurement quality before interpreting a pattern flag.',instructions:'Open Crew Telemetry and review PhysioAlert’s measurement-quality evidence. Note missing values, temporary spikes and persistent patterns. A missing state is not proof of an acceptable reading.',caution:'No actual wearable or medical sensor is calibrated in this demonstration.'},
  {id:'activity',name:'Activity and context log',category:'MISSION ROUTINE',icon:'activity',route:'dashboard',action:'Review activity context',xp:20,summary:'Review the declared activity context for this simulated mission.',instructions:'On Mission Dashboard, check the simulated activity context when it is available. Consider how physical activity can change measurements. Use the mission reflection note to record what you reviewed.',caution:'Activity states are fictional simulation context, not observations from a tracker.'},
  {id:'literacy',name:'Health indicator learning',category:'LEARNING',icon:'book',route:'body',action:'Explore body systems',xp:10,summary:'Explore one body system and understand its monitored signals.',instructions:'Open Body Explorer, select an anatomical region, and review its linked physiological measurements and limitations. Not every region has a directly measured signal.',caution:'A numerical pattern flag cannot diagnose a medical condition.'},
  {id:'evening',name:'Evening mission reflection',category:'CHECK-IN',icon:'check',route:'routine',action:'Write mission reflection',xp:20,summary:'Review completed and deferred tasks, then record your mission note.',instructions:'Return to this routine, review the daily task statuses, and write a short note about observations, missing telemetry or tasks that need follow-up. Then mark the reflection complete.',caution:'Notes are saved only to this browser and are never sent to real Mission Control.'}
]);
export const ROUTINE_STORAGE_KEY='healthguard-mission-quest-v2';
export const LEGACY_ROUTINE_KEY='healthguard-mission-quest-v1';
export const ROUTINE_CREW=Object.freeze(['SIM_CREW_01','SIM_CREW_02','SIM_CREW_03','SIM_CREW_04']);
const isObject=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const pad=n=>String(n).padStart(2,'0');
export function localDayKey(date=new Date()){return date.getFullYear()+'-'+pad(date.getMonth()+1)+'-'+pad(date.getDate())}
export function getQuestPoints(ids=[]){const done=new Set(ids);return QUESTS.reduce((sum,q)=>sum+(done.has(q.id)?q.xp:0),0)}
export function getQuestCompletion(ids=[]){const done=new Set(ids);return Math.round(100*QUESTS.filter(q=>done.has(q.id)).length/QUESTS.length)}
export function emptyRoutineStore(){return {version:2,days:{}}}
export function readRoutineStore(storage){
  const source=storage===undefined?(typeof window!=='undefined'?window.localStorage:null):storage;
  if(!source)return emptyRoutineStore();
  try{
    const parsed=JSON.parse(source.getItem(ROUTINE_STORAGE_KEY)||'null');
    if(isObject(parsed)&&parsed.version===2&&isObject(parsed.days))return parsed;
    const previous=JSON.parse(source.getItem(LEGACY_ROUTINE_KEY)||'null');
    const store=emptyRoutineStore();
    if(isObject(previous)){
      // Legacy progress did not identify a crew. Preserve it for the original
      // default crew only; do not incorrectly assign it to all four astronauts.
      for(const [day,tasks] of Object.entries(previous)){
        if(!/^\d{4}-\d{2}-\d{2}$/.test(day)||!isObject(tasks))continue;
        const accepted={};
        for(const q of QUESTS)if(tasks[q.id]==='complete'||tasks[q.id]==='deferred')accepted[q.id]=tasks[q.id];
        if(Object.keys(accepted).length)store.days[day]={SIM_CREW_01:{tasks:accepted,note:''}};
      }
    }
    return store;
  }catch{return emptyRoutineStore()}
}
export function getCrewRoutine(store,day,crewId){
  const value=store?.days?.[day]?.[crewId];
  return {tasks:isObject(value?.tasks)?value.tasks:{},note:typeof value?.note==='string'?value.note:''};
}
export function summarizeCrewRoutine(store,day,crewId){
  const entry=getCrewRoutine(store,day,crewId);
  const ids=QUESTS.filter(q=>entry.tasks[q.id]==='complete').map(q=>q.id);
  const deferred=QUESTS.filter(q=>entry.tasks[q.id]==='deferred').length;
  return {ids,done:ids.length,deferred,pending:QUESTS.length-ids.length-deferred,percent:getQuestCompletion(ids),xp:getQuestPoints(ids)};
}
export function updateCrewRoutine(store,day,crewId,patch){
  if(!ROUTINE_CREW.includes(crewId)||!/^\d{4}-\d{2}-\d{2}$/.test(day))return store;
  const prior=getCrewRoutine(store,day,crewId);
  const next={tasks:{...prior.tasks},note:prior.note};
  if(patch.taskId&&QUESTS.some(q=>q.id===patch.taskId)){
    if(patch.status==='complete'||patch.status==='deferred')next.tasks[patch.taskId]=patch.status;
    else delete next.tasks[patch.taskId];
  }
  if(typeof patch.note==='string')next.note=patch.note.slice(0,800);
  return {...store,version:2,days:{...(store?.days||{}),[day]:{...(store?.days?.[day]||{}),[crewId]:next}}};
}
export function saveRoutineStore(store,storage){
  try{const target=storage===undefined?(typeof window!=='undefined'?window.localStorage:null):storage;if(!target)return false;target.setItem(ROUTINE_STORAGE_KEY,JSON.stringify(store));return true}catch{return false}
}
