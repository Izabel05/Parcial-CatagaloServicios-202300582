"""Huella del código/configuración; excluye .env, dependencias y evidencias."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--output',required=True)
args=parser.parse_args();root=Path(args.root);files=[]
for directory in ['backend','frontend/src','frontend/tests','frontend/scripts','tests','scripts']:
    files.extend(p for p in (root/directory).rglob('*') if p.is_file() and p.suffix in ('.py','.js','.mjs','.jsx','.sql','.sh','.ps1','.css','.txt') and '__pycache__' not in p.parts)
files.extend(root/p for p in ['Dockerfile','compose.yaml','compose.test.yaml','compose.acceptance.yaml','frontend/package.json','frontend/package-lock.json','frontend/playwright.config.js'])
Path(args.output).write_text(json.dumps({str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2),encoding='utf-8')
