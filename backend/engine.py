"""Synthetic scenarios, isolated sessions and evidence-based rule feedback."""
import copy
import json
import os
import random
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = json.loads((ROOT / 'data/demo_products.json').read_text())
SCENARIOS = sum([json.loads((ROOT / f'scenarios/{mode}/scenarios.json').read_text()) for mode in ('tob', 'toc')], [])
PROMPT = (ROOT / 'prompts/roleplay.md').read_text()
RUBRICS = {
 'tob': [('需求澄清', ['目前', '担心', '困难', '最关注', '工作量']), ('价值说明', ['检查', '清洁', '预约', '讲解']), ('责任边界', ['不包含', '不能保证', '分工', '责任', '未提供']), ('回应顾虑', ['理解', '担心', '确认', '顾虑']), ('下一步', ['试点', '复盘', '下次', '安排'])],
 'toc': [('需求探索', ['平时', '习惯', '需求', '出行', '预算']), ('产品匹配', ['检查', '清洁', '预约', '讲解']), ('边界告知', ['不包含', '不能保证', '不保证', '不含']), ('理解异议', ['理解', '担心', '考虑', '商量']), ('尊重选择', ['自主', '不买', '您决定', '再联系', '不着急'])]
}

class Engine:
 def __init__(self):
  self.sessions = {}
  self.lock = threading.RLock()

 def capabilities(self):
  return {'live_available': bool(os.getenv('MODEL_BASE_URL') and os.getenv('MODEL_NAME')), 'products': PRODUCTS, 'scenarios': SCENARIOS}

 def start(self, body):
  scenario = next((s for s in SCENARIOS if s['id'] == body.get('scenario_id')), None)
  product = next((p for p in PRODUCTS if p['id'] == body.get('product_id')), None)
  if not scenario or not product: raise ValueError('请选择有效的场景和产品。')
  mode = body.get('engine', 'mock')
  if mode not in ('mock', 'live'): raise ValueError('不支持的对话引擎。')
  if mode == 'live' and not self.capabilities()['live_available']: raise ValueError('服务端尚未配置真实模型。')
  difficulty = body.get('difficulty', 'normal')
  if difficulty not in ('normal', 'challenge'): raise ValueError('不支持的难度。')
  reverse = body.get('reverse', False)
  if not isinstance(reverse, bool): raise ValueError('角色参数无效。')
  seed = str(body.get('seed', 'demo'))[:64]
  concerns = list(scenario['concerns'])
  random.Random(seed).shuffle(concerns)
  user_role = scenario['counterpart'] if reverse else ('合作顾问' if scenario['mode'] == 'tob' else '服务顾问')
  ai_role = ('合作顾问' if scenario['mode'] == 'tob' else '服务顾问') if reverse else scenario['counterpart']
  opening = ('您好，您最关注哪方面的需求？我们可以先确认适用范围，再决定是否继续。' if reverse else scenario['opening'])
  session = {'id': secrets.token_urlsafe(24), 'scenario': copy.deepcopy(scenario), 'product': copy.deepcopy(product), 'engine': mode, 'difficulty': difficulty, 'reverse': reverse, 'seed': seed, 'concerns': concerns, 'user_role': user_role, 'ai_role': ai_role, 'messages': [{'role': 'assistant', 'content': opening}], 'finished': False, 'busy': False, 'created': time.time()}
  with self.lock:
   self.sessions = {k:v for k,v in self.sessions.items() if time.time()-v['created'] < 7200}
   if len(self.sessions) >= 100: raise ValueError('演示会话已满，请重启服务清理。')
   self.sessions[session['id']] = session
  return self.public(session)

 def get(self, sid):
  s = self.sessions.get(sid)
  if not s or time.time()-s['created'] >= 7200: raise ValueError('会话不存在或已过期，请重新开始。')
  return s

 def public(self, session):
  return copy.deepcopy({k:v for k,v in session.items() if k not in ('busy', 'created', 'concerns')})

 def chat(self, sid, message):
  if not isinstance(message, str) or not message.strip() or len(message) > 2000: raise ValueError('请输入 1–2000 字的消息。')
  message = message.strip()
  with self.lock:
   s = self.get(sid)
   if s['finished'] or s['busy']: raise ValueError('会话已结束或正在回复。')
   if len(s['messages']) >= 41: raise ValueError('本次演练已达 20 轮，请结束并复盘。')
   s['busy'] = True
   pending = s['messages'] + [{'role':'user', 'content':message}]
  try:
   reply = self.live(s, pending) if s['engine'] == 'live' else self.mock(s, message)
   with self.lock:
    s['messages'] = pending + [{'role':'assistant', 'content':reply}]
    return self.public(s)
  finally:
   with self.lock: s['busy'] = False

 def mock(self, s, message):
  if s['reverse']:
   if any(x in message for x in ('保证', '免费', '赔', '维修')):
    return '不能保证车辆不会故障。' + '；'.join(s['product']['exclusions']) + '。您最在意的是哪项服务？'
   return f"理解您的顾虑。{s['product']['name']}的{ s['product']['price']}，包含：{'；'.join(s['product']['facts'])}。您可以自主决定，不需要当场购买。"
  turn = sum(m['role']=='user' for m in s['messages'])
  if re.search(r'保证.*(?:收益|赚钱|不出问题)|全部免费|一定成交', message): return '这个承诺听起来太绝对了，产品卡里有明确写吗？请先解释限制。'
  if any(x in message for x in ('担心', '关注', '需求', '习惯', '预算', '困难')):
   response = '我主要担心实际用不上，以及后续谁来负责。' if s['scenario']['mode']=='toc' else '我最担心员工工作量，还有客户投诉时责任说不清。'
  elif any(x in message for x in ('不包含', '不能保证', '不保证', '不含', '责任')):
   response = '这样说边界就清楚一些了。下一步具体怎么安排？'
  elif any(x in message for x in ('试点', '复盘', '自主', '不着急', '您决定')):
   response = '可以，我们先把范围和安排确认下来，再决定是否继续。'
  else: response = s['concerns'][turn % len(s['concerns'])]
  if s['difficulty']=='challenge': response += '请给我一个具体、可以核对的说明。'
  return response

 def live(self, s, messages):
  base = os.environ['MODEL_BASE_URL'].rstrip('/')
  if not (base.startswith('https://') or base.startswith('http://127.0.0.1:') or base.startswith('http://localhost:')):
   raise ValueError('模型地址需要 HTTPS，或本机 HTTP 地址。')
  system = PROMPT + '\n' + json.dumps({'role':s['ai_role'], 'user_role':s['user_role'], 'scenario':s['scenario'], 'product':s['product'], 'difficulty':s['difficulty']}, ensure_ascii=False)
  payload = json.dumps({'model':os.environ['MODEL_NAME'], 'messages':[{'role':'system','content':system}]+messages, 'temperature':0.6}).encode()
  headers = {'Content-Type':'application/json'}
  if os.getenv('MODEL_API_KEY'): headers['Authorization'] = 'Bearer ' + os.environ['MODEL_API_KEY']
  request = urllib.request.Request(base + '/chat/completions', data=payload, headers=headers)
  # Never follow redirects with a model credential.
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self, *args, **kwargs): return None
  try:
   with urllib.request.build_opener(NoRedirect()).open(request, timeout=35) as response:
    data = response.read(1024*1024+1)
   if len(data)>1024*1024: raise ValueError('模型响应过大。')
   text = json.loads(data)['choices'][0]['message']['content']
   if not isinstance(text,str) or not text.strip(): raise ValueError('模型返回内容为空。')
   return text[:6000]
  except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
   raise ValueError('模型请求失败，请检查服务端配置或稍后重试；本轮未保存。') from exc

 def finish(self, sid):
  with self.lock:
   s = self.get(sid)
   if s['busy']: raise ValueError('请等待当前回复完成。')
   s['finished'] = True
   messages = [m['content'] for m in s['messages'] if m['role']=='user']
   dimensions=[]
   if not s['reverse']:
    for label, words in RUBRICS[s['scenario']['mode']]:
     evidence = next((m for m in messages if any(w in m for w in words)), '')
     dimensions.append({'name':label, 'observed':bool(evidence), 'evidence':evidence, 'suggestion': '尝试用一个具体问题或解释呈现这一环节。' if not evidence else '已出现相关表达，请检查它是否真正回应了对方。'})
   return {'session':self.public(s), 'review':{'method':'关键词覆盖提示，不是 AI 评分或能力测评；匹配可能包含否定或无关表达。', 'dimensions':dimensions, 'turns':len(messages), 'reverse_note':'角色互换时仅回顾对话，不给客户角色套用销售量表。' if s['reverse'] else '', 'next_step':'选一个未充分说明的环节，用具体问题重新练习。'}}
