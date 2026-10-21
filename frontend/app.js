'use strict';
const $ = id => document.getElementById(id);
let catalog, mode='tob', session=null, review=null, busy=false;
function error(message){$('error').textContent=message;$('error').hidden=false;}
async function api(path,body){
 const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
 const data=await response.json(); if(!response.ok)throw new Error(data.error||'请求失败，请重试。');return data;
}
function setBusy(value){busy=value;const active=!!session&&!session.finished; $('start').disabled=value||!catalog;$('send').disabled=value||!active;$('finish').disabled=value||!active;$('message').disabled=value||!active;$('send').textContent=value?'处理中…':'发送 ↗';}
function option(select,value,text){const el=document.createElement('option');el.value=value;el.textContent=text;select.append(el);}
function setMode(next){mode=next;for(const m of ['tob','toc']){$(m).classList.toggle('active',m===mode);$(m).setAttribute('aria-pressed',String(m===mode));} $('modeHint').textContent=mode==='tob'?'与门店关键人沟通，推进合作试点。':'与车主沟通需求，帮助客户自主选择。';$('scenario').replaceChildren();catalog.scenarios.filter(s=>s.mode===mode).forEach(s=>option($('scenario'),s.id,s.subtitle));preview();}
function list(id,items){$(id).replaceChildren();for(const text of items){const li=document.createElement('li');li.textContent=text;$(id).append(li);}}
function context(s,p){$('contextText').textContent=s.context;$('goalText').textContent=s.goal;$('productName').textContent=p.name;$('price').textContent=p.price;list('facts',p.facts);list('exclusions',p.exclusions);}
function preview(){if(session)return;const s=catalog.scenarios.find(s=>s.id===$('scenario').value),p=catalog.products.find(p=>p.id===$('product').value);if(s&&p)context(s,p);}
function render(){
 $('chatTitle').textContent=session.scenario.title;$('engineBadge').textContent=session.engine==='mock'?'模拟模式':'真实模型';$('rolebar').textContent=`你：${session.user_role}　/　对方：${session.ai_role}`;
 $('sessionStatus').textContent=session.engine==='mock'?'模拟回复由规则生成':'回复来自配置的模型，请核对产品事实';
 $('messages').replaceChildren();for(const m of session.messages){const div=document.createElement('div');div.className='message '+(m.role==='user'?'user':'assistant');const label=document.createElement('small');label.textContent=m.role==='user'?'你 · '+session.user_role:session.ai_role;const p=document.createElement('p');p.textContent=m.content;div.append(label,p);$('messages').append(div);}
 $('messages').scrollTop=$('messages').scrollHeight;$('turns').textContent=`${session.messages.filter(m=>m.role==='user').length} 轮对话 / 最多 20 轮`;context(session.scenario,session.product);
}
$('tob').onclick=()=>{if(catalog)setMode('tob');};$('toc').onclick=()=>{if(catalog)setMode('toc');};$('scenario').onchange=preview;$('product').onchange=preview;
$('start').onclick=async()=>{if(busy)return;if(session&&!session.finished&&!confirm('重新开始会清空当前对话，继续吗？'))return;setBusy(true);$('error').hidden=true;
 try{session=await api('/api/start',{scenario_id:$('scenario').value,product_id:$('product').value,difficulty:$('difficulty').value,engine:$('engine').value,seed:$('seed').value,reverse:$('reverse').checked});review=null;$('review').hidden=true;$('message').value='';render();}catch(e){error(e.message);}finally{setBusy(false);}if(session&&!session.finished)$('message').focus();};
$('chatForm').onsubmit=async e=>{e.preventDefault();if(busy||!session||session.finished)return;const message=$('message').value.trim();if(!message)return;setBusy(true);$('error').hidden=true;try{session=await api('/api/chat',{session_id:session.id,message});$('message').value='';render();}catch(e){error(e.message);}finally{setBusy(false);$('message').focus();}};
$('message').onkeydown=e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();$('chatForm').requestSubmit();}};
$('finish').onclick=async()=>{if(busy||!session)return;setBusy(true);$('error').hidden=true;try{const data=await api('/api/finish',{session_id:session.id});session=data.session;review=data.review;render();$('reviewMethod').textContent=review.method;$('dimensions').replaceChildren();for(const d of review.dimensions){const card=document.createElement('div');card.className='dimension';const h=document.createElement('h3');h.textContent=d.name;const mark=document.createElement('span');mark.className='indicator';mark.textContent=d.observed?'● 已出现相关表达':'○ 尚未观察到';const quote=document.createElement('blockquote');quote.textContent=d.evidence?'“'+d.evidence+'”':'本轮没有匹配的原话';const tip=document.createElement('p');tip.textContent=d.suggestion;card.append(h,mark,quote,tip);$('dimensions').append(card);} $('nextStep').textContent=review.reverse_note||review.next_step;$('review').hidden=false;$('review').scrollIntoView({behavior:'smooth',block:'start'});}catch(e){error(e.message);}finally{setBusy(false);}};
$('export').onclick=()=>{if(!review)return;const {id,...publicSession}=session;const blob=new Blob([JSON.stringify({notice:'包含你输入的内容；分享前请自行检查个人信息。',session:publicSession,review},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='practice-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
api('/api/catalog').then(data=>{catalog=data;data.products.forEach(p=>option($('product'),p.id,p.name));if(data.live_available){$('engine').options[1].disabled=false;$('engine').options[1].textContent='真实模型 · 服务端已配置';}setMode('tob');setBusy(false);}).catch(()=>error('无法连接本地服务。请按 README 启动后刷新页面。'));
