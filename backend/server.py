"""Loopback-only demo server. Exposes frontend assets, never repository files."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .engine import Engine, ROOT

ENGINE = Engine()
ASSETS = {'/': ('index.html','text/html'), '/app.js':('app.js','text/javascript'), '/style.css':('style.css','text/css')}
class Handler(BaseHTTPRequestHandler):
 def log_message(self, *_): pass
 def send(self, status, body, content_type='application/json'):
  data = json.dumps(body, ensure_ascii=False).encode() if content_type=='application/json' else body
  self.send_response(status)
  self.send_header('Content-Type',content_type+'; charset=utf-8')
  self.send_header('Content-Length',str(len(data)))
  self.send_header('Cache-Control','no-store')
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
  self.end_headers()
  self.wfile.write(data)
 def trusted(self):
  expected = f'127.0.0.1:{self.server.server_port}'
  host = self.headers.get('Host','')
  allowed = {expected, f'localhost:{self.server.server_port}'}
  origin = self.headers.get('Origin')
  return host in allowed and (not origin or origin in {'http://'+h for h in allowed})
 def do_GET(self):
  if not self.trusted(): return self.send(403, {'error':'请求来源不受支持。'})
  path = urlparse(self.path).path
  if path == '/api/catalog': return self.send(200, ENGINE.capabilities())
  if path in ASSETS:
   name, mime = ASSETS[path]
   return self.send(200, (ROOT/'frontend'/name).read_bytes(), mime)
  self.send(404, {'error':'页面不存在。'})
 def do_POST(self):
  if not self.trusted(): return self.send(403, {'error':'请求来源不受支持。'})
  if self.headers.get('Content-Type') != 'application/json': return self.send(415, {'error':'需要 JSON 请求。'})
  try:
   length = int(self.headers.get('Content-Length','0'))
   if not 0 < length <= 16000: raise ValueError('请求大小无效。')
   body = json.loads(self.rfile.read(length))
   if not isinstance(body,dict): raise ValueError('请求必须为对象。')
   path = urlparse(self.path).path
   if path == '/api/start': result = ENGINE.start(body)
   elif path == '/api/chat': result = ENGINE.chat(body.get('session_id'),body.get('message'))
   elif path == '/api/finish': result = ENGINE.finish(body.get('session_id'))
   else: return self.send(404, {'error':'接口不存在。'})
   self.send(200,result)
  except (ValueError, TypeError, UnicodeError):
   # Validation errors in our engine are intentionally safe to display.
   import sys
   exc = sys.exception()
   msg = str(exc) if type(exc) is ValueError else '请求格式无效。'
   self.send(400, {'error':msg})

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--port',type=int,default=8765)
 args=parser.parse_args()
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 print(f'Local: http://127.0.0.1:{server.server_port}',flush=True)
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 finally: server.server_close()
if __name__=='__main__': main()
