#!/usr/bin/env python3
"""Fail closed on unexpected release files; print paths/categories, never contents."""
import argparse
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES={'.py','.md','.html','.css','.js','.json','.yml','.example'}
ALLOWED_NAMES={'.gitignore'}
# Organization patterns supplied as Unicode escapes to avoid repeating private names in source.
PATTERNS={
 'organization':re.compile(r'\u5229\u771f|li[-_ ]?zhen|li[z]en',re.I),
 'personal_path':re.compile(r'/(?:Users|home)/[\w.-]+|[A-Z]:\\Users\\',re.I),
 'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'credential':re.compile(r'(?:sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})'),
 'phone_candidate':re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)'),
 'email_candidate':re.compile(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}'),
}
def files():
 for p in ROOT.rglob('*'):
  if any(x in {'.git','__pycache__','.venv'} for x in p.relative_to(ROOT).parts):continue
  if p.is_file() or p.is_symlink():yield p

def scan(paths):
 issues=[]
 for p in paths:
  relative=p.relative_to(ROOT).as_posix()
  if p.is_symlink():issues.append((relative,'symlink'));continue
  if p.name.startswith('.env') and p.name!='.env.example':issues.append((relative,'environment file'));continue
  if p.name not in ALLOWED_NAMES and p.suffix not in ALLOWED_SUFFIXES:issues.append((relative,'unapproved file type'));continue
  try:text=p.read_text('utf-8')
  except (UnicodeError,OSError):issues.append((relative,'unreadable'));continue
  for label,pattern in PATTERNS.items():
   if pattern.search(relative) or pattern.search(text):issues.append((relative,label))
 return issues

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--tracked',action='store_true');args=parser.parse_args()
 paths=list(files())
 if args.tracked:
  result=subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,capture_output=True)
  paths=[ROOT/p for p in result.stdout.decode().split('\0') if p]
 issues=scan(paths)
 for path,kind in issues:print(f'BLOCKED {path}: {kind}')
 print(f'Checked {len(paths)} files; {len(issues)} finding(s). Manual semantic review still required.')
 return bool(issues)
if __name__=='__main__':raise SystemExit(main())
