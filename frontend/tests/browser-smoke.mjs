import assert from 'node:assert/strict';
import http from 'node:http';
import {once} from 'node:events';
import {chromium} from 'playwright';
import {createSupportHandler} from '../server/http.mjs';
import {createAgent} from '../server/agent.mjs';
import {seed} from '../dist/data.js';
const requests=[],books=[];let conflict=true;
const date=new Date(Date.now()+86400000).toLocaleDateString('sv-SE',{timeZone:'Europe/Moscow'});
const slot={master_id:1,service_id:1,start_time:date+'T12:00:00+03:00',end_time:date+'T14:00:00+03:00',available:true};
const master={...seed.users[0],services:[{service_id:1,title:'Комплексный уход'}]};
const core=http.createServer(async(req,res)=>{
 let raw='';for await(const chunk of req)raw+=chunk;const body=raw?JSON.parse(raw):null;
 const url=new URL(req.url,'http://localhost'),path=url.pathname.replace('/api/v0.0.1/','');requests.push({path,method:req.method,body,query:url.search});
 let result=[];res.setHeader('Content-Type','application/json');
 if(path==='users/11')result={...seed.users.find(u=>u.user_id===11),role:req.headers.authorization?.includes('admin')?'admin':req.headers.authorization?.includes('manager')?'manager':req.headers.authorization?.includes('groomer')?'groomer':'client',pets:seed.pets.filter(p=>p.owner_id===11)};
 else if(path==='users')result=seed.users;
 else if(path==='masters')result=[master];
 else if(path==='services')result=seed.services.map(s=>({...s,masters:[master],consumables:[],buffer_before_minutes:0,buffer_after_minutes:15}));
 else if(path==='slots/available')result=[slot];
 else if(path==='bookings'&&req.method==='POST'){
  if(conflict){conflict=false;res.statusCode=409;result={detail:'Окошко уже занято. Выберите другое время.'};}
  else{result={...body,booking_id:77,end_time:slot.end_time,status:'pending',client_id:11};books.push(result);}
 }else if(path==='bookings')result=books;
 else if(path==='bookings/77/cancel'){books[0].status='cancelled';res.statusCode=204;res.end();return;}
 else if(path==='users/link/code')result={code:'test-only',expires_in:60,deep_link:'https://t.me/mimiroom_test_bot?start=test-only'};
 else if(path.endsWith('/history'))result=[];
 else if(path==='slots/interval')result={interval_minutes:30};
 else if(path==='work-schedules')result=[{work_schedule_id:1,master_id:1,weekday:0,start_time:'10:00:00',end_time:'19:00:00',is_day_off:false}];
 else result=seed[path]||[];
 res.end(JSON.stringify(result));
});
core.listen(0,'127.0.0.1');await once(core,'listening');
let server;server=http.createServer((req,res)=>createSupportHandler(createAgent(),{port:server.address().port,coreBase:`http://127.0.0.1:${core.address().port}`})(req,res));server.listen(0,'127.0.0.1');await once(server,'listening');
const base=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});const errors=[];
async function pageFor(role,portal='studio',width=1440){const context=await browser.newContext({viewport:{width,height:1000}});await context.addInitScript(role=>{sessionStorage.setItem('mimiroom-token',role);sessionStorage.setItem('mimiroom-user','11');sessionStorage.setItem('mimiroom-mode','live');},role);const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/'+portal+'/');await page.waitForFunction(()=>!document.querySelector('.loading'));return page;}
try{
 const page=await pageFor('client','client');await page.locator('[data-c-book]').first().click();await page.locator('#w-next').click();await page.locator('#w-next').click();await page.locator('[data-w-date="'+date+'"]').click();await page.locator('[data-w-time="12:00"]').click();await page.locator('#w-next').click();await page.locator('#w-consent').check();await page.locator('#w-next').click();await page.waitForFunction(()=>document.querySelector('#w-error')?.textContent.includes('заняли'));
 await page.locator('[data-w-time="12:00"]').click();await page.locator('#w-next').click();await page.locator('#w-consent').check();await page.locator('#w-next').click();await page.locator('#success-visits').waitFor();assert.equal(books[0].start_time,slot.start_time);await page.locator('#success-visits').click();await page.locator('[data-c-cancel="77"]').click();await page.locator('#cancel-visit').click();await page.waitForFunction(()=>document.querySelector('[data-c-filter="history"]'));assert.equal(books[0].status,'cancelled');
 assert(!requests.some(r=>r.path==='users'&&r.method==='GET'),'client must not load all users');
 const mobile=await pageFor('client','client',390);assert(await mobile.locator('[data-c-book]').first().isVisible());assert(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'mobile overflow');
 const admin=await pageFor('admin');for(const tab of ['team','work-schedules','services','access','settings']){await admin.locator(`[data-page="${tab}"]`).click();assert(!await admin.locator('.error').filter({hasText:/TypeError/}).count());}await admin.locator('[data-page="team"]').click();await admin.locator('[data-team-new]').click();assert(await admin.locator('form').isVisible());await admin.keyboard.press('Escape');
 const manager=await pageFor('manager');assert.equal(await manager.locator('[data-page="access"]').count(),0);await manager.locator('[data-page="work-schedules"]').click();assert(await manager.locator('[data-schedule-new]').isVisible());
 const groomer=await pageFor('groomer');assert.equal(await groomer.locator('[data-page="clients"]').count(),0);await groomer.locator('[data-page="work-schedules"]').click();assert.equal(await groomer.locator('[data-schedule-new]').count(),0);
 assert.deepEqual(errors,[]);console.log('Browser smoke passed: live slots, 409 recovery, booking, cancellation, mobile, four roles, management forms.');
}finally{await browser.close();for(const s of [server,core]){s.closeAllConnections();await new Promise(resolve=>s.close(resolve));}}
