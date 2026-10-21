#!/usr/bin/env python3
"""Build a browser-only demo from explicit public source files."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.engine import PRODUCTS, SCENARIOS, RUBRICS

def build(output):
 output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
 html=(ROOT/'frontend/index.html').read_text()
 html=html.replace('href="/"','href="./"').replace('href="/style.css"','href="./style.css"')
 html=html.replace('<script defer src="/app.js"></script>','<script defer src="./demo-data.js"></script><script defer src="./static-engine.js"></script><script defer src="./app.js"></script>')
 html=html.replace('真实模型 · 服务端未配置','真实模型 · 请下载本地版')
 html=html.replace('默认回复由规则生成，非真实 AI 推理。真实模型需在服务端配置。','在线版回复由浏览器内规则生成，非真实 AI 推理。对话只留在当前页面，刷新后清空。真实模型接入请下载本地版。')
 html=html.replace('场景种子只固定模拟追问顺序。','场景种子只固定在线模拟追问顺序。在线版与本地版的随机顺序可能不同。')
 html=html.replace('<footer><span>SALES PRACTICE LAB</span>','<footer><a href="https://github.com/LazyDell/sales-roleplay-demo" target="_blank" rel="noopener noreferrer">GitHub 源码与本地版 ↗</a><span>对话仅在当前浏览器页面处理</span>')
 html=html.replace('<meta name="viewport"','<meta name="description" content="销售对练实验室：TOB 与 TOC 双场景在线沟通练习，免费体验规则模拟、角色互换和证据复盘。所有业务资料均为虚构。"><meta name="viewport"')
 html=html.replace('<head>','<head><meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\'; connect-src \'none\'; img-src \'self\' data:; object-src \'none\'; base-uri \'self\'">')
 (output/'index.html').write_text(html)
 for name in ('app.js','static-engine.js','style.css'):(output/name).write_text((ROOT/'frontend'/name).read_text())
 (output/'demo-data.js').write_text('globalThis.DEMO_DATA = '+json.dumps({'products':PRODUCTS,'scenarios':SCENARIOS,'rubrics':RUBRICS},ensure_ascii=False)+';\n')
 print(f'Built 5 static files in {output.name}')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args();build(args.output)
