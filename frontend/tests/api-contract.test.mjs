import {test,beforeEach} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const storage=new Map();
globalThis.localStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)};
globalThis.sessionStorage=globalThis.localStorage;
const {api,config,salonDateParts}=await import('../dist/api.js');
const schema=JSON.parse(fs.readFileSync(new URL('../docs/openapi.json',import.meta.url))).components.schemas;
const sample={booking_id:42,service_id:3,master_id:7,start_time:'2026-12-01T09:00:00Z',end_time:'2026-12-01T10:00:00Z',client_id:11,pet_id:4,client_name:'Клиент',client_phone:null,status:'pending',comment:null,options:{},created_at:'2026-11-28T09:00:00Z',updated_at:'2026-11-28T09:00:00Z'};
const response=(value,status=200)=>new Response(value===undefined?undefined:JSON.stringify(value),{status});
function contract(name,body){const s=schema[name];for(const key of s.required||[])assert.ok(key in body,`Missing ${name}.${key}`);for(const key of Object.keys(body))assert.ok(key in s.properties,`Unexpected ${name}.${key}`);}
beforeEach(()=>{storage.clear();config.mode='live';config.base='https://api.example.test';config.token='test-token';});
test('booking create follows the new JSON contract and normalizes Moscow dates',async()=>{
 globalThis.fetch=async(url,options)=>{assert.equal(url,'https://api.example.test/api/v0.0.1/bookings');assert.equal(options.method,'POST');const body=JSON.parse(options.body);contract('BookingCreate',body);assert.equal(body.start_time,'2026-12-01T12:00:00+03:00');assert.ok(!('status' in body));assert.ok(!('date' in body));return response(sample);};
 const b=await api.save('book',{master_id:7,service_id:3,pet_id:4,client_id:11,date:'2026-12-01',time:'12:00',status:'pending'});
 assert.equal(b.book_id,42);assert.equal(b.date,'2026-12-01');assert.equal(b.time,'12:00:00');
 assert.deepEqual(salonDateParts('2026-12-01T22:30:00Z'),{date:'2026-12-02',time:'01:30:00'});
});
test('existing bookings cannot silently pretend to move through BookingUpdate',async()=>{
 let called=false;globalThis.fetch=async()=>{called=true;};await assert.rejects(api.save('book',{date:'2026-12-02'},42),/не поддерживает перенос/);assert.equal(called,false);
 globalThis.fetch=async(url,options)=>{assert.equal(options.method,'PUT');contract('BookingUpdate',JSON.parse(options.body));return response(sample);};await api.save('book',{comment:'Бережно',status:'confirmed'},42);
});
test('cancellation and completion use dedicated POST actions and retain records',async()=>{
 const paths=[];globalThis.fetch=async(url,options)=>{paths.push(url);assert.equal(options.method,'POST');assert.equal(options.body,undefined);return response({...sample,status:url.endsWith('cancel')?'cancelled':'completed'});};
 assert.equal((await api.cancelBooking(42)).status,'cancelled');assert.equal((await api.completeBooking(42)).status,'completed');assert.ok(paths[0].endsWith('/bookings/42/cancel'));assert.ok(paths[1].endsWith('/bookings/42/complete'));
});
test('availability is a POST body and keeps the exact server timestamp',async()=>{
 globalThis.fetch=async(url,options)=>{assert.ok(url.endsWith('/slots/available'));assert.equal(options.method,'POST');const body=JSON.parse(options.body);contract('SlotsAvailableRequest',body);assert.deepEqual(body,{service_id:3,date_from:'2026-12-01',date_to:'2026-12-14',pet_id:4});return response([{master_id:7,service_id:3,start_time:sample.start_time,end_time:sample.end_time},{master_id:8,service_id:3,start_time:sample.start_time,end_time:sample.end_time,available:false}]);};
 const slots=await api.availableSlots({service_id:3,date_from:'2026-12-01',date_to:'2026-12-14',pet_id:4,master_id:null,client_id:100});assert.equal(slots.length,1);assert.equal(slots[0].time,'12:00:00');assert.equal(slots[0].start_time,sample.start_time);
});
test('scoped bookings and pet history use new resources and booking_id pagination',async()=>{
 const paths=[];globalThis.fetch=async(url)=>{paths.push(url);return response([sample]);};
 await api.list('book',{client_id:11,status:'pending'});const history=await api.petHistory(4);assert.match(paths[0],/\/bookings\?client_id=11&status=pending/);assert.match(paths[1],/\/pets\/4\/history\?/);assert.equal(history[0].book_id,42);
});
test('registration never sends role or unrelated profile fields',async()=>{
 globalThis.fetch=async(url,options)=>{assert.ok(url.endsWith('/auth/register'));assert.ok(!options.headers.Authorization);const body=JSON.parse(options.body);contract('RegisterRequest',body);assert.deepEqual(body,{login:'guest',password:'test12345',name:'Иван',surname:'Иванов'});return response({access_token:'new',refresh_token:'refresh',expires_in:3600,user_id:11});};
 await api.register('',{login:'guest',password:'test12345',name:'Иван',surname:'Иванов',role:'admin',phone:'123'});assert.equal(config.mode,'live');assert.equal(storage.get('mimiroom-user'),'11');
});
test('failed login leaves the old endpoint and session intact',async()=>{
 globalThis.fetch=async()=>response({detail:'Неверный пароль'},401);await assert.rejects(api.login('https://other.example','guest','bad'),/Неверный пароль/);assert.equal(config.base,'https://api.example.test');assert.equal(config.token,'test-token');
});
test('simultaneous expired requests share one token refresh',async()=>{
 storage.set('mimiroom-refresh','old-refresh');let refreshes=0;
 globalThis.fetch=async(url,options)=>{
  if(url.endsWith('/auth/refresh')){refreshes++;await new Promise(resolve=>setTimeout(resolve,10));return response({access_token:'fresh',refresh_token:'new-refresh',expires_in:3600,user_id:11});}
  if(options.headers.Authorization!=='Bearer fresh')return response({detail:'expired'},401);
  return response([{user_id:11,name:'Иван',role:'client'}]);
 };
 const results=await Promise.all([api.list('users'),api.list('users')]);assert.equal(refreshes,1);assert.equal(results[0].length,1);assert.equal(config.token,'fresh');
});
test('validation errors expose field names and conflict status is preserved',async()=>{
 globalThis.fetch=async()=>response({detail:[{loc:['body','name'],msg:'Field required'}]},422);await assert.rejects(api.save('pets',{}),error=>error.status===422&&error.message==='name: Field required');
 globalThis.fetch=async()=>response({detail:'Время уже занято'},409);await assert.rejects(api.save('book',{service_id:3,master_id:7,start_time:sample.start_time}),error=>error.status===409);
});
test('masters, schedules, buffers, required contacts and role writes match schema',async()=>{
 const types=['MasterCreate','WorkScheduleCreate','ServiceCreate','UserCreate','UserRoleUpdate'];let index=0;
 globalThis.fetch=async(url,options)=>{contract(types[index++],JSON.parse(options.body));return response({user_id:7,work_schedule_id:2,service_id:3});};
 await api.save('masters',{login:'groomer',password:'test123',name:'Мастер',surname:'Тест',service_ids:[3]});
 await api.save('work-schedules',{master_id:7,weekday:0,start_time:'09:00:00',end_time:'18:00:00',is_day_off:false});
 await api.save('services',{title:'Уход',price:'3500',duration:'PT60M',duration_minutes:60,buffer_before_minutes:10,buffer_after_minutes:15,master_ids:[7],consumables:[{consumable_id:1,volume:2}]});
 await api.save('users',{login:'guest',password:'test123',name:'Имя',surname:'Фамилия'});await api.setRole(7,'manager');assert.equal(index,5);
});
test('Telegram link creation is authenticated and has no external-id guessing',async()=>{
 globalThis.fetch=async(url,options)=>{assert.ok(url.endsWith('/users/link/code?provider=telegram'));assert.equal(options.method,'POST');assert.equal(options.body,undefined);assert.equal(options.headers.Authorization,'Bearer test-token');return response({code:'one-use',expires_in:300,deep_link:'https://t.me/test_bot?start=one-use'});};
 assert.equal((await api.telegramCode()).expires_in,300);
});
test('logout clears browser credentials even if core cannot be reached',async()=>{
 storage.set('mimiroom-token','secret');globalThis.fetch=async()=>{throw Error('offline')};await assert.rejects(api.logout());assert.equal(config.token,'');assert.equal(config.mode,'demo');assert.equal(storage.get('mimiroom-token'),undefined);
});
