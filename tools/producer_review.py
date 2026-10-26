"""Producer self-review submission filter. Never issues independent approval."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'planning/execution/producer_review_policy.json'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def file_at(relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ':' in relative:
        raise ValueError('Evidence path must be project-relative')
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError('Missing or escaping path: ' + relative)
    return path

def ref(relative):
    return {'path': relative, 'sha256': digest(file_at(relative))}

def known_issues():
    issues = {}
    for relative,key in [('planning/execution/workflow_fixes.json','issues'), ('art_review/reports/independent_20261024/defects.json','defects')]:
        path=ROOT/relative
        if path.is_file():
            for issue in load(path).get(key,[]):
                iid=issue.get('id')
                if iid:
                    issues[iid]={'id':iid,'severity':issue.get('severity', 'major' if issue.get('priority') in ('high','medium') else 'minor'),
                                 'title':issue.get('title',''),'status':'open','resolution_evidence':[]}
    return issues

def text_ok(value):
    return isinstance(value, str) and bool(value.strip())

def template(manifest_relative, output):
    manifest_path = file_at(manifest_relative)
    manifest = load(manifest_path)
    rubric = load(ROOT / 'art_review/rubric.json')
    policy = load(POLICY)
    if manifest.get('stage') not in ('scene_demo', 'art_complete'):
        raise ValueError('Self-review applies to scene_demo/art_complete candidates')
    report = {'kind': 'producer_self_review/1.0', 'reviewer': {'id': '', 'mode': 'producer_self_review'},
              'stage': manifest['stage'], 'round': 1, 'manifest': ref(manifest_relative),
              'rubric_sha256': digest(ROOT / 'art_review/rubric.json'),
              'contract_sha256': digest(ROOT / 'art_review/harness_contract.json'),
              'policy_sha256': digest(POLICY), 'quality_results': None, 'capture_binding': None,
              'cards': {card: {'dimensions': [dict(id=d['id'], score=None, observation='', gap='',
                        action_or_acceptance_reason='', reference_evidence=[], candidate_evidence=[]) for d in dims]}
                        for card, dims in rubric['cards'].items()},
              'asset_checks': [], 'issues': [], 'comparison_note': 'Inspect actual P1 references and actual candidate media; never copy old scores.'}
    if manifest['stage'] == 'art_complete':
        contract = load(ROOT / 'art_review/harness_contract.json')
        report['asset_checks'] = [dict(asset_id=aid, decision='not_checked', reason='', evidence=[]) for aid in contract['expected_art_ids']]
        report['issues'] = list(known_issues().values())
    output = output.resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Template requires a new output path inside project; never overwrite an existing review')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return {'status': 'blank_template_not_reviewed', 'path': str(output), 'accepted': False}

def evaluate(report_relative):
    policy = load(POLICY)
    rubric = load(ROOT / 'art_review/rubric.json')
    contract = load(ROOT / 'art_review/harness_contract.json')
    findings = []
    totals = {}
    diagnostics = []
    def fail(area, reason, action):
        findings.append({'area': area, 'reason': reason, 'action': action})
    def evidence(items, area, allowed=None, reference=False):
        if not isinstance(items, list) or not items:
            fail(area, 'Evidence missing', 'Add actual file path and SHA256; inspect the actual media')
            return
        for entry in items:
            try:
                if not isinstance(entry, dict): raise ValueError('Evidence entry must be an object')
                relative = entry.get('path')
                path = file_at(relative)
                if entry.get('sha256') != digest(path): raise ValueError('Evidence hash changed: '+relative)
                if allowed is not None and relative not in allowed: raise ValueError('Candidate evidence not in frozen manifest: '+relative)
                if reference and not relative.replace('\\','/').startswith('reference/_raw_screenshots/P1/'):
                    raise ValueError('Reference must include actual P1 source frame')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                fail(area, str(exc), 'Rebind to the correct immutable evidence; do not raise the score to hide it')
    try:
        report = load(file_at(report_relative))
        if report.get('kind') != 'producer_self_review/1.0': raise ValueError('Unknown producer review format')
        reviewer = report.get('reviewer', {})
        if reviewer.get('mode') != 'producer_self_review' or not text_ok(reviewer.get('id')):
            fail('reviewer', 'Producer identity/mode missing', 'Use actual producer identity and producer_self_review; do not impersonate independent review')
        evidence([report['manifest']], 'manifest')
        manifest = load(file_at(report['manifest']['path']))
        stage = manifest.get('stage')
        if stage not in ('scene_demo','art_complete') or report.get('stage') != stage:
            raise ValueError('Review/manifest stage mismatch')
        for name, path in [('rubric_sha256', ROOT/'art_review/rubric.json'), ('contract_sha256', ROOT/'art_review/harness_contract.json'), ('policy_sha256', POLICY)]:
            if report.get(name) != digest(path): fail(name, 'Review is stale', 'Regenerate/review using the actual current rules')
        artifacts = manifest.get('artifacts', []) + manifest.get('catalog_members', [])
        if not artifacts: fail('manifest', 'No frozen artifacts', 'Prepare actual candidate manifest first')
        evidence(artifacts, 'manifest_payload')
        candidates = {a['path'] for a in artifacts}
        threshold = policy['sample_minimum_per_card'] if stage == 'scene_demo' else policy['final_submission_minimum_per_card']
        if set(report.get('cards', {})) != set(rubric['cards']):
            fail('cards', 'Missing/unknown cards', 'Score ENV/CHAR/UI/MIX separately')
        for card, definitions in rubric['cards'].items():
            rows = report.get('cards', {}).get(card, {}).get('dimensions', [])
            by_id = {d.get('id'): d for d in rows if isinstance(d, dict)}
            if len(by_id) != len(rows) or set(by_id) != {d['id'] for d in definitions}:
                fail(card, 'Missing/duplicate/unknown dimensions', 'Use exact rubric dimensions'); continue
            total = 0
            complete = True
            for definition in definitions:
                row = by_id[definition['id']]; area = card+'/'+definition['id']; score = row.get('score')
                if type(score) is not int or not 0 <= score <= 4:
                    fail(area, 'Score must be integer 0..4; null/boolean is not a score', 'Inspect and score evidence before submission');complete=False;continue
                total += definition['weight']*score/4
                diagnostics.append({'card':card,'dimension':definition['id'],'score':score,'lost_weight':definition['weight']*(4-score)/4,
                                    'reported_gap':row.get('gap'),'suggested_repair':row.get('action_or_acceptance_reason'),
                                    'candidate_evidence':row.get('candidate_evidence',[])})
                if score == 4 and len({e.get('path') for e in row.get('candidate_evidence',[]) if isinstance(e,dict)}) < 2:
                    fail(area, 'Score 4 lacks multiple candidate views/states', 'Inspect at least two relevant actual views/states or lower the unsupported score')
                floor = max(rubric['minimum_dimension'], policy['minimum_dimension'],
                            max(rubric['minimum_core_dimension'],policy['minimum_core_dimension']) if definition['core'] else 0)
                if score < floor: fail(area, 'Dimension below floor', 'Fix this feature; high scores elsewhere cannot compensate')
                for key in ('observation','gap','action_or_acceptance_reason'):
                    if not text_ok(row.get(key)): fail(area, key+' missing', 'Describe concrete reference/candidate difference and repair or justified acceptance')
                evidence(row.get('reference_evidence'), area+'/reference', reference=True)
                evidence(row.get('candidate_evidence'), area+'/candidate', allowed=candidates)
            totals[card] = total if complete else None
            if complete and total < threshold:
                fail(card, f'Score {total} below submission threshold {threshold}', 'Repair lowest dimensions and their shared causes, recapture affected states, then rescore honestly')
        if stage == 'art_complete':
            rows = report.get('asset_checks', []); by_id = {r.get('asset_id'):r for r in rows if isinstance(r,dict)}
            if len(by_id) != len(rows) or set(by_id) != set(contract['expected_art_ids']):
                fail('asset_checks','Full 47-group coverage missing/duplicate','Check every required asset; do not recreate already valid sources')
            for aid,row in by_id.items():
                if row.get('decision') != 'pass' or not text_ok(row.get('reason')):
                    fail(aid, 'Asset not producer-checked/pass', 'Fix/recheck the asset and record concrete evidence')
                evidence(row.get('evidence'),aid,allowed=candidates)
        if not isinstance(report.get('issues'), list):
            fail('issues','Issue list missing','Record known issues; use [] only after checking')
        else:
            issue_ids=[i.get('id') for i in report['issues'] if isinstance(i,dict)]
            if len(issue_ids)!=len(report['issues']) or len(set(issue_ids))!=len(issue_ids):
                fail('issues','Malformed or duplicate issue IDs','Keep one truthful result per known issue')
            if stage=='art_complete' and not set(known_issues()).issubset(set(issue_ids)):
                fail('issues','Known F/R issues omitted from report','Reconcile all known audit findings; fixed-pending-independent is allowed only with real resolution evidence')
            for issue in report['issues']:
                status=issue.get('status');severity=issue.get('severity')
                if severity not in ('blocking','major','minor') or status not in ('open','resolved','fixed_pending_independent_confirmation'):
                    fail('issues','Unknown issue state/severity','Use explicit producer issue state');continue
                if severity in ('blocking','major') and status=='open':
                    fail(issue.get('id','issue'),'Unresolved blocking/major issue','Repair locally before asking for final review')
                if status!='open': evidence(issue.get('resolution_evidence'),'issue_resolution')
        # Reuse existing mechanical validators; this does not certify visual truth.
        try:
            evidence([report.get('quality_results')], 'quality_results')
            evidence([report.get('capture_binding')], 'capture_binding')
            result_path=file_at(report['quality_results']['path']); binding_path=file_at(report['capture_binding']['path'])
            sys.path.insert(0,str(ROOT/'tools/art_gate'))
            import check_quality, check_bindings
            check_bindings.verify_binding(ROOT,binding_path,'art_review/vnext/capture_binding.schema.json')
            results=load(result_path)
            check_quality.schema_validate(results,ROOT/'art_review/vnext/behavior_results.schema.json')
            if results.get('stage') != stage: raise ValueError('Q results stage differs from manifest')
            binding=load(binding_path)
            assessed=check_quality.evaluate(ROOT,results,load(ROOT/'art_review/vnext/quality_checks.json'),binding)
            if assessed['status']!='pass': fail('Q01-Q09',str({'failed':assessed['failed'],'pending':assessed['pending']}),'Fix or collect actual required evidence; no invented N/A')
            binding_build = binding.get('build_id') or (binding.get('build') or {}).get('build_id')
            if binding_build != results.get('build_id'): raise ValueError('Build binding mismatch')
            # Ensure candidate evidence belongs to the binding graph as well as the manifest.
            bound_paths=set()
            def paths(value):
                if isinstance(value,dict):
                    if isinstance(value.get('path'),str): bound_paths.add(value['path'])
                    for v in value.values():paths(v)
                elif isinstance(value,list):
                    for v in value:paths(v)
            paths(binding)
            media={a['path'] for a in artifacts if Path(a['path']).suffix.lower() in {'.png','.jpg','.jpeg','.gif','.mp4','.webm'}}
            if media and not (media & bound_paths): fail('capture_binding','No snapshotted candidate media occurs in binding','Bind actual captured candidate media, not an unrelated successful run')
        except Exception as exc:
            fail('mechanical_validation',str(exc),'Repair actual Q/binding inputs or validator environment; do not substitute producer scores for checks')
    except (OSError,ValueError,TypeError,KeyError) as exc:
        fail('report',str(exc),'Complete a current manifest-bound producer review first')
    ready = not findings
    return {'kind':'producer_submission_filter_not_independent_approval','status':'ready_for_final_review' if ready else 'producer_rework_required',
            'ready_for_final_review':ready,'accepted':False,'independent_approval':False,'computed_scores':totals,
            'findings':findings,'dimension_diagnostics':diagnostics,
            'priority_repairs':sorted([d for d in diagnostics if d['lost_weight']>0],key=lambda d:-d['lost_weight']) if not ready else [],'next_action':'Submit complete candidate for final review; do not sign approval' if ready else 'Continue producer repair/review loop; no external reviewer required to fix these findings',
            'limitation':'Computes reported scores and validates evidence/mechanical consistency; cannot judge whether visual observations or claimed measurements are truthful.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    make=sub.add_parser('template');make.add_argument('--manifest',required=True);make.add_argument('--out',type=Path,required=True)
    check=sub.add_parser('check');check.add_argument('--review',required=True);check.add_argument('--out',type=Path)
    args=parser.parse_args()
    try:
        result=template(args.manifest,args.out) if args.command=='template' else evaluate(args.review)
        if args.command=='check' and args.out:
            output=args.out.resolve()
            if not output.is_relative_to(ROOT):raise ValueError('Output outside project')
            output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if args.command=='template' or result['ready_for_final_review'] else 3
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'invalid','accepted':False,'error':str(exc)},ensure_ascii=False));return 2
if __name__=='__main__':sys.exit(main())