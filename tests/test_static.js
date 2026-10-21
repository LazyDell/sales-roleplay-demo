const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {createEngine,shuffled}=require('../frontend/static-engine.js');
const products=JSON.parse(fs.readFileSync('data/demo_products.json','utf8'));
const scenarios=['tob','toc'].flatMap(mode=>JSON.parse(fs.readFileSync(`scenarios/${mode}/scenarios.json`,'utf8')));
const data={products,scenarios,rubrics:{tob:[['需求',['担心']]],toc:[['需求',['需求']]]}};
const settings={scenario_id:'tob-pilot',product_id:'care-demo',engine:'mock',difficulty:'normal',seed:'test',reverse:false};
test('both modes complete with evidence and stop after finish',async()=>{
 for(const scenario of scenarios){const e=createEngine(data);let s=await e.request('/api/start',{...settings,scenario_id:scenario.id});s=await e.request('/api/chat',{session_id:s.id,message:'您担心什么？有什么需求？'});const r=await e.request('/api/finish',{session_id:s.id});assert.equal(r.review.turns,1);assert.ok(r.review.dimensions[0].evidence);await assert.rejects(e.request('/api/chat',{session_id:s.id,message:'继续'}));}
});
test('new session invalidates old and reverse does not score customer',async()=>{
 const e=createEngine(data),old=await e.request('/api/start',settings),s=await e.request('/api/start',{...settings,reverse:true,product_id:'travel-demo'});
 await assert.rejects(e.request('/api/chat',{session_id:old.id,message:'旧内容'}));
 const r=await e.request('/api/chat',{session_id:s.id,message:'介绍一下'});assert.match(r.messages.at(-1).content,/180/);assert.doesNotMatch(r.messages.at(-1).content,/360/);
 assert.deepEqual((await e.request('/api/finish',{session_id:s.id})).review.dimensions,[]);
});
test('reject live, empty input, excess turns and expired sessions',async()=>{
 const e=createEngine(data);await assert.rejects(e.request('/api/start',{...settings,engine:'live'}));const s=await e.request('/api/start',settings);
 await assert.rejects(e.request('/api/chat',{session_id:s.id,message:''}));
 for(let i=0;i<20;i++)await e.request('/api/chat',{session_id:s.id,message:'你好'});
 await assert.rejects(e.request('/api/chat',{session_id:s.id,message:'超限'}));
 const original=Date.now;try{Date.now=()=>original()+7200001;await assert.rejects(e.request('/api/finish',{session_id:s.id}));}finally{Date.now=original;}
});
test('seed ordering is repeatable and source data is not mutable through snapshots',async()=>{
 assert.deepEqual(shuffled(['a','b','c'],'seed'),shuffled(['a','b','c'],'seed'));
 const e=createEngine(data);const s=await e.request('/api/start',settings);s.product.name='edited';const next=await e.request('/api/chat',{session_id:s.id,message:'hello'});assert.equal(next.product.name,products[0].name);
});
