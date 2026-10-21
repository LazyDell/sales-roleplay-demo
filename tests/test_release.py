import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_scan', ROOT/'tools/check_public.py')
scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)
class ReleaseTests(unittest.TestCase):
 def test_sensitive_and_unknown_files_blocked(self):
  with tempfile.TemporaryDirectory() as tmp:
   old=scanner.ROOT;scanner.ROOT=Path(tmp)
   try:
    bad={'sample.md':chr(0x5229)+chr(0x771f),'.env':'value=private','record.zip':'archive','example.md':'sk-'+('a'*30)}
    paths=[]
    for name,value in bad.items():
     p=Path(tmp)/name;p.write_text(value);paths.append(p)
    self.assertEqual(len(scanner.scan(paths)),4)
   finally:scanner.ROOT=old
 def test_release_archive_contains_only_public_files(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'public.zip'
   subprocess.run([sys.executable,'tools/package_public.py',str(output)],cwd=ROOT,check=True,capture_output=True)
   with zipfile.ZipFile(output) as archive:
    names=archive.namelist()
    self.assertIn('sales-roleplay-demo/frontend/index.html',names)
    self.assertTrue(all(name.startswith('sales-roleplay-demo/') for name in names))
    self.assertFalse(any('/.git/' in n or '/__pycache__/' in n or n.endswith('/.env') for n in names))
