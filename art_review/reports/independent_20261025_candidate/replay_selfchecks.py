from pathlib import Path
import json,subprocess,sys,time,os
root=Path(r'C:/软件/鼠鼠');out=root/'art_review/reports/independent_20261025_candidate';runs=[]
for name in ['p02_selfcheck','p03_chain_test','p04_selfcheck','p05_selfcheck','p06_selfcheck']:
 source=root/'delivery/next_cycle/T0'/(name+'.py')
 code=source.read_text(encoding='utf-8-sig')
 # Preserve the tested gate code and production inputs; redirect only generated selfcheck artifacts.
 for prefix in ['p02','p04','p05','p06']:
  code=code.replace('delivery/next_cycle/T0/_'+prefix+'_tmp','art_review/reports/independent_20261025_candidate/fixtures_'+prefix)
  code=code.replace('art_review/vnext/_'+prefix+'_tmp','art_review/vnext/_independent_final_'+prefix)
  code=code.replace('delivery/next_cycle/T0/'+prefix+'_selfcheck.json','art_review/reports/independent_20261025_candidate/'+prefix+'_replay.json')
 code=code.replace('delivery/next_cycle/T0/_p06_canvas','art_review/reports/independent_20261025_candidate/fixtures_p06_canvas')
 for target in [out/'fixtures_p02',out/'fixtures_p04',out/'fixtures_p05',out/'fixtures_p06',out/'fixtures_p06_canvas',root/'art_review/vnext/_independent_final_p02']:
  if not target.resolve().is_relative_to(root.resolve()):raise RuntimeError('Fixture escapes project')
 # Keep __file__ as the original for its ROOT calculation. No producer source is edited.
 wrapper='__file__='+repr(str(source))+'\n__name__="__main__"\n'+code
 launcher=out/(name+'_isolated.py');launcher.write_text(wrapper,encoding='utf-8')
 tick=time.perf_counter();proc=subprocess.run([sys.executable,'-X','utf8',str(launcher)],cwd=root,capture_output=True,text=True,encoding='utf-8')
 runs.append({'script':str(source.relative_to(root)),'redirected_fixture_and_report_paths':True,'exit_code':proc.returncode,'seconds':time.perf_counter()-tick,'stdout':proc.stdout,'stderr':proc.stderr})
(out/'selfcheck_replays.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{k:r[k] for k in ['script','exit_code','seconds']} for r in runs]))