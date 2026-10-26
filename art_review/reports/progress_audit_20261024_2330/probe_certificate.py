import contextlib, importlib.util, io, json, hashlib, os, pathlib
repo=pathlib.Path(r'C:/软件/鼠鼠')
out=repo/'art_review/reports/progress_audit_20261024_2330'
script=(repo/'delivery/next_cycle/T0/p03_chain_test.py').read_text(encoding='utf-8')
# Isolate predecessor-only evidence. Synthetic fixtures and test key only.
script=script.replace('w(root / "runtime.txt", b"synthetic fixture")','w(root / "runtime.txt", b"synthetic fixture")\nw(root / "char_runtime.txt", b"synthetic predecessor runtime")')
script=script.replace('spec = root / f"spec_{stage}.json"','if stage == "character_playback":\n        artifacts["artifacts"][-1]["path"] = "char_runtime.txt"\n    spec = root / f"spec_{stage}.json"')
ns={'__name__':'audit_fixture'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(script, 'isolated_p03_fixture', 'exec'),ns)
args=['verify','--manifest',str(ns['mp2']),'--review',str(ns['rp2']),'--attestation',str(ns['ap2']),'--certificate',str(ns['cp2'])]+ns['COMMON']
normal_code,normal_out,_=ns['run'](args)
(ns['root']/'char_runtime.txt').write_text('CHANGED after predecessor approval',encoding='utf-8')
code,stdout,stderr=ns['run'](args)
# Explicit check of the predecessor manifest must detect the change.
spec=importlib.util.spec_from_file_location('audited_harness',repo/'tools/art_harness.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
h=mod.Harness(ns['root'])
try:
    h.check_manifest(json.loads(ns['mp1'].read_text(encoding='utf-8')))
    predecessor_error=None
except Exception as e:
    predecessor_error=str(e)
result={'scope':'synthetic isolated fixtures; no production signing or approval','fixture_root':str(ns['root']),
        'normal':{'exit':normal_code,'body':json.loads(normal_out)},
        'after_predecessor_artifact_mutation':{'exit':code,'body':json.loads(stdout),'stderr':stderr},
        'explicit_predecessor_check_error':predecessor_error,
        'defect_reproduced':code==0 and json.loads(stdout).get('accepted') is True and bool(predecessor_error)}
(out/'certificate_stale_dependency_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
# Capture immutable audit inputs without logging any secret environment values.
paths=['PROJECT_TASKS.json','delivery/next_cycle/last_checkpoint.json','tools/art_harness.py','tools/art_gate/migrate_catalog.py','art_review/vnext/harness_contract.json','art_review/vnext/asset_status.schema.json','art_review/vnext/asset_status_migrated.json','delivery/next_cycle/T0/p03_selfcheck.json']
snapshot={p:{'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest(),'bytes':(repo/p).stat().st_size} for p in paths}
(out/'input_snapshot.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
print(json.dumps({'defect_reproduced':result['defect_reproduced'],'after_mutation_accepted':result['after_predecessor_artifact_mutation']['body'].get('accepted'),'predecessor_error':predecessor_error},ensure_ascii=False))