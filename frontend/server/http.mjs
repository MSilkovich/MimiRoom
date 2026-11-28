import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {startTelegram} from './telegram.mjs';
import {createAgent,BudgetGate} from './agent.mjs';
import {loadEnvironment} from './config.mjs';

const root=path.resolve(fileURLToPath(new URL('../dist/',import.meta.url)));
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.ttf':'font/ttf','.svg':'image/svg+xml'};
export function createSupportHandler(agent,{port=4180,coreBase='http://127.0.0.1:30010'}={}) {
  const upstream=new URL(coreBase);
  if(!['http:','https:'].includes(upstream.protocol)||upstream.username||upstream.password||upstream.search||upstream.hash)throw Error('CORE_API_URL должен быть HTTP(S)-адресом без учётных данных и параметров.');
  const buckets=new Map();
  return async(req,res)=>{
    const json=(status,data)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(JSON.stringify(data));};
    const readBody=async(limit)=>{const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>limit)return null;chunks.push(Buffer.from(chunk));}return Buffer.concat(chunks);};
    try {
      if(![`127.0.0.1:${port}`,`localhost:${port}`].includes(req.headers.host)){json(403,{error:'Недопустимый адрес сервера'});return;}
      const url=new URL(req.url,'http://127.0.0.1:'+port);
      if(!['GET','HEAD'].includes(req.method)&&req.headers.origin&&![`http://127.0.0.1:${port}`,`http://localhost:${port}`].includes(req.headers.origin)){json(403,{error:'Недопустимый источник запроса'});return;}
      // Same-origin bridge: upstream is configured by the developer, never by a browser request.
      if(url.pathname.startsWith('/api/v0.0.1/')){
        if(!['GET','HEAD','POST','PUT','DELETE'].includes(req.method)){json(405,{detail:'Метод не поддерживается'});return;}
        const target=new URL(upstream);target.pathname=upstream.pathname.replace(/\/$/,'')+url.pathname;target.search=url.search;
        const headers={Accept:'application/json'};
        for(const name of ['authorization','content-type'])if(req.headers[name])headers[name]=req.headers[name];
        const body=['GET','HEAD'].includes(req.method)?undefined:await readBody(131072);
        if(body===null){json(413,{detail:'Запрос слишком большой'});return;}
        let response;
        try{response=await fetch(target,{method:req.method,headers,body:body?.length?body:undefined,redirect:'manual',signal:AbortSignal.timeout(20000)});}
        catch{json(502,{detail:'Бэкенд студии недоступен. Проверьте CORE_API_URL и запуск core.'});return;}
        if(response.status>=300&&response.status<400){json(502,{detail:'API вернул перенаправление. Проверьте адрес core.'});return;}
        const data=req.method==='HEAD'?null:Buffer.from(await response.arrayBuffer());
        res.writeHead(response.status,{'Content-Type':response.headers.get('content-type')||'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(data);return;
      }
      if(url.pathname==='/api/support/status'&&req.method==='GET'){json(200,agent.status());return;}
      if(url.pathname==='/api/support/chat'&&req.method==='POST'){
        if(!req.headers['content-type']?.startsWith('application/json')){json(415,{error:'Требуется JSON'});return;}
        const ip=req.socket.remoteAddress||'local',now=Date.now(),bucket=(buckets.get(ip)||[]).filter(t=>now-t<60000);
        if(bucket.length>=10){json(429,{error:'Слишком много сообщений. Подождите минуту.'});return;}
        bucket.push(now);buckets.set(ip,bucket);
        const body=await readBody(16384);if(body===null){json(413,{error:'Сообщение слишком большое'});return;}
        let input;try{input=JSON.parse(body.toString('utf8'));}catch{json(400,{error:'Некорректный JSON'});return;}
        if(typeof input.message!=='string'||!input.message.trim()||input.message.length>1600){json(400,{error:'Отправьте сообщение до 1600 символов.'});return;}
        json(200,await agent.reply(input));return;
      }
      if(url.pathname.startsWith('/api/')){json(404,{error:'Метод не найден'});return;}
      if(!['GET','HEAD'].includes(req.method)){json(405,{error:'Метод не поддерживается'});return;}
      let name;try{name=decodeURIComponent(url.pathname);}catch{json(400,{error:'Некорректный путь'});return;}
      const file=path.resolve(root,'.'+(name.endsWith('/')?name+'index.html':name));
      if(!file.startsWith(root+path.sep)&&file!==root){json(403,{error:'Доступ запрещён'});return;}
      let stat;try{stat=fs.statSync(file);}catch{json(404,{error:'Файл не найден'});return;}
      if(!fs.realpathSync(file).startsWith(root+path.sep)||!stat.isFile()){json(404,{error:'Файл не найден'});return;}
      res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin'});
      if(req.method==='HEAD')res.end();else fs.createReadStream(file).pipe(res);
    }catch{if(!res.headersSent)json(500,{error:'Не удалось обработать запрос. Попробуйте ещё раз.'});else res.end();}
  };
}
export function start(){
  loadEnvironment();const port=Number(process.env.SUPPORT_PORT||4180),host=process.env.SUPPORT_HOST||'127.0.0.1';
  if(!Number.isInteger(port)||port<1||port>65535)throw Error('SUPPORT_PORT должен быть от 1 до 65535.');
  const agent=createAgent({key:process.env.GROQ_API_KEY||'',enabled:process.env.AI_ENABLED==='true',model:process.env.AI_MODEL||'openai/gpt-oss-20b',budget:new BudgetGate({file:fileURLToPath(new URL('../.data/ai-budget.json',import.meta.url))})});
  const server=http.createServer(createSupportHandler(agent,{port,coreBase:process.env.CORE_API_URL||'http://127.0.0.1:30010'}));
  server.on('error',error=>{console.error(error.code==='EADDRINUSE'?`Порт ${port} занят. Измените SUPPORT_PORT.`:'Не удалось запустить сервер: '+error.code);process.exitCode=1;});
  server.listen(port,host,()=>{
    if(process.env.TELEGRAM_ENABLED==='true')startTelegram({agent,token:process.env.TELEGRAM_BOT_TOKEN,ownerId:process.env.TELEGRAM_BUSINESS_OWNER_ID,allowedChats:(process.env.TELEGRAM_ALLOWED_CHAT_IDS||'').split(',').filter(Boolean),stateFile:new URL('../.data/telegram-state.json',import.meta.url)}).catch(()=>console.error('Telegram не подключён. Проверьте токен, разрешённые чаты и webhook.'));
    console.log(`МиМиРум: http://127.0.0.1:${port}/client/ · ${agent.status().configured?'Groq подключён':'Справочный режим'} · core: ${process.env.CORE_API_URL||'http://127.0.0.1:30010'}`);
  });return server;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)start();
