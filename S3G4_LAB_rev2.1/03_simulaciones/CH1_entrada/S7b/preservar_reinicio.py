"""Preserve a validated checkpoint and all uncheckpointed native attempts.

Use --snapshot while the runner is live, stop its process tree, then --harvest.
No physical simulation result is accepted from an incomplete checkpoint.
"""
import sys,json,time,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ejecutar_s7b as s
work=s.ROOT/'S7b'/'campaign'
checkpoint=work/'s7b_checkpoint.json'
snapshot=s.ROOT/'S7b'/'restart_snapshot.json'
archive=s.ROOT/'S7b'/'campaign_before_warm_restart'
if '--snapshot' in sys.argv:
 for attempt in range(30):
  try:
   text=checkpoint.read_text(encoding='utf-8');d=json.loads(text)
   captured=dict(data=d,checkpoint_epoch=checkpoint.stat().st_mtime,capture_epoch=time.time())
   s.checkpoint_write(snapshot,json.dumps(captured,ensure_ascii=False));break
  except json.JSONDecodeError:
   time.sleep(.2)
 else:raise RuntimeError('No valid checkpoint could be captured')
 archive.mkdir(exist_ok=True)
 shutil.copy2(work/'s7b_protected_before.json',archive/'s7b_protected_before.json')
 print('SNAPSHOT',d['meta']['successful'],d['meta']['simulations'],flush=True)
elif '--harvest' in sys.argv:
 captured=json.loads(snapshot.read_text(encoding='utf-8'))
 d=captured['data'];epoch=captured['checkpoint_epoch']
 try:
  current=json.loads(checkpoint.read_text(encoding='utf-8'))
  if current['meta']['seconds']>=d['meta']['seconds']:
   d=current;epoch=checkpoint.stat().st_mtime
 except json.JSONDecodeError:pass
 known={r['id'] for r in d['records']}
 added=[]
 for c in s.jobs():
  if c['phase']!='K2' or c['id'] in known:continue
  log=work/(c['id']+'.log')
  if not log.exists():continue
  finished='Total elapsed time:' in log.read_text(errors='replace')
  rec=dict(id=c['id'],returncode=-2,errors=['Native attempt not in durable checkpoint; full AC spectrum re-executed'],warnings=[],simulations=1,interrupted_harvest=True,native_finished=finished)
  added.append(rec)
  for ext in ['.cir','.log','.bias','.raw','.op.raw']:
   f=work/(c['id']+ext)
   if f.exists():shutil.copy2(f,archive/f.name)
 d['records'].extend(added)
 d['meta'].update(returncode=1,simulations=sum(r.get('simulations',1) for r in d['records']),successful=len(d['rows']),seconds=d['meta']['seconds']+max(0,time.time()-epoch),harvested_attempts=len(added))
 s.checkpoint_write(checkpoint,json.dumps(d,ensure_ascii=False))
 s.write(archive/'harvest.json',json.dumps(dict(attempts=added,meta=d['meta']),ensure_ascii=False,indent=2))
 print('HARVEST',len(added),'finished',sum(r['native_finished'] for r in added),'meta',d['meta'],flush=True)
else:raise SystemExit('Use --snapshot or --harvest')
