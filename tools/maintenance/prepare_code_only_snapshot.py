#!/usr/bin/env python3
"""Prepare an isolated, code-only Git snapshot; never replace the live .git."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {
    '.py', '.ts', '.js', '.json', '.jsonl', '.md', '.scene', '.meta',
    '.ps1', '.sh', '.toml', '.yaml', '.yml', '.css', '.html', '.txt',
}
EXCLUDE_PREFIXES = (
    'reference/', 'art/candidates/', 'art/phase1/', 'art/full/',
    'art/iterations/', 'screenshots/', 'vibe_images/', 'images/',
    'assets/', 'audio/', 'tools/cocos/logs/', 'tools/blender/out/',
)
ASSET_ROOTS = (
    'art/candidates/candidate_n4', 'art/candidates/candidate_n5',
    'demo_n4/assets/resources', 'demo_n5/assets/resources',
    'reference/_raw_screenshots/P1',
)
REQUIRED_CODE = {
    'demo_n5/assets/scripts/CourtyardBootstrap.ts',
    'demo_n5/assets/scenes/main.scene',
    'tools/cocos/build_web_desktop.py',
    'tools/maintenance/prepare_code_only_snapshot.py',
    'planning/performance/CODE_ONLY_GIT_POLICY.md',
    'planning/performance/LOCAL_ASSET_MANIFEST.json',
}
FORBIDDEN_BINARY_SUFFIXES = {
    '.blend', '.glb', '.png', '.jpg', '.jpeg', '.gif', '.zip',
    '.ttf', '.m4s', '.mp4', '.skel', '.atlas',
}


def wanted(relative: str) -> bool:
    path = Path(relative)
    if relative.startswith(EXCLUDE_PREFIXES):
        return False
    if relative.startswith('tools/source_search/') and path.suffix == '.json':
        return False
    if relative.startswith('delivery/') and path.suffix not in {'.py', '.js', '.md'}:
        return False
    if path.name == '.gitattributes':
        return False  # the fresh repository has no Git LFS filters
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {
        '.gitignore', '.eslintrc.js', 'LICENSE', 'Dockerfile', 'Makefile',
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    stage = ROOT / '.tooling' / ('code_only_snapshot_' + stamp)
    stage.mkdir(parents=True, exist_ok=False)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT)
    chosen = []
    for relative in tracked.decode('utf-8').split('\0'):
        if not relative or not wanted(relative):
            continue
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            continue
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        chosen.append(relative)

    asset_rows = []
    for relative_root in ASSET_ROOTS:
        base = ROOT / relative_root
        if not base.is_dir():
            continue
        for path in base.rglob('*'):
            if not path.is_file() or path.is_symlink() or path.suffix == '.meta':
                continue
            asset_rows.append({
                'path': path.relative_to(ROOT).as_posix(),
                'bytes': path.stat().st_size,
                'sha256': sha256(path),
            })
    asset_rows.sort(key=lambda item: item['path'])
    manifest = {
        'kind': 'local_assets_not_in_git',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'note': 'Hash index only. Asset bytes remain in the original project and need independent backup.',
        'files': asset_rows,
    }
    manifest_path = stage / 'planning/performance/LOCAL_ASSET_MANIFEST.json'
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    subprocess.run(['git', 'init', '-b', 'master'], cwd=stage, check=True, capture_output=True)
    subprocess.run(['git', 'add', '-A'], cwd=stage, check=True, capture_output=True)
    staged = {
        p for p in subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=stage)
        .decode('utf-8').split('\0') if p
    }
    missing = sorted(REQUIRED_CODE - staged)
    binary = sorted(p for p in staged if Path(p).suffix.lower() in FORBIDDEN_BINARY_SUFFIXES)
    if missing or binary:
        raise RuntimeError('Invalid code-only snapshot: missing=' + repr(missing) + ', binary=' + repr(binary[:10]))
    name = subprocess.run(['git', 'config', 'user.name'], cwd=ROOT, text=True, capture_output=True).stdout.strip() or 'Local Snapshot'
    email = subprocess.run(['git', 'config', 'user.email'], cwd=ROOT, text=True, capture_output=True).stdout.strip() or 'snapshot@local.invalid'
    subprocess.run(['git', '-c', 'user.name=' + name, '-c', 'user.email=' + email,
                    'commit', '-q', '-m', 'Code-only snapshot; assets indexed locally'],
                   cwd=stage, check=True)

    included_bytes = sum((ROOT / p).stat().st_size for p in chosen)
    git_bytes = sum(p.stat().st_size for p in (stage / '.git').rglob('*') if p.is_file())
    print(json.dumps({
        'snapshot': str(stage), 'code_files': len(chosen),
        'code_bytes': included_bytes, 'asset_index_files': len(asset_rows),
        'asset_index_bytes': sum(row['bytes'] for row in asset_rows),
        'new_git_bytes': git_bytes,
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=stage, text=True).strip(),
        'replaces_live_repository': False,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
