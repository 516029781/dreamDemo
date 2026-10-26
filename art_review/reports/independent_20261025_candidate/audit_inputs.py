from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,subprocess,sys,zipfile,time
from PIL import Image
root=Path(r'C:/软件/鼠鼠');out=root/'art_review/reports/independent_20261025_candidate';out.mkdir(parents=True,exist_ok=True)
start_paths=['PROJECT_TASKS.json','tools/art_harness.py','tools/producer_review.py','tools/test_art_harness.py','tools/art_gate/check_quality.py','tools/art_gate/check_bindings.py','art_review/harness_contract.json','art_review/rubric.json','planning/execution/producer_review_policy.json','art_review/submissions/candidate_full/manifest.json','delivery/next_cycle/T4/producer_self_review.json','delivery/next_cycle/T4/producer_submission_check.json','art/iterations/cycle_02/full_art_catalog.json','demo/assets/scripts/CourtyardBootstrap.ts']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snapshot={rel:{'sha256':sha(root/rel),'bytes':(root/rel).stat().st_size} for rel in start_paths}
(out/'input_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
for rel in start_paths:
 dest=out/'audited_inputs'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((root/rel).read_bytes())
manifest=json.loads((root/'art_review/submissions/candidate_full/manifest.json').read_text(encoding='utf-8-sig'))
rows=manifest['artifacts']+manifest.get('catalog_members',[])
results=[];cache={}
for item in rows:
 rel=item['path'];p=root/rel
 if rel not in cache:cache[rel]=sha(p) if p.is_file() else None
 results.append({'role':item.get('role'),'path':rel,'expected':item['sha256'],'actual':cache[rel],'match':item['sha256']==cache[rel]})
(out/'manifest_integrity.json').write_text(json.dumps({'records':len(rows),'unique_paths':len(cache),'mismatches':[r for r in results if not r['match']],'all_records':results},ensure_ascii=False,indent=2),encoding='utf-8')
runs=[]
for name,args in [('unit_regression',['tools/test_art_harness.py','-v']),('producer_filter',['tools/producer_review.py','check','--review','delivery/next_cycle/T4/producer_self_review.json']),('manifest_verify',['tools/art_harness.py','verify','--manifest','art_review/submissions/candidate_full/manifest.json']),('actual_quality',['tools/art_gate/check_quality.py','--results','delivery/next_cycle/T5/behavior_results_art_complete.json','--binding','delivery/next_cycle/T3/bindings/binding_formal_no_ui.json'])]:
 tick=time.perf_counter();p=subprocess.run([sys.executable,'-X','utf8']+args,cwd=root,capture_output=True,text=True,encoding='utf-8')
 result={'label':name,'command':[sys.executable,'-X','utf8']+args,'exit_code':p.returncode,'seconds':time.perf_counter()-tick,'stdout':p.stdout,'stderr':p.stderr};runs.append(result)
 (out/(name+'.stdout.txt')).write_text(p.stdout,encoding='utf-8');(out/(name+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
 try:(out/(name+'.json')).write_text(json.dumps(json.loads(p.stdout),ensure_ascii=False,indent=2),encoding='utf-8')
 except ValueError:pass
(out/'command_runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
animation=[]
for rel in ['delivery/next_cycle/T6/character/char_idle.gif','delivery/next_cycle/T6/character/char_move.gif','art/phase1/character_playback_1015/idle.gif','art/phase1/character_playback_1015/move.gif']:
 p=root/rel
 if not p.is_file():continue
 im=Image.open(p);frames=[];duration=0
 for i in range(getattr(im,'n_frames',1)):
  im.seek(i);duration+=im.info.get('duration',0);frames.append(hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest())
 animation.append({'path':rel,'sha256':sha(p),'frames':len(frames),'unique_rgba_frames':len(set(frames)),'duration_ms':duration})
(out/'animation_inspection.json').write_text(json.dumps(animation,indent=2),encoding='utf-8')
print(json.dumps({'manifest_records':len(rows),'unique_paths':len(cache),'mismatches':sum(not r['match'] for r in results),'artifacts':[(a['role'],a['path']) for a in manifest['artifacts']],'commands':[{k:r[k] for k in ('label','exit_code','seconds')} for r in runs],'animation':animation},ensure_ascii=False))