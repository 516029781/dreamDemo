import pathlib,hashlib,json,subprocess,sys,time
repo=pathlib.Path(r'C:/软件/鼠鼠');out=repo/'art_review/reports/progress_audit_20261024_2330'
manifest=json.loads((repo/'art_review/submissions/art_complete/manifest.json').read_text(encoding='utf-8'))
rows=manifest['artifacts']+manifest.get('catalog_members',[])
results=[]
for row in rows:
 p=repo/row['path']; actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
 results.append({'path':row['path'],'role':row['role'],'expected':row['sha256'],'actual':actual,'match':actual==row['sha256']})
summary={'records':len(rows),'mismatch_count':sum(not r['match'] for r in results),'mismatches':[r for r in results if not r['match']],'records_all':results}
(out/'historical_manifest_integrity.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
replays=[]
for label,args in [('regression',['tools/test_art_harness.py']),('chain_selfcheck',['delivery/next_cycle/T0/p03_chain_test.py']),('audit',['tools/art_harness.py','audit','--root',str(repo)])]:
 start=time.perf_counter(); p=subprocess.run([sys.executable,'-X','utf8']+args,cwd=repo,capture_output=True,text=True,encoding='utf-8')
 replays.append({'label':label,'command':[sys.executable,'-X','utf8']+args,'exit_code':p.returncode,'duration_seconds':time.perf_counter()-start,'stdout':p.stdout,'stderr':p.stderr})
(out/'replays.json').write_text(json.dumps(replays,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'records':len(rows),'mismatch_count':summary['mismatch_count'],'mismatched_paths':[r['path'] for r in summary['mismatches']],'replay_exit_codes':{r['label']:r['exit_code'] for r in replays}},ensure_ascii=False))