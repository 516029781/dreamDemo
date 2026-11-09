"""渲染图归一化：去掉 PNG 元数据，只保留像素与最小色彩块。

为什么需要：
Blender 写出的 PNG 会带 File / Date / RenderTime / cycles.* 等文本块，
这些值每次渲染都不同，导致 **像素完全相同、文件 SHA 不同**。
若证据契约直接绑定文件 SHA，复现检查会永远失败——本次 pilot 已实测到这一点。

做法：用 PIL 重编码为无 info 的 PNG（optimize 开），像素不变。
归一化后，两次逐位相同的渲染会得到相同的文件 SHA。

用法：
  python tools/normalize_render.py <png> [<png> ...]
  python tools/normalize_render.py --check <png>            # 只报告是否含可去元数据
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image

KEEP_MODE = "RGB"


def normalize(path: Path) -> dict:
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as im:
        had_info = sorted(im.info.keys())
        rgb = im.convert(KEEP_MODE)
    rgb.save(path, format="PNG", optimize=True)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "sha_before": before, "sha_after": after,
            "changed": before != after, "stripped_keys": had_info}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    check_only = argv[0] == "--check"
    for raw in argv[1:] if check_only else argv:
        p = Path(raw).resolve()
        with Image.open(p) as im:
            keys = sorted(im.info.keys())
        if check_only:
            print(f"{p.name}: {len(keys)} info keys -> {keys}")
            continue
        r = normalize(p)
        print(f"{p.name}: changed={r['changed']} sha16 {r['sha_before'][:16]} -> {r['sha_after'][:16]} "
              f"stripped={r['stripped_keys']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
