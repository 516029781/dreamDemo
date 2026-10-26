"""Compact work-package reader and timed command wrapper; never approves tasks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
STATES = {'todo', 'in_progress', 'rework', 'waiting_review', 'blocked', 'done'}
GIB = 1024 ** 3
MIB = 1024 ** 2
STORAGE_WARNING_BYTES = 10 * GIB
STORAGE_LIMIT_BYTES = 12 * GIB
STORAGE_STATUS_PATH = ROOT / 'delivery/workflow/STORAGE_STATUS.json'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(content, encoding='utf-8')
    os.replace(temp, path)

def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def storage_check(planned_growth_mib=0):
    """Read-only scan. The derived status file is evidence, never a cleanup action."""
    if planned_growth_mib < 0:
        raise ValueError('planned growth must be non-negative')
    from maintenance.storage_report import scan
    scan_result = scan(ROOT, largest_count=10)
    total = scan_result['total_bytes']
    projected = total + int(planned_growth_mib * MIB)
    status = ('over_limit' if projected > STORAGE_LIMIT_BYTES else
              'warning' if projected >= STORAGE_WARNING_BYTES else 'ok')
    report = {
        'kind': 'workspace_storage_preflight',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'current_bytes': total,
        'projected_bytes': projected,
        'planned_growth_mib': planned_growth_mib,
        'warning_bytes': STORAGE_WARNING_BYTES,
        'limit_bytes': STORAGE_LIMIT_BYTES,
        'scan_errors': scan_result['error_count'],
        'largest_top_level': [g for g in scan_result['groups'] if '/' not in g['path']][:8],
        'action': ('Do not start another large build/export/package. Continue source repair and '
                   'read-only checks; recover space under tools/maintenance/STORAGE_POLICY.md.'
                   if status == 'over_limit' else
                   'Avoid duplicate previews and old package ZIPs; measure again after this batch.'
                   if status == 'warning' else 'Continue with the planned batch.'),
    }
    atomic(STORAGE_STATUS_PATH, encoded(report))
    return report


def storage_command(args):
    report = storage_check(args.planned_growth_mib)
    print(encoded(report))
    return 2 if args.enforce and (report['status'] == 'over_limit' or report['scan_errors']) else 0

def inputs():
    raw = (ROOT / 'PROJECT_TASKS.json').read_bytes()
    ledger = json.loads(raw.decode('utf-8-sig'))
    packages = read(ROOT / 'planning/performance/remaining_work_packages.json')['packages']
    tasks = {t['id']: t for t in ledger['tasks']}
    if len(tasks) != len(ledger['tasks']):
        raise ValueError('Duplicate task IDs')
    owners = {}
    for package in packages:
        for tid in package['task_ids']:
            if tid not in tasks or tid in owners:
                raise ValueError('Unknown or duplicate package task: ' + tid)
            owners[tid] = package['id']
    for tid, task in tasks.items():
        if task['status'] not in STATES:
            raise ValueError('Unknown status: ' + tid)
        if tid not in owners:
            raise ValueError('Task missing from package index (include done tasks for future reopen): ' + tid)
        for dep in task['depends_on']:
            if dep not in tasks:
                raise ValueError('Unknown dependency: ' + dep)
    def ancestors(tid, trail=()):
        if tid in trail:
            raise ValueError('Dependency cycle: ' + ' -> '.join(trail + (tid,)))
        result = set()
        for dep in tasks[tid]['depends_on']:
            result.add(dep)
            result.update(ancestors(dep, trail + (tid,)))
        return result
    dependencies = {tid: ancestors(tid) for tid in tasks}
    return raw, ledger, packages, tasks, owners, dependencies

def summary(args):
    raw, ledger, packages, tasks, owners, dependencies = inputs()
    scope = args.scope or ledger['current_scope']
    rows = []
    for package in packages:
        for tid in package['task_ids']:
            task = tasks[tid]
            if task['scope'] != scope or task['status'] == 'done':
                continue
            pending = sorted(d for d in dependencies[tid] if tasks[d]['status'] != 'done')
            if ledger.get('workflow_mode') != 'candidate_first_final_review' and tid.startswith('A-') and tasks['V09']['status'] != 'done' and 'V09' not in pending:
                pending.append('V09')
            ready = not pending and task['owner_role'] == 'producer' and task['status'] in {'todo', 'rework', 'in_progress'}
            rows.append({'id': tid, 'package': package['id'], 'title': task['title'],
                         'status': task['status'], 'role': task['owner_role'],
                         'ready_for_producer': ready, 'unfinished_ancestors': pending,
                         'blocker': task.get('blocker'), 'resume_action': task.get('resume_action'),
                         'final_release_dependencies': task.get('release_dependencies', task.get('review_dependencies', []))})
    ready = [row for row in rows if row['ready_for_producer']]
    package_order = {p['id']: i for i, p in enumerate(packages)}
    ready.sort(key=lambda r: (package_order[r['package']], {'in_progress': 0, 'rework': 1, 'todo': 2}[r['status']]))
    producer_complete = all(t['status'] == 'done' for t in tasks.values() if t['scope'] == scope and t['owner_role'] == 'producer')
    rework_path = ROOT / 'planning/execution/ACTIVE_REWORK_CYCLE.json'
    rework = read(rework_path) if scope == 'art_required' and rework_path.exists() else None
    if rework and rework.get('status') != 'open':
        rework = None
    submission = {'status':'not_due_until_full_candidate','ready_for_final_review':False}
    if scope == 'art_required' and producer_complete:
        policy = read(ROOT / 'planning/execution/producer_review_policy.json')
        review_path = policy['final_report']
        if (ROOT / review_path).is_file():
            import producer_review
            submission = producer_review.evaluate(review_path)
        else:
            submission = {'status':'producer_self_review_required','ready_for_final_review':False,
                          'next_action':'Complete producer self-review and local repair before requesting final review; no external reviewer needed yet.'}
    if rework and rework.get('last_attempt'):
        last = rework['last_attempt']
        submission = {'status': last.get('producer_filter', 'producer_rework_required'),
                      'ready_for_final_review': False,
                      'candidate': last.get('candidate'),
                      'scores': last.get('scores', {}),
                      'next_action': rework.get('resume_action')}
    external = [row for row in rows if row['role'] in {'independent_reviewer', 'controller'} and not row['unfinished_ancestors']]
    if scope == 'art_required' and (not submission['ready_for_final_review'] or rework):
        external = []
    selected = args.package or (ready[0]['package'] if ready else 'B11' if scope == 'art_required' and producer_complete and (not submission['ready_for_final_review'] or rework) else external[0]['package'] if external else None)
    rollout_path = ROOT / 'planning/execution/optimization_rollout.json'
    measures = read(rollout_path).get('measures', []) if rollout_path.exists() else []
    focus = [m for m in measures if selected in m.get('package_ids', [])]
    if selected and selected not in {p['id'] for p in packages}:
        raise ValueError('Unknown package: ' + selected)
    counts = {}
    for task in tasks.values():
        counts.setdefault(task['scope'], {})
        counts[task['scope']][task['status']] = counts[task['scope']].get(task['status'], 0) + 1
    checkpoint_path = ROOT / 'delivery/next_cycle/last_checkpoint.json'
    checkpoint = read(checkpoint_path) if checkpoint_path.exists() else {}
    warnings = []
    storage = read(STORAGE_STATUS_PATH) if STORAGE_STATUS_PATH.is_file() else None
    if storage:
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(storage['generated_at'])
            if age.total_seconds() > 24 * 3600:
                warnings.append('Storage preflight is older than 24 hours; rerun workflow.py storage before a large output.')
        except (KeyError, ValueError, TypeError):
            warnings.append('Storage preflight timestamp invalid; rerun workflow.py storage.')
        if storage.get('status') == 'over_limit':
            warnings.append('Workspace over 12 GiB: do not generate another large build/export/package; continue source repair and storage recovery.')
        if storage.get('scan_errors'):
            warnings.append('Storage scan had errors; rerun preflight and resolve them before a large output.')
    else:
        warnings.append('No storage preflight yet; run workflow.py storage before a large output.')
    if checkpoint.get('ledger_revision') != ledger['revision']:
        warnings.append('Checkpoint revision differs; ledger wins, preserve previous evidence.')
    if any(t['status'] == 'done' and any(tasks[d]['status'] != 'done' for d in dependencies[t['id']]) for t in tasks.values()):
        warnings.append('Some previously done tasks have reopened ancestors; downstream scheduling checks the whole chain.')
    report = {'kind': 'workflow_summary_not_release_gate', 'generated_at': datetime.now(timezone.utc).isoformat(),
              'ledger_revision': ledger['revision'], 'ledger_sha256': hashlib.sha256(raw).hexdigest(),
              'scope': scope, 'counts': counts, 'selected_package': selected,
              'workflow_mode': ledger.get('workflow_mode', 'legacy'),
              'candidate_target': ledger.get('candidate_completion_tasks', {}).get(scope),
              'producer_candidate_complete': producer_complete, 'producer_submission_check': submission,
              'active_rework_cycle': rework,
              'ready_producer_ids': [r['id'] for r in ready], 'external_actions': external, 'optimization_focus': focus, 'unfinished': rows,
              'warnings': warnings, 'storage_preflight': storage,
              'release_note': 'Readiness is scheduling only. No certificate or visual approval is verified or issued here.'}
    lines = ['# 当前工作包（由账本生成）', '', f"账本：{ledger['revision']}；范围：{scope}；工作包：{selected or '无ready生产任务'}。", '',
             '先读 MODEL_EXECUTION_GUIDE.md。当前为完整候选后集中评审模式；待审核不阻塞制作，不自签放行。',
             '相关规范/最佳用例/失败案例检索：knowledge/README.md（导航资料，不替代合同与当前工作包）。', '',
             '制作目标：' + str(report.get('candidate_target') or '按当前范围'), '',
             '最终制作侧提交筛选：四卡各自评≥90、核心≥3/4、所有项≥2/4；Q/绑定通过且无未解严重问题。独立验收仍按 art_review/rubric.json。低分自行返修，不找外部审核者等指令。', '',
             '最近尝试的提交筛选：' + submission['status'] + ('（' + str(submission.get('candidate')) + '）' if submission.get('candidate') else ''), '',
             'Ready：' + (', '.join(report['ready_producer_ids']) or '无；核实依赖和外部阻塞'), '']
    if rework:
        lines += ['## 当前独立审核退回：先执行返修', '',
                  f"冻结候选：{rework['source_candidate']}；下个候选：{rework['next_candidate']}。",
                  f"审核报告：{rework['independent_report']}",
                  f"返修工作单：{rework['execution_spec']}",
                  '开放项：' + ', '.join(rework['open_findings'])]
        if rework.get('review_report'):
            lines += ['最近候选预审与耗时分析：' + rework['review_report']]
        if rework.get('execution_design'):
            lines += ['下一候选执行细化：' + rework['execution_design']]
            lines += ['n5 量化试点：逐次记录 Blender/Cocos 运行、全量重采、端到端墙钟与 unknown、四卡评分及自评/独立分差、三类证据链错误；4–6/15–20 次、6–7 小时、分差≤5、错误清零均是待实测目标，不是已实现结果或质量失败时的停止上限。具体计算与失败处理见执行细化及 n4 预审报告。']
        if rework.get('visual_playbook'):
            lines += ['n5 视觉制作配方（改哪个母版、先看什么、无效时换法）：' + rework['visual_playbook']]
        if rework.get('parallel_agent_plan'):
            lines += ['n5 子代理并行排程（独占源、单点集成与串行门）：' + rework['parallel_agent_plan']]
        if rework.get('reuse_after_success'):
            lines += ['首图成功后沉淀其他地图可复用链路（当前须同步留日志，后续提炼不阻塞 I07）：' + rework['reuse_after_success']]
        if rework.get('self_learning_protocol'):
            lines += ['每批自我总结与问题发现：' + rework['self_learning_protocol']]
        if rework.get('lessons_index'):
            lines += ['相关经验索引（仅供检索，需复验证据）：' + rework['lessons_index']]
        lines += [rework['resume_action'],
                  '执行闭环：选一个开放缺陷→从低分维度和原图定位共享原因→改可编辑母版→同机位预览→记录是否改善；未改善立即换结构方法，改善后再构建/采集/评分。自审未达门槛时不得以“已记录下一步”结束制作轮。',
                  '既有制作任务 done 不代表本次独立退回已解决。当前不应交外部放行；先修复并重新冻结新候选。', '']
    if producer_complete and scope == 'art_required' and not submission['ready_for_final_review']:
        lines += ['## 制作模型继续自行审核/返修', '', '完整包存在但尚未达到提交门槛。执行PRODUCER_SELF_REVIEW.md；没有ready账本项不等于外部审核阻塞。', '']
    for warning in warnings:
        lines += ['提示：' + warning, '']
    if external:
        lines += ['## 当前可交外部角色的任务', '']
        lines += [f"- {r['id']} → {r['role']}（不得制作方自签）" for r in external]
        lines += ['']
    if focus:
        lines += ['## 本工作包的提速措施（不是已完成证明）', '']
        lines += [f"- {m['id']} {m['title']}：{m['status']}；{m.get('remaining', '')}" for m in focus]
        lines += ['']
    for row in rows:
        if row['package'] != selected:
            continue
        task = tasks[row['id']]
        lines += [f"## {row['id']} {row['title']}", '', f"状态：{row['status']}；角色：{row['role']}；ready={row['ready_for_producer']}",
                  '未完成制作前序：' + (', '.join(row['unfinished_ancestors']) or '无'),
                  '最终评审/放行依赖（不阻塞候选制作）：' + (', '.join(row['final_release_dependencies']) or '无'), '', '验收：']
        if rework and row['id'] == 'I07':
            lines += ['- 当前开放项：' + ', '.join(rework['open_findings']),
                      '- 在 ' + rework['next_candidate'] + ' 下实际修复并同机位比较；按当前工作单逐项关闭。',
                      '- 47项覆盖、四卡各≥90、Q/绑定通过、严重问题0；同源冻结并请求集中独立审核。']
        else:
            lines += ['- ' + item for item in task['acceptance']]
        if rework and row['id'] == 'I07':
            lines += ['', '本轮输出：新候选的可编辑源、正式画面、行为/Q结果、自审与检查结果、manifest和审阅包；实际路径更新到返修指针和账本。旧候选路径只作历史证据。']
        else:
            lines += ['', '输出：']
            lines += ['- ' + item for item in task['outputs']]
        optimization = task.get('execution_optimization', {})
        if optimization:
            lines += ['', '本任务的流程优化动作：'] + ['- ' + action for action in optimization.get('actions', [])]
        lines += ['', '下一动作：' + (rework['resume_action'] if rework and row['id'] == 'I07' else task.get('resume_action') or '按验收核对实际成果'), '']
        if rework and row['id'] == 'I07':
            lines += ['本轮执行优先级：上方当前返修指针与工作单覆盖此任务中旧 N01–N08 叙述；只重做 open_findings，resolved_pending_independent 在相关依赖变化时复核。原有 47 项覆盖及最终门槛继续有效。', '']
    if args.write:
        atomic(ROOT / 'delivery/workflow/SUMMARY.json', encoded(report))
        atomic(ROOT / 'delivery/workflow/CURRENT_WORK_PACKAGE.md', '\n'.join(lines) + '\n')
    print(encoded({'ledger_revision': ledger['revision'], 'scope': scope, 'counts': counts,
                   'selected_package': selected, 'ready_producer_ids': report['ready_producer_ids'],
                   'external_action_ids': [r['id'] for r in external],
                   'candidate_target': report['candidate_target'], 'producer_candidate_complete': report['producer_candidate_complete'],
                   'submission_filter_status': submission['status'], 'ready_for_final_review': submission['ready_for_final_review'], 'warnings': warnings,
                   'storage_status': storage.get('status') if storage else 'not_measured',
                   'active_rework_cycle': rework,
                   'written': bool(args.write)}))
    return 0

def run_command(args):
    raw, ledger, packages, *_ = inputs()
    if args.package not in {p['id'] for p in packages}:
        raise ValueError('Unknown package')
    if args.planned_growth_mib:
        preflight = storage_check(args.planned_growth_mib)
        if preflight['status'] == 'over_limit' or preflight['scan_errors']:
            print(encoded({'status': 'storage_blocked', 'preflight': preflight}), file=sys.stderr)
            return 2
    command = list(args.command)
    if command and command[0] == '--':
        command.pop(0)
    if not command:
        raise ValueError('An explicit command after -- is required')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    folder = ROOT / 'delivery/performance' / stamp
    folder.mkdir(parents=True)
    event = {'run_id': stamp, 'package_id': args.package, 'label': args.label,
             'ledger_revision': ledger['revision'], 'ledger_sha256': hashlib.sha256(raw).hexdigest(),
             'command': command, 'started_at': datetime.now(timezone.utc).isoformat(),
             'scope': 'one explicit tool command, not total model development time'}
    atomic(folder / 'event.json', encoded({**event, 'status': 'running'}))
    started = time.perf_counter()
    try:
        with (folder / 'stdout.log').open('wb') as stdout, (folder / 'stderr.log').open('wb') as stderr:
            completed = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, shell=False)
        code = completed.returncode
        event['status'] = 'command_exited_not_acceptance'
    except (OSError, KeyboardInterrupt) as exc:
        event['status'] = 'launch_failed_or_interrupted'
        event['error'] = str(exc)
        code = 130 if isinstance(exc, KeyboardInterrupt) else 127
    event.update(ended_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.perf_counter()-started, exit_code=code)
    atomic(folder / 'event.json', encoded(event))
    print(encoded({'log_folder': str(folder), 'duration_seconds': event['duration_seconds'], 'exit_code': code,
                   'note': 'Exit zero alone does not prove build/art acceptance; inspect outputs and logs.'}))
    return code

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    compact = subs.add_parser('summary')
    compact.add_argument('--scope', choices=['art_required','game_deferred','optional_deferred'])
    compact.add_argument('--package')
    compact.add_argument('--write', action='store_true', help='Write disposable derived summary, never the task ledger')
    storage = subs.add_parser('storage', help='Measure project size before a large build/export/package')
    storage.add_argument('--planned-growth-mib', type=float, default=0)
    storage.add_argument('--enforce', action='store_true', help='Exit 2 above 12 GiB or on scan errors')
    measured = subs.add_parser('run')
    measured.add_argument('--package', required=True)
    measured.add_argument('--label', required=True)
    measured.add_argument('--planned-growth-mib', type=float, required=True,
                          help='Declare 0 for no large output; positive values trigger a capacity preflight')
    measured.add_argument('command', nargs=argparse.REMAINDER)
    clean = subs.add_parser('clean', help='Reclaim build scratch; report superseded artefacts')
    clean.add_argument('--apply', action='store_true', help='delete the regenerable category')
    clean.add_argument('--json', action='store_true')
    clean.add_argument('--keep-builds', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'clean':
            import clean_workspace
            forward = [flag for flag, on in (('--apply', args.apply), ('--json', args.json),
                                             ('--keep-builds', args.keep_builds)) if on]
            return clean_workspace.main(forward)
        return (summary(args) if args.action == 'summary' else
                storage_command(args) if args.action == 'storage' else run_command(args))
    except (OSError, ValueError, KeyError, RecursionError) as exc:
        print(encoded({'status':'workflow_error','error':str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
