import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from backend.engine import Engine, PRODUCTS, SCENARIOS
from backend.server import Handler, ThreadingHTTPServer

class EngineTests(unittest.TestCase):
 def setUp(self):self.e=Engine()
 def start(self,**kw):return self.e.start({'scenario_id':'tob-pilot','product_id':'care-demo',**kw})
 def test_both_modes_end_to_end(self):
  for scenario in SCENARIOS:
   s=self.start(scenario_id=scenario['id'])
   s=self.e.chat(s['id'],'您目前最担心什么？我想先了解需求。')
   report=self.e.finish(s['id'])
   self.assertEqual(report['review']['turns'],1)
   self.assertEqual(len(report['review']['dimensions']),5)
   self.assertTrue(any(d['evidence'] for d in report['review']['dimensions']))
   with self.assertRaises(ValueError):self.e.chat(s['id'],'结束后发送')
 def test_swap_is_new_isolated_session(self):
  s=self.start();self.e.chat(s['id'],'上一轮专属内容')
  r=self.start(reverse=True)
  self.assertNotEqual(s['id'],r['id']);self.assertEqual(len(r['messages']),1)
  self.assertEqual(r['ai_role'],'合作顾问')
  self.assertFalse(self.e.finish(r['id'])['review']['dimensions'])
 def test_product_isolation(self):
  s=self.start(reverse=True,product_id='travel-demo')
  r=self.e.chat(s['id'],'介绍服务')
  self.assertIn('180',r['messages'][-1]['content']);self.assertNotIn('360',r['messages'][-1]['content'])
 def test_empty_review_and_seed(self):
  s=self.start(seed='fixed');r=self.start(seed='fixed')
  self.assertEqual(self.e.sessions[s['id']]['concerns'],self.e.sessions[r['id']]['concerns'])
  self.assertTrue(all(not d['observed'] for d in self.e.finish(s['id'])['review']['dimensions']))
 def test_failed_model_does_not_save_turn(self):
  with patch.dict('os.environ',{'MODEL_BASE_URL':'https://example.invalid/v1','MODEL_NAME':'demo'}):
   s=self.start(engine='live')
   with patch.object(self.e,'live',side_effect=ValueError('模型请求失败')):
    with self.assertRaises(ValueError):self.e.chat(s['id'],'hello')
   self.assertEqual(len(self.e.get(s['id'])['messages']),1)
   self.assertFalse(self.e.get(s['id'])['busy'])
 def test_invalid_inputs(self):
  for kwargs in [{'scenario_id':'missing'},{'product_id':'missing'},{'reverse':'true'},{'difficulty':'oops'}]:
   with self.assertRaises(ValueError):self.start(**kwargs)
  s=self.start()
  for message in ['',None,'x'*2001]:
   with self.assertRaises(ValueError):self.e.chat(s['id'],message)
 def test_synthetic_only(self):
  self.assertTrue(all(p['synthetic'] for p in PRODUCTS+SCENARIOS))

class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
  cls.base=f'http://127.0.0.1:{cls.server.server_port}'
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def test_assets_and_private_paths(self):
  with urllib.request.urlopen(self.base+'/') as r:self.assertEqual(r.status,200);self.assertIn('frame-ancestors',r.headers['Content-Security-Policy'])
  for path in ['/../data/demo_products.json','/.env','/backend/engine.py']:
   with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(self.base+path)
   self.assertEqual(cm.exception.code,404)
 def test_foreign_origin_blocked(self):
  req=urllib.request.Request(self.base+'/api/start',data=b'{}',headers={'Content-Type':'application/json','Origin':'https://example.invalid'})
  with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(req)
  self.assertEqual(cm.exception.code,403)

if __name__=='__main__':unittest.main()
