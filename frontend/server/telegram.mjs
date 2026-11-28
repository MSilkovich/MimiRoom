import fs from 'node:fs';
import {salonFacts,redactContacts} from '../dist/support-core.js';
export function createTelegramHandler({agent,call,ownerId='',allowedChats=[],state={processed:[],paused:{}},persist=()=>{}}){
 const allowed=new Set(allowedChats.map(String));
 async function handle(update){
  if(!allowed.size)return {ignored:'allowlist_required'};
  const b=update.business_message,m=b||update.message;if(!m?.text||m.chat?.type!=='private')return {ignored:'not_text_private'};
  const chat=String(m.chat.id),connection=b?.business_connection_id;
  if(!allowed.has(chat))return {ignored:'chat_not_allowed'};
  const key=(connection||'bot')+':'+chat;
  if(b){if(!ownerId)return {ignored:'owner_required'};const info=await call('getBusinessConnection',{business_connection_id:connection});if(String(info.user?.id)!==String(ownerId)||!info.is_enabled||!(info.rights?.can_reply||info.can_reply))return {ignored:'connection_denied'};
   if(String(m.from?.id)===String(ownerId)){if(m.text==='/resume_ai'){delete state.paused[key];persist(state);return {resumed:true}}state.paused[key]=true;persist(state);return {paused:true}}
   if(m.date&&Date.now()/1000-m.date>86400)return {ignored:'old_business_message'};
  }
  if(m.from?.is_bot||state.paused[key])return {ignored:'paused_or_bot'};
  if(m.text==='/operator'||/администратор|оператор|живой человек/i.test(m.text)){state.paused[key]=true;persist(state);await call('sendMessage',{chat_id:m.chat.id,...(connection?{business_connection_id:connection}:{}),text:`Я ИИ-помощник МиМиРум. Автоответы в этом чате поставлены на паузу. Для связи с администратором студии: ${salonFacts.phone}.`});return {handoff:true}}
  const id=String(update.update_id);if(state.processed.includes(id))return {ignored:'duplicate'};
  // Claim before sending: a crash may lose a response, but will not generate repeated auto-replies.
  state.processed=[...state.processed.slice(-999),id];persist(state);
  state.conversations??={};const conversation=state.conversations[key]||{history:[],profile:null};const response=await agent.reply({message:m.text.slice(0,1600),history:conversation.history,profile:conversation.profile});state.conversations[key]={profile:response.profile,history:[...conversation.history,{role:'user',content:redactContacts(m.text).slice(0,600)},{role:'assistant',content:response.answer.slice(0,500)}].slice(-8),updated:Date.now()};for(const [old] of Object.entries(state.conversations).sort((a,b)=>b[1].updated-a[1].updated).slice(100))delete state.conversations[old];persist(state);
  const mode=response.mode==='ai'?'ИИ-помощник МиМиРум':'Справочник МиМиРум';
  const answer=response.handoff?`Поставила автоответы на паузу. С администратором студии можно связаться по телефону: ${salonFacts.phone}.`:response.answer.replaceAll('Нажмите «Выбрать окошко»','Откройте запись на сайте студии');
  if(response.handoff){state.paused[key]=true;persist(state)}
  await call('sendMessage',{chat_id:m.chat.id,...(connection?{business_connection_id:connection}:{}),text:(mode+'\n\n'+answer).slice(0,3900),link_preview_options:{is_disabled:true}});return {sent:true,mode:response.mode};
 }
 return {handle,state};
}
export async function startTelegram({agent,token,ownerId,allowedChats,stateFile,signal}){
 if(!token||!allowedChats.length)throw Error('Для пробного Telegram нужны токен и разрешённые chat_id.');
 const call=async(method,data={})=>{const r=await fetch(`https://api.telegram.org/bot${token}/${method}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal:signal||AbortSignal.timeout(35000)});const body=await r.json();if(!body.ok)throw Error('Telegram не выполнил запрос ('+r.status+').');return body.result};
 const webhook=await call('getWebhookInfo');if(webhook.url)throw Error('У бота уже настроен webhook. Этот пробный процесс его не меняет.');
 let state;try{state=JSON.parse(fs.readFileSync(stateFile))}catch{state={offset:0,processed:[],paused:{}}}
 const persist=s=>{fs.mkdirSync(new URL('./',stateFile),{recursive:true});fs.writeFileSync(stateFile,JSON.stringify(s),{mode:0o600})};
 const handler=createTelegramHandler({agent,call,ownerId,allowedChats,state,persist});
 while(!signal?.aborted){try{const updates=await call('getUpdates',{offset:state.offset,timeout:25,allowed_updates:['message','business_message']});for(const u of updates){await handler.handle(u);state.offset=u.update_id+1;persist(state)}}catch{if(signal?.aborted)break;console.error('Telegram временно недоступен; повтор через несколько секунд.');await new Promise(r=>setTimeout(r,5000))}}
}
