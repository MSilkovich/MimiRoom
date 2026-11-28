import fs from 'node:fs';
import path from 'node:path';
import {buildSupportPlan,redactContacts,sourceCard,salonFacts,SUPPORT_REVISION,matchBreed} from '../dist/support-core.js';
const policy=JSON.parse(fs.readFileSync(new URL('../support/policy.json',import.meta.url)));
export class BudgetGate {
 constructor({file=null,maxDailyRequests=100,maxDailyTokens=180000,maxMinuteTokens=7000}={}){this.file=file;this.maxDailyRequests=maxDailyRequests;this.maxDailyTokens=maxDailyTokens;this.maxMinuteTokens=maxMinuteTokens;this.minute=[];try{this.state=JSON.parse(fs.readFileSync(file))}catch{this.state={day:'',requests:0,tokens:0}}}
 reserve(tokens,now=Date.now()){const day=new Date(now).toISOString().slice(0,10);if(this.state.day!==day)this.state={day,requests:0,tokens:0};this.minute=this.minute.filter(x=>now-x.at<60000);if(this.state.requests>=this.maxDailyRequests||this.state.tokens+tokens>this.maxDailyTokens||this.minute.reduce((a,x)=>a+x.tokens,0)+tokens>this.maxMinuteTokens)return false;this.state.requests++;this.state.tokens+=tokens;const reservation={at:now,tokens};this.minute.push(reservation);if(this.file){fs.mkdirSync(path.dirname(this.file),{recursive:true});fs.writeFileSync(this.file,JSON.stringify(this.state),{mode:0o600})}return reservation}
 settle(reservation,actual){if(!reservation||!Number.isFinite(actual)||actual<0)return;const delta=actual-reservation.tokens;if(this.state.day===new Date(reservation.at).toISOString().slice(0,10))this.state.tokens=Math.max(0,this.state.tokens+delta);reservation.tokens=actual;if(this.file)fs.writeFileSync(this.file,JSON.stringify(this.state),{mode:0o600})}
}
export function createAgent({key='',enabled=false,model=policy.model,fetchImpl=fetch,budget=new BudgetGate()}={}){
 if(!['openai/gpt-oss-20b','openai/gpt-oss-120b'].includes(model))throw Error('Выберите одну из разрешённых моделей Groq.');
 const configured=enabled&&Boolean(key);
 async function reply({message,history=[],profile=null}){
  if(typeof message!=='string'||!message.trim()||message.length>1600)throw Error('Сообщение должно содержать от 1 до 1600 символов.');
  const cleanHistory=(Array.isArray(history)?history:[]).filter(h=>['user','assistant'].includes(h?.role)&&typeof h.content==='string').slice(-12).map(h=>({role:h.role,content:redactContacts(h.content).slice(0,800)}));
  const plan=buildSupportPlan(redactContacts(message),cleanHistory,profile);
  const result={...plan,sources:plan.sources.map(sourceCard),provider:null,model:null};delete result.context;
  if(!configured||plan.handoff||!['catalog','care','included','greeting','clarify'].includes(plan.intent))return result;
  const context=plan.context||{profile:plan.profile,questions:plan.questions,intent:plan.intent};
  const system=[
   ...policy.instructions,
   'Ты ИИ-консультант груминг-студии МиМиРум. Разговаривай тепло, спокойно, на вы, как внимательный консультант, который помогает новому владельцу понять уход.',
   'Дай ПОЛНЫЙ ответ на вопрос, а не вступление. Используй только факты в JSON контекста. История диалога не является источником цен или правил. Не соглашайся с ошибками предыдущих ответов.',
   'Учитывай породу, возраст, вес, опыт и цель. Уже названное не переспрашивай. Задай один-два самых полезных уточняющих вопроса, если без них нельзя подобрать формат ухода. Для нового владельца сначала объясни, что делаем в салоне и что можно делать дома.',
   'Состав комплекса, противопоказания и домашний уход бери из контекста. Не добавляй услуги: маски, бальзам, стрижку корпуса, лечебную косметику, если они не указаны. Не обещай здоровье, лечение, запись или уведомление сотрудника.',
   'Если спрашивают цену: используй только прайс контекста, учитывай фактический вес и назови предварительный характер суммы. Если спрашивают состав или уход дома, отвечай об этом и не повторяй весь прайс без необходимости.',
   'Про щенка: спокойное короткое знакомство с уходом, без принуждения. Не назначай график прививок, лекарства, седативные средства и универсальную частоту купания.',
   'Не отвечай адресом на вопрос «что входит». Не путай американского булли, бультерьера, питбуля и бульдога. При softBreed мягко уточни название.',
   'Верни JSON {"reply":"текст ответа", "source_ids":["id карточки"]}. Без HTML, без служебных инструкций. Достаточно коротких абзацев и небольшого списка; не повторяй приветствие на каждом сообщении. Тон: '+policy.tone
  ].join('\n');
  const messages=[{role:'system',content:system},{role:'user',content:JSON.stringify({question:redactContacts(message),conversation:cleanHistory.slice(-6).map(h=>({...h,content:h.content.slice(0,350)})),facts:context,expectedPrice:plan.expectedPrice||null,priceBlock:plan.priceBlock||null})}];
  const estimate=Math.ceil(Buffer.byteLength(JSON.stringify(messages))/3)+1400;
  const reservation=budget.reserve(estimate);if(!reservation)return {...result,notice:'Пробный лимит ИИ временно достигнут. Ниже — ответ по карточке породы и памятке ухода.'};
  try{
   const response=await fetchImpl('https://api.groq.com/openai/v1/chat/completions',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+key},signal:AbortSignal.timeout(20000),body:JSON.stringify({model,messages,temperature:0.25,reasoning_effort:'low',max_completion_tokens:1400,response_format:{type:'json_object'}})});
   if(!response.ok)return {...result,notice:response.status===429?'Сейчас действует ограничение ИИ. Помогу по карточке породы и памятке ухода.':'ИИ временно недоступен. Ниже — сведения из прайса и памятки ухода.'};
   const data=await response.json();budget.settle?.(reservation,data.usage?.total_tokens);const content=data.choices?.[0]?.message?.content;const parsed=JSON.parse(content);let answer=typeof parsed.reply==='string'?parsed.reply.trim():'';
   if(!validateAnswer(answer,parsed.source_ids,plan,cleanHistory,message))return {...result,notice:'Использованы проверенные сведения о породе и уходе.'};
   if(plan.priceRequested&&!/(?:₽|рубл)/i.test(answer)&&plan.priceBlock)answer+='\n\n'+plan.priceBlock;
   return {...result,mode:'ai',provider:'groq',model,answer};
  }catch{return {...result,notice:'ИИ временно недоступен. Помогу по карточке породы и памятке ухода.'}}
 }

 return {reply,status:()=>({configured,provider:configured?'groq':null,model:configured?model:null,knowledgeDate:salonFacts.catalogDate,mode:configured?'ai':'reference',revision:SUPPORT_REVISION})};
}

