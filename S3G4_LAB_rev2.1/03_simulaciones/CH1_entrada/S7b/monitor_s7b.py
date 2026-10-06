"""Read-only compact monitoring for context-mode."""
from pathlib import Path
from collections import Counter
import json,re
from datetime import datetime
print('AT',datetime.now().isoformat(timespec='seconds'))
p=Path(r'C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada\S7b\campaign')
f=p/'s7b_checkpoint.json'
if f.exists():
 d=json.loads(f.read_text());m=d['meta']
 print('CHECKPOINT',m['successful'],'/',m['logical_cases'],'native',m['simulations'],'seconds',round(m['seconds']), 'code',m['returncode'])
 latest={r['id']:r for r in d['records']}
 bad=[r for r in latest.values() if r['errors'] or r['returncode']]
 print('PENDING ERRORS',dict(Counter('K'+re.search(r'_k([^_]+)',r['id'])[1].upper() for r in bad)))
f=p/'s7b_progress.json'
if f.exists():
 x=json.loads(f.read_text());phase=re.search(r'_k([^_]+)',x['phase'])[1]
 print('BATCH','K'+phase.upper(),x['completed'],'/',x['total'],'errors',x['errors'])
fs=list(p.glob('*.cir'))
if fs:
 last=max(fs,key=lambda f:f.stat().st_mtime)
 print('LATEST DECK','K'+re.search(r'_k([^_]+)',last.name)[1].upper())
print('FINAL REGISTER',(p/'s7b_registro.json').exists())
