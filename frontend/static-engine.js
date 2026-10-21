/* Browser-only rule simulator. No network calls, credentials or persistence. */
(function(root){
'use strict';
const clone=value=>JSON.parse(JSON.stringify(value));
function shuffled(items,seed){
 let h=2166136261;
 for(const ch of seed){h=Math.imul(h^ch.charCodeAt(0),16777619)>>>0;}
 const result=[...items];
 for(let i=result.length-1;i>0;i--){h=(Math.imul(h,1664525)+1013904223)>>>0;const j=h%(i+1);[result[i],result[j]]=[result[j],result[i]];}
 return result;
}
function createEngine(data){
 let current=null;
 function publicSession(){const {created,concerns,...s}=current;return clone(s);}
 function get(id){if(!current||current.id!==id||Date.now()-current.created>=7200000)throw new Error('会话已过期，请重新开始。');return current;}
 function start(b){
  const scenario=data.scenarios.find(s=>s.id===b.scenario_id), product=data.products.find(p=>p.id===b.product_id);
  if(!scenario||!product)throw new Error('请选择有效的场景和产品。');
  if(b.engine!=='mock')throw new Error('在线版仅提供规则模拟，真实模型请使用本地版。');
  if(!['normal','challenge'].includes(b.difficulty)||typeof b.reverse!=='boolean')throw new Error('训练设置无效。');
  const advisor=scenario.mode==='tob'?'合作顾问':'服务顾问';
  const seed=String(b.seed||'demo').slice(0,64);
  current={id:root.crypto.randomUUID(),created:Date.now(),scenario:clone(scenario),product:clone(product),engine:'mock',difficulty:b.difficulty,seed,reverse:b.reverse,concerns:shuffled(scenario.concerns,seed),user_role:b.reverse?scenario.counterpart:advisor,ai_role:b.reverse?advisor:scenario.counterpart,finished:false,messages:[{role:'assistant',content:b.reverse?'您好，您最关注哪方面的需求？我们可以先确认适用范围，再决定是否继续。':scenario.opening}]};
  return publicSession();
 }
 function reply(s,message){
  const has=words=>words.some(w=>message.includes(w));
  if(s.reverse){
   if(has(['保证','免费','赔','维修']))return '不能保证车辆不会故障。'+s.product.exclusions.join('；')+'。您最在意的是哪项服务？';
   return `理解您的顾虑。${s.product.name}的${s.product.price}，包含：${s.product.facts.join('；')}。您可以自主决定，不需要当场购买。`;
  }
  if(/保证.*(?:收益|赚钱|不出问题)|全部免费|一定成交/.test(message))return '这个承诺听起来太绝对了，产品卡里有明确写吗？请先解释限制。';
  let response;
  if(has(['担心','关注','需求','习惯','预算','困难']))response=s.scenario.mode==='toc'?'我主要担心实际用不上，以及后续谁来负责。':'我最担心员工工作量，还有客户投诉时责任说不清。';
  else if(has(['不包含','不能保证','不保证','不含','责任']))response='这样说边界就清楚一些了。下一步具体怎么安排？';
  else if(has(['试点','复盘','自主','不着急','您决定']))response='可以，我们先把范围和安排确认下来，再决定是否继续。';
  else response=s.concerns[s.messages.filter(m=>m.role==='user').length%s.concerns.length];
  return response+(s.difficulty==='challenge'?'请给我一个具体、可以核对的说明。':'');
 }
 function chat(b){
  const s=get(b.session_id);
  if(s.finished)throw new Error('会话已结束，请重新开始。');
  if(typeof b.message!=='string'||!b.message.trim()||b.message.length>2000)throw new Error('请输入 1–2000 字的消息。');
  if(s.messages.length>=41)throw new Error('本次演练已达 20 轮，请结束并复盘。');
  const message=b.message.trim(),text=reply(s,message);
  s.messages.push({role:'user',content:message},{role:'assistant',content:text});return publicSession();
 }
 function finish(b){
  const s=get(b.session_id);s.finished=true;
  const messages=s.messages.filter(m=>m.role==='user').map(m=>m.content);
  const dimensions=s.reverse?[]:data.rubrics[s.scenario.mode].map(([name,words])=>{
   const evidence=messages.find(m=>words.some(w=>m.includes(w)))||'';
   return {name,observed:!!evidence,evidence,suggestion:evidence?'已出现相关表达，请检查它是否真正回应了对方。':'尝试用一个具体问题或解释呈现这一环节。'};
  });
  return {session:publicSession(),review:{method:'关键词覆盖提示，不是 AI 评分或能力测评；匹配可能包含否定或无关表达。',dimensions,turns:messages.length,reverse_note:s.reverse?'角色互换时仅回顾对话，不给客户角色套用销售量表。':'',next_step:'选一个未充分说明的环节，用具体问题重新练习。'}};
 }
 return {request:async(path,body)=>{
  if(path==='/api/catalog')return clone({products:data.products,scenarios:data.scenarios,live_available:false});
  if(path==='/api/start')return start(body);
  if(path==='/api/chat')return chat(body);
  if(path==='/api/finish')return finish(body);
  throw new Error('不支持的演示操作。');
 }};
}
if(typeof module!=='undefined'&&module.exports)module.exports={createEngine,shuffled};
if(root.DEMO_DATA)root.RoleplayStatic=createEngine(root.DEMO_DATA);
})(globalThis);