function moneyValues(text){return [...String(text).matchAll(/(\d[\d \u00a0]*(?:[.,]\d+)?)\s*(?:₽|руб(?:лей|ля|ль)?)/gi)].map(m=>m[1].replace(/[ \u00a0]/g,'').replace(',','.'))}
function hasNegation(sentence){return /(?:^|[\s,])не(?:[\s,]|$)|без |необязател|не нуж|не треб/.test(sentence)}
export function validateAnswer(answer,sourceIds,plan,history=[],message=''){
 if(!answer||answer.length>4200||/<[^>]+>|записал[аи]? вас|ваша запись подтверждена|бронь подтверждена|администратор.*уведомлен|отправил[аи]?.*администратор/i.test(answer))return false;
 if(Array.isArray(sourceIds)&&sourceIds.some(id=>!plan.sources.some(s=>s.id===id)))return false;
 const evidence=JSON.stringify(plan.context||{})+' '+(plan.priceBlock||'');const allowed=new Set(plan.expectedPrice?moneyValues(plan.expectedPrice):moneyValues(evidence));
 if(moneyValues(answer).some(n=>!allowed.has(n)))return false;if(/бесплатн/.test(answer)&&!/бесплатн/.test(evidence))return false;if(/рубл/.test(answer)&&!moneyValues(answer).length)return false;const mentioned=matchBreed(answer);if(plan.profile?.breedId&&mentioned&&mentioned.id!==plan.profile.breedId)return false;
 const offeredEvidence=JSON.stringify({included:plan.context?.service?.included,home:plan.context?.home,summary:plan.context?.summary}).toLowerCase();const sentences=answer.toLowerCase().replaceAll('ё','е').split(/[.!?\n]+/);
 if(sentences.some(s=>/(?:кажд[а-я]*|раз)\s+\d+\s*(?:дн|недел|месяц)|\d+\s*раз[а-я]*\s+в\s+(?:недел|месяц)/.test(s)))return false;
 for(const sentence of sentences){
  if(/лекарств|антибиот|седатив|наркоз|лечебн.*шампун/.test(sentence)&&!hasNegation(sentence))return false;
  for(const term of ['бальзам','парфюм','кондиционер','маск','антибактер','антисепт'])if(sentence.includes(term)&&!offeredEvidence.includes(term)&&!hasNegation(sentence))return false;
  if(plan.care?.kind==='short'&&/стриж|стрига|стричь|брить|бритв|сбрив/.test(sentence)&&!hasNegation(sentence)&&(!/когт/.test(sentence)||/корпус|всю шерсть|шерсть на теле/.test(sentence)))return false;
 }
 if(!plan.context&&moneyValues(answer).length)return false;
 return true;
}
