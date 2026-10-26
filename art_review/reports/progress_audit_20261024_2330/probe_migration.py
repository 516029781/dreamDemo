import pathlib,json,hashlib,importlib.util,tempfile,shutil,subprocess,sys
repo=pathlib.Path(r'C:/软件/鼠鼠'); out=repo/'art_review/reports/progress_audit_20261024_2330'
doc=json.loads((repo/'art_review/vnext/asset_status_migrated.json').read_text(encoding='utf-8'))
violations=[]
for rec in [doc['package']]+doc['items']:
 for key in ('old_status','old_decision','old_reviewer'):
  if key in rec.get('mapping',{}) and not isinstance(rec['mapping'][key],str):
   violations.append({'asset_id':rec['asset_id'],'path':f'mapping.{key}','value':rec['mapping'][key],'schema_requires':'string'})
root=pathlib.Path(tempfile.mkdtemp(prefix='audit_migration_'))
(root/'tools/art_gate').mkdir(parents=True);(root/'reviews').mkdir()
shutil.copyfile(repo/'tools/art_gate/migrate_catalog.py',root/'tools/art_gate/migrate_catalog.py')
(root/'catalog.json').write_text(json.dumps({'status':'candidate','items':[{'id':'ENV001','kind':'environment','status':'missing','blockers':[]}]}),encoding='utf-8')
(root/'reviews/ENV001.json').write_text(json.dumps({'decision':'fail','reviewer':'synthetic technical failure','evidence':[]}),encoding='utf-8')
(root/'defects.json').write_text(json.dumps({'defects':[]}),encoding='utf-8')
proc=subprocess.run([sys.executable,str(root/'tools/art_gate/migrate_catalog.py'),'--catalog','catalog.json','--reviews-dir','reviews','--defects','defects.json'],capture_output=True,text=True,encoding='utf-8')
migrated=json.loads((root/'art_review/vnext/asset_status_migrated.json').read_text(encoding='utf-8')) if proc.returncode==0 else None
result={'scope':'targeted explicit string-type constraints, not full JSON Schema validation (jsonschema unavailable)','actual_schema_type_violations':violations,'synthetic_failed_review_migration':{'exit':proc.returncode,'stdout':proc.stdout,'result':migrated['items'][0] if migrated else None},'fixture_root':str(root)}
(out/'migration_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'schema_type_violations':violations,'failed_review_technical_state':migrated['items'][0]['technical_state'] if migrated else None},ensure_ascii=False))