import {test} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {once} from 'node:events';
import {createSupportHandler} from '../server/http.mjs';
import {createAgent} from '../server/agent.mjs';

test('same-origin core proxy preserves JWT, query, payload, conflict and 204',async()=>{
 const received=[];
 const core=http.createServer(async(req,res)=>{let body='';for await(const chunk of req)body+=chunk;received.push({url:req.url,method:req.method,authorization:req.headers.authorization,body});if(req.url.includes('/cancel')){res.writeHead(204);res.end();}else{res.writeHead(409,{'Content-Type':'application/json'});res.end(JSON.stringify({detail:'Окошко занято'}));}});
 core.listen(0,'127.0.0.1');await once(core,'listening');const corePort=core.address().port;
 let frontend;frontend=http.createServer((req,res)=>createSupportHandler(createAgent(),{port:frontend.address().port,coreBase:`http://127.0.0.1:${corePort}`})(req,res));frontend.listen(0,'127.0.0.1');await once(frontend,'listening');const base=`http://127.0.0.1:${frontend.address().port}`;
 try{
  const res=await fetch(base+'/api/v0.0.1/bookings?master_id=7',{method:'POST',headers:{Authorization:'Bearer test-only','Content-Type':'application/json'},body:JSON.stringify({service_id:3})});assert.equal(res.status,409);assert.equal((await res.json()).detail,'Окошко занято');assert.deepEqual(received[0],{url:'/api/v0.0.1/bookings?master_id=7',method:'POST',authorization:'Bearer test-only',body:'{"service_id":3}'});
  assert.equal((await fetch(base+'/api/v0.0.1/bookings/42/cancel',{method:'POST'})).status,204);
  const denied=await fetch(base+'/api/v0.0.1/bookings',{method:'POST',headers:{Origin:'https://foreign.example'}});assert.equal(denied.status,403);assert.equal(received.length,2);
 }finally{frontend.closeAllConnections();core.closeAllConnections();await Promise.all([new Promise(r=>frontend.close(r)),new Promise(r=>core.close(r))]);}
});
