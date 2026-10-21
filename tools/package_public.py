#!/usr/bin/env python3
"""Create a scanned allowlist archive without runtime files or Git history."""
import argparse
import zipfile
from pathlib import Path
from check_public import ROOT, files, scan

def main():
 parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
 output=args.output.resolve()
 if output.is_relative_to(ROOT):raise SystemExit('Write the archive outside the source directory.')
 paths=sorted(files())
 issues=scan(paths)
 if issues:raise SystemExit('Release blocked. Run tools/check_public.py for findings.')
 with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as archive:
  for p in paths:archive.write(p,'sales-roleplay-demo/'+p.relative_to(ROOT).as_posix())
 print(f'Packaged {len(paths)} reviewed source files.')
if __name__=='__main__':main()
