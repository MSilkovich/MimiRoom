export function durationMinutes(service={}) {
  if(Number(service.duration_minutes)>0)return Number(service.duration_minutes);
  const m=/^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$/.exec(service.duration||'');
  return m?Math.ceil(Number(m[1]||0)*1440+Number(m[2]||0)*60+Number(m[3]||0)+Number(m[4]||0)/60)||60:60;
}
export const minutesOf=t=>Number(t?.slice(0,2)||0)*60+Number(t?.slice(3,5)||0);
export const formatTime=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
export function collisionFor({bookings,services,date,masterId,petId,start,duration,excludeId}) {
  return bookings.find(b=>b.status!=='cancelled'&&b.book_id!==excludeId&&b.date===date&&(b.master_id===masterId||(petId&&b.pet_id===petId))&&minutesOf(b.time)<start+duration&&minutesOf(b.time)+durationMinutes(services.find(s=>s.service_id===b.service_id))>start);
}
export function availableSlots(options){
  const slots=[];for(let start=600;start+options.duration<=1140;start+=30){if(!collisionFor({...options,start}))slots.push(formatTime(start))}return slots;
}
