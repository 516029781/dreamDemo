# -*- coding: utf-8 -*-
r"""plan_doc_check.py — 规划文档机械校验（工作流硬规则）

校验三件事：
  1. 表格列数一致性：每张 markdown 表所有行与表头列数一致（忽略 \| 转义、忽略分隔行）。
  2. § 引用合法性：文内 `§N` / `§N.M` 必须能对应到本文 `## N.` / `### N.M` 标题。
  3. 外部引用：`某文件.md` §N —— 若同目录存在该文件，校验其含 `## N.` 标题。

用法：python tools/plan_doc_check.py <md文件> [更多md文件...]
退出码：0=全部通过，1=有失败。
"""
import re
import sys
from pathlib import Path


def split_row(line: str):
    r"""按 | 切分一行表格，忽略 \| 转义；行首/行尾的 | 只作边界不产生空格。"""
    cells, cur = [], []
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if c == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def is_sep(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells) and cells


def check_file(path: Path):
    errors, warnings = [], []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # 归档文件（横幅声明已并入/降级为过程记录）不再修改正文，悬空 § 引用降级为警告
    archived = any(("已并入" in ln or "降级为过程记录" in ln) for ln in lines[:10])
    if archived:
        warn_sink = warnings
    else:
        warn_sink = errors

    # ---- 1. 表格列数 ----
    tables = 0
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and is_sep(split_row(lines[i + 1])):
            tables += 1
            head_n = len(split_row(lines[i]))
            start = i
            i += 2
            rows = 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                n = len(split_row(lines[i]))
                if n != head_n:
                    errors.append(f"L{i+1} 表格列数 {n} != 表头 {head_n}（表起于 L{start+1}）")
                rows += 1
                i += 1
            if rows < 1:
                warnings.append(f"L{start+1} 表格只有表头")
        else:
            i += 1

    # ---- 2. 标题编号收集 ----
    h2, h3 = set(), set()
    for ln in lines:
        m = re.match(r"^##\s+(\d+)[\.\s]", ln)
        if m:
            h2.add(m.group(1))
        m = re.match(r"^###\s+(\d+\.\d+)[\s\.\u3002]", ln)
        if m:
            h3.add(m.group(1))

    # ---- 3. § 引用 ----
    body = "\n".join(lines)
    # 3a. 内部引用：§ 后跟数字（排除紧跟文件名反引号后的）
    for m in re.finditer(r"§(\d+(?:\.\d+)?)", body):
        ref = m.group(1)
        ok = ref in h2 or ref in h3
        if not ok and "." in ref:
            ok = ref.split(".")[0] in h2  # 允许引用到二级节下的内容
        if not ok:
            line_no = body[: m.start()].count("\n") + 1
            warn_sink.append(f"L{line_no} §{ref} 在本文无对应标题" + ("（归档件，忽略）" if archived else ""))
    # 3b. 外部引用：`X.md` §N
    for m in re.finditer(r"`([\w\.\-]+\.md)`\s*（?[^）]*?§(\d+(?:\.\d+)?)", body):
        fname, ref = m.group(1), m.group(2)
        target = path.parent / fname
        if not target.exists():
            line_no = body[: m.start()].count("\n") + 1
            warnings.append(f"L{line_no} 引用文件 {fname} 不存在（同目录）")
            continue
        ttext = target.read_text(encoding="utf-8")
        heads = set(re.findall(r"^#{2,3}\s+(\d+(?:\.\d+)?)[\.\s]", ttext, re.M))
        if not any(h == ref or h.startswith(ref + ".") for h in heads):
            line_no = body[: m.start()].count("\n") + 1
            errors.append(f"L{line_no} {fname} §{ref} 无对应标题")

    return tables, errors, warnings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    total_fail = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"[缺失] {p}")
            total_fail += 1
            continue
        tables, errors, warnings = check_file(p)
        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {p.name}：{tables} 张表格，{len(errors)} 处错误，{len(warnings)} 处警告")
        for e in errors:
            print(f"    ✗ {e}")
            total_fail += 1
        for w in warnings:
            print(f"    ! {w}")
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()
