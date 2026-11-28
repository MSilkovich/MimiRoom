import {seed,ids} from './data.js';

const KEY='mimiroom-crm-demo-v1';
let db;
try { db=JSON.parse(localStorage.getItem(KEY))||structuredClone(seed); }
catch { db=structuredClone(seed); }
for (const booking of db.book||[]) {
  if (booking.status==='done') booking.status='completed';
  if (booking.status==='active') booking.status='confirmed';
}
db['work-schedules']??=(db.users||[]).filter(u=>['groomer','master'].includes(u.role)).flatMap((u,i)=>Array.from({length:5},(_,weekday)=>({work_schedule_id:i*5+weekday+1,master_id:u.user_id,weekday,start_time:'10:00:00',end_time:'19:00:00',is_day_off:false})));
const persist=()=>localStorage.setItem(KEY,JSON.stringify(db));
export const config={base:localStorage.getItem('mimiroom-api')||'',token:sessionStorage.getItem('mimiroom-token')||'',mode:sessionStorage.getItem('mimiroom-mode')||'demo'};
export class ApiError extends Error {
  constructor(message,status,detail=null) { super(message);this.name='ApiError';this.status=status;this.detail=detail; }
}
export function salonDateParts(value) {
  const date=new Date(value);
  if (!Number.isFinite(date.getTime())) throw new ApiError('Сервер вернул некорректную дату визита.',0);
  const parts=Object.fromEntries(new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Moscow',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(date).map(p=>[p.type,p.value]));
  return {date:`${parts.year}-${parts.month}-${parts.day}`,time:`${parts.hour}:${parts.minute}:${parts.second}`};
}
export function normalizeBooking(booking) {
  if (!booking.start_time) return {...booking,book_id:booking.booking_id??booking.book_id};
  return {...booking,book_id:booking.booking_id,...salonDateParts(booking.start_time)};
}
function apiBase(value) {
  const base=String(value||'').trim().replace(/\/+$/,'').replace(/\/api\/v0\.0\.1$/,'');
  if (base&&!/^https?:\/\/[^\s]+$/i.test(base)) throw new ApiError('Укажите HTTP(S)-адрес API или оставьте поле пустым для подключения студии.',0);
  if(base){const u=new URL(base);if(u.username||u.password||u.search||u.hash)throw new ApiError('Адрес API не должен содержать пароль, параметры или фрагмент.',0);}
  return base;
}
function clearSession() {
  config.token='';config.mode='demo';
  for(const key of ['mimiroom-token','mimiroom-refresh','mimiroom-user','mimiroom-mode'])sessionStorage.removeItem(key);
}
function setTokens(tokens) {
  if (!tokens?.access_token||!tokens.refresh_token||!Number.isInteger(tokens.user_id)) throw new ApiError('Некорректный ответ авторизации.',0);
  config.token=tokens.access_token;
  sessionStorage.setItem('mimiroom-token',tokens.access_token);
  sessionStorage.setItem('mimiroom-refresh',tokens.refresh_token);
  sessionStorage.setItem('mimiroom-user',String(tokens.user_id));
}
function errorMessage(data,status) {
  if (typeof data?.detail==='string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map(e=>`${(e.loc||[]).filter(x=>x!=='body').join('.')}: ${e.msg||'проверьте значение'}`).join('; ');
  if (typeof data?.message==='string') return data.message;
  return {401:'Войдите заново. Сессия завершена.',403:'Недостаточно прав для этого действия.',409:'Окошко уже занято. Обновите свободное время и выберите другое.'}[status]||`Не удалось выполнить запрос (${status}).`;
}
let refreshing=null;
async function request(resource,{method='GET',body,base=config.base,auth=true,signal}={},retry=true) {
  let response;
  try {
    response=await fetch(apiBase(base)+'/api/v0.0.1/'+resource,{method,headers:{...(body!==undefined?{'Content-Type':'application/json'}:{}),...(auth&&config.token?{Authorization:`Bearer ${config.token}`}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{}),signal:signal||AbortSignal.timeout(15000)});
  } catch(error) {
    if(error instanceof ApiError)throw error;
    throw new ApiError('Сервер недоступен. Проверьте подключение к студии.',0);
  }
  if(response.status===401&&auth&&retry&&sessionStorage.getItem('mimiroom-refresh')) {
    if(!refreshing)refreshing=request('auth/refresh',{method:'POST',body:{refresh_token:sessionStorage.getItem('mimiroom-refresh'),grant_type:'refresh'},base,auth:false},false).then(setTokens).catch(error=>{clearSession();throw error}).finally(()=>{refreshing=null});
    await refreshing;
    return request(resource,{method,body,base,auth,signal},false);
  }
  if(!response.ok) {
    let data;try{data=await response.json()}catch{}
    if(response.status===401&&auth)clearSession();
    throw new ApiError(errorMessage(data,response.status),response.status,data?.detail);
  }
  if(response.status===204)return null;
  try{return await response.json()}catch{throw new ApiError('Сервер вернул неожиданный формат ответа.',0)}
}
const apiResources={book:'bookings'};
const apiFields={...ids,bookings:'booking_id',masters:'user_id','work-schedules':'work_schedule_id'};
const bodyFields={
  pets:['name','owner_id','birthday','breed_id'],
  users:['login','password','name','surname','patronymic','phone','email'],
  services:['title','description','duration','price','buffer_before_minutes','buffer_after_minutes','breed_id','master_ids'],
  masters:['login','password','name','surname','patronymic','phone','email','service_ids'],
  storages:['title','count','measure_unit_id'],
  'work-schedules':['master_id','weekday','start_time','end_time','is_day_off'],
  breeds:['title','pet_type_id'],'pet-types':['title'],'measure-units':['title']
};
function writeBody(resource,data,id) {
  if(resource==='book')resource='bookings';
  if(resource==='bookings') {
    if(id&&['master_id','service_id','date','time','start_time','end_time'].some(k=>data[k]!==undefined))throw new ApiError('API не поддерживает перенос времени или смену услуги существующей записи. Создайте новую запись и отдельно отмените прежнюю.',0);
    const allowed=id?['status','client_id','client_name','client_phone','pet_id','comment','options']:['master_id','service_id','start_time','client_id','client_name','client_phone','pet_id','comment','options'];
    const result=Object.fromEntries(allowed.filter(k=>data[k]!==undefined).map(k=>[k,data[k]]));
    if(!id&&!result.start_time&&data.date&&data.time)result.start_time=`${data.date}T${data.time.length===5?data.time+':00':data.time}+03:00`;
    if(!id&&!result.start_time)throw new ApiError('Выберите свободное окошко.',0);
    return result;
  }
  let fields=bodyFields[resource];
  if(!fields)throw new ApiError('Неизвестный ресурс API.',0);
  if(resource==='services'&&!id)fields=[...fields,'consumables'];
  if(resource==='work-schedules'&&id)fields=fields.filter(k=>k!=='master_id');
  const result=Object.fromEntries(fields.filter(k=>data[k]!==undefined).map(k=>[k,data[k]]));
  if(resource==='users'&&!id){result.phone??=null;result.email??=null;}
  return result;
}
async function list(resource,filters={}) {
  if(config.mode==='demo') {
    let data=resource==='masters'?db.users.filter(u=>['groomer','master','employee'].includes(u.role)):db[resource==='bookings'?'book':resource]||[];
    data=data.filter(item=>Object.entries(filters).every(([k,v])=>v===undefined||v===null||v===''||(k==='date_from'?item.date>=v:k==='date_to'?item.date<=v:String(item[k])===String(v))));
    return structuredClone(data);
  }
  const remote=apiResources[resource]||resource,field=remote==='bookings'?'booking_id':apiFields[resource]||apiFields[remote]||(remote.endsWith('/history')?'booking_id':undefined),all=[],seen=new Set();
  for(let offset=0;offset<10000;offset+=100) {
    const query=new URLSearchParams(Object.entries(filters).filter(([,v])=>v!==undefined&&v!==null&&v!==''));query.set('limit','100');query.set('offset',String(offset));
    const page=await request(remote+'?'+query);
    if(!Array.isArray(page))throw new ApiError('API вернул неожиданный формат списка.',0);
    for(const item of page){const id=item[field];if(id===undefined)throw new ApiError(`API не вернул идентификатор ${field}.`,0);if(seen.has(id))throw new ApiError('API вернул повторные записи при загрузке страниц. Проверьте offset.',0);seen.add(id);all.push(remote==='bookings'?normalizeBooking(item):item);}
    if(page.length<100)return all;
  }
  throw new ApiError('Превышен предел загрузки 10 000 строк. Сузьте диапазон или фильтры.',0);
}
export const api={
  list,
  async get(resource,id){
    if(config.mode==='demo')return structuredClone((resource==='masters'?db.users:db[resource]||[]).find(x=>x[apiFields[resource]]===id));
    const item=await request((apiResources[resource]||resource)+'/'+encodeURIComponent(id));return ['book','bookings'].includes(resource)?normalizeBooking(item):item;
  },
  async login(base,username,password){const nextBase=apiBase(base);const tokens=await request('auth/token',{method:'POST',body:{username,password,grant_type:'password'},base:nextBase,auth:false},false);setTokens(tokens);config.base=nextBase;config.mode='live';localStorage.setItem('mimiroom-api',nextBase);sessionStorage.setItem('mimiroom-mode','live');return tokens;},
  async register(base,data){const nextBase=apiBase(base);const payload=Object.fromEntries(['login','password','name','surname','patronymic'].filter(k=>data[k]!==undefined&&data[k]!=='').map(k=>[k,data[k]]));const tokens=await request('auth/register',{method:'POST',body:payload,base:nextBase,auth:false},false);setTokens(tokens);config.base=nextBase;config.mode='live';localStorage.setItem('mimiroom-api',nextBase);sessionStorage.setItem('mimiroom-mode','live');return tokens;},
  async logout(){try{if(config.mode==='live')await request('auth/logout',{method:'POST',body:{refresh_token:sessionStorage.getItem('mimiroom-refresh')}})}finally{clearSession()}},
  async save(resource,data,id){
    if(config.mode==='live'){const item=await request((apiResources[resource]||resource)+(id?'/'+encodeURIComponent(id):''),{method:id?'PUT':'POST',body:writeBody(resource,data,id)});return ['book','bookings'].includes(resource)?normalizeBooking(item):item;}
    const name=resource==='masters'?'users':resource==='bookings'?'book':resource,field=resource==='masters'?'user_id':apiFields[resource];
    db[name]??=[];
    if(id){const at=db[name].findIndex(x=>x[field]===id);if(at<0)throw new ApiError('Запись не найдена.',404);db[name][at]={...db[name][at],...data};persist();return structuredClone(db[name][at]);}
    const item={...data,...(resource==='masters'?{role:'groomer'}:{}),[field]:Math.max(0,...db[name].map(x=>x[field]||0))+1};db[name].push(item);persist();return structuredClone(item);
  },
  async remove(resource,id){if(config.mode==='live')return request((apiResources[resource]||resource)+'/'+id,{method:'DELETE'});const name=resource==='masters'?'users':resource;db[name]=(db[name]||[]).filter(x=>x[apiFields[resource]]!==id);persist();},
  async cancelBooking(id){if(config.mode==='demo')return api.save('book',{status:'cancelled'},id);return normalizeBooking(await request(`bookings/${id}/cancel`,{method:'POST'}));},
  async completeBooking(id){if(config.mode==='demo')return api.save('book',{status:'completed'},id);return normalizeBooking(await request(`bookings/${id}/complete`,{method:'POST'}));},
  async availableSlots(data){const slots=await request('slots/available',{method:'POST',body:Object.fromEntries(['service_id','master_id','date_from','date_to','pet_id'].filter(k=>data[k]!==undefined&&data[k]!==null&&data[k]!=='').map(k=>[k,data[k]]))});if(!Array.isArray(slots))throw new ApiError('Не удалось прочитать свободные окошки.',0);return slots.filter(s=>s.available!==false&&s.master_id&&s.start_time&&s.end_time).map(s=>({...s,...salonDateParts(s.start_time)}));},
  async petHistory(id){if(config.mode==='demo')return (await api.list('book')).filter(b=>b.pet_id===id);return (await list(`pets/${id}/history`)).map(normalizeBooking);},
  async summary(id){if(config.mode==='live')return request(`users/${id}/summary`);return {user:db.users.find(u=>u.user_id===id),pets:db.pets.filter(p=>p.owner_id===id)};},
  async setRole(id,role){if(!['admin','manager','groomer','client'].includes(role))throw new ApiError('Неизвестная роль.',0);if(config.mode==='live')return request(`users/${id}/role`,{method:'PUT',body:{role}});return api.save('users',{role},id);},
  async slotInterval(value){if(config.mode==='demo'){if(value!==undefined)db.slotInterval=value;return {interval_minutes:db.slotInterval||30};}return request('slots/interval',value===undefined?{}:{method:'POST',body:{interval_minutes:value}});},
  async telegramCode(){if(config.mode!=='live')throw new ApiError('Привязка Telegram доступна после входа в настоящий аккаунт.',0);return request('users/link/code?provider=telegram',{method:'POST'});},
  reset(){db=structuredClone(seed);persist();}
};
