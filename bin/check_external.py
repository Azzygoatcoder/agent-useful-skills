#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_external.py — 外部 skill 依赖的发现 / 契约校验 / 悬空链接检测

用法:
  python check_external.py                 # 报告（人类可读）
  python check_external.py --json          # 机读
  python check_external.py --emit-paths    # 只输出 "name<TAB>真实路径"，供部署脚本消费
  python check_external.py --strict        # 必需项缺失/不合规 → 退出码 1（可选缺失不算）
  python check_external.py --dsh-skills <dir>   # 指定 DSH 技能根（默认 ~/.dsh/skills）

为什么需要它：本仓库的技能会引用若干个**不随仓库分发**的外部 skill（diagram-design /
fireworks-tech-graph / md-format-fixer …）。它们常常只装在 ~/.claude/skills，
而 DSH 只发现 ~/.dsh/skills、~/.agents/skills 与 <项目>/.dsh/skills ——
于是「技能里写着 use diagram-design，DSH 里的模型却看不到它」。
本脚本把这件事从"靠记得"变成"可校验"。

DSH frontmatter 契约（与 bin/check_skills.py 同一套规则，此处只报不影响发现的硬问题 + 明显异常）：
  - name 存在、kebab-case、且与目录名一致（不一致 DSH 仍能发现，但按契约应当一致）
  - description 存在且非空
  - 无 legacy camelCase 键（disableModelInvocation / modelInvocable / userInvocable）——
    有则 DSH 加载器抛错并**静默丢弃**该技能
  - description 超长会被 catalog 截断（默认上限 500）

纯标准库。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

CATALOG_DESC_MAX = 500
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEGACY_KEYS = ("disableModelInvocation", "modelInvocable", "userInvocable")
DEFAULT_REGISTRY = Path(__file__).resolve().parent.parent / "skills.external.json"


def expand(p: str) -> Path:
    """展开 ~ 与 G:/ 这类正斜杠盘符路径。"""
    return Path(os.path.expanduser(p.replace("\\", "/")))


def locate(entry: dict, roots: list[Path]) -> tuple[Path | None, str]:
    """跨根查找一个外部 skill 的真实目录。返回 (路径, 说明)。"""
    name = entry["name"]
    kind = entry.get("kind", "skill-at-root")
    tried: list[str] = []

    candidates: list[Path] = []
    hint = entry.get("repoHint")
    if hint:
        base = expand(hint)
        # plugin 形态：仓库下 skills/<name>；skill-at-root：仓库根即技能目录
        candidates.append(base / "skills" / name if kind == "plugin" else base)
        candidates.append(base)  # repoHint 可能直接指向技能目录
    for root in roots:
        candidates.append(root / name)

    for c in candidates:
        tried.append(str(c))
        if c.is_dir() and (c / "SKILL.md").is_file():
            # 解析到最终真实路径：~/.claude/skills 下的条目本身可能还是 junction，
            # 双层间接会让链接目标随中间层变化而悬空，所以直接记真实盘符路径。
            return Path(os.path.realpath(c)), "found"
    return None, "tried: " + " | ".join(tried)


def parse_frontmatter(text: str) -> dict[str, str]:
    """极简 frontmatter 解析：顶层标量 + >/| 块标量（够用即可）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}
    meta: dict[str, str] = {}
    i = 1
    while i < end:
        m = re.match(r"^(\S+):\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest in ("", ">", "|", ">-", "|-"):
            j, block = i + 1, []
            while j < end and (not lines[j].strip() or lines[j][0] in " \t"):
                if lines[j].strip():
                    block.append(lines[j].strip())
                j += 1
            meta[key] = " ".join(block)
            i = j
            continue
        meta[key] = rest.strip("\"'")
        i += 1
    return meta


def check_contract(skill_dir: Path) -> tuple[list[str], list[str]]:
    """返回 (errors, warnings)。errors = 会被 DSH 丢弃；warnings = 能发现但效果打折。"""
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"缺 SKILL.md（DSH 单层发现要求 <技能根>/<技能名>/SKILL.md）"], []
    meta = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
    if not meta:
        return ["frontmatter 缺失或不可解析（DSH 会忽略该技能）"], []

    name = meta.get("name")
    if not name:
        errors.append("frontmatter 缺 name（DSH 会忽略该技能）")
    elif not NAME_RE.match(name):
        errors.append(f"name '{name}' 非 kebab-case")
    elif name != skill_dir.name:
        warnings.append(f"name '{name}' 与目录名 '{skill_dir.name}' 不一致")

    desc = meta.get("description")
    if not desc or not desc.strip():
        errors.append("frontmatter 缺 description（DSH 会忽略该技能）")
    elif len(desc) < 20:
        warnings.append(f"description 仅 {len(desc)} 字符——触发命中率低")
    elif len(desc) > CATALOG_DESC_MAX:
        warnings.append(
            f"description {len(desc)} 字符 > DSH catalog 上限 {CATALOG_DESC_MAX}，会被截断"
        )

    for k in LEGACY_KEYS:
        if k in meta:
            errors.append(f"legacy 键 '{k}' 会让 DSH 丢弃该技能")
    return errors, warnings


def link_state(dsh_skills: Path, name: str) -> tuple[str, str]:
    """返回 (状态, 说明)。状态 ∈ ok | missing | dangling | foreign"""
    dest = dsh_skills / name
    if not os.path.lexists(dest):
        return "missing", "未链接进 DSH 技能根"
    if not os.path.islink(dest) and not os.path.isdir(dest):
        return "dangling", "存在但不是目录/链接"
    if os.path.isdir(dest):
        return "ok", "已链接"
    return "dangling", "链接目标不存在（悬空）"


def main() -> int:
    ap = argparse.ArgumentParser(description="外部 skill 依赖检查")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--dsh-skills", type=Path,
                    default=Path(os.path.expanduser("~/.dsh/skills")))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-paths", action="store_true",
                    help="只输出 name<TAB>path，供部署脚本消费")
    ap.add_argument("--strict", action="store_true",
                    help="必需项缺失或契约不合规时退出码 1（optional 项不算）")
    args = ap.parse_args()

    if not args.registry.is_file():
        print(f"找不到依赖清单：{args.registry}", file=sys.stderr)
        return 2
    reg = json.loads(args.registry.read_text(encoding="utf-8"))
    roots = [expand(r) for r in reg.get("searchRoots", [])]
    entries = reg.get("external", [])

    results = []
    for e in entries:
        found, detail = locate(e, roots)
        item = {
            "name": e["name"],
            "optional": bool(e.get("optional")),
            "purpose": e.get("purpose", ""),
            "usedBy": e.get("usedBy", []),
            "path": str(found) if found else None,
            "found": found is not None,
            "errors": [],
            "warnings": [],
            "link": None,
        }
        if found:
            errs, warns = check_contract(found)
            item["errors"], item["warnings"] = errs, warns
            state, note = link_state(args.dsh_skills, e["name"])
            item["link"] = {"state": state, "note": note}
        else:
            item["locateDetail"] = detail
        results.append(item)

    if args.emit_paths:
        for r in results:
            if r["found"]:
                print(f"{r['name']}\t{r['path']}")
        return 0

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"外部 skill 依赖（清单：{args.registry.name}）")
        print(f"DSH 技能根：{args.dsh_skills}")
        print()
        hard = 0
        for r in results:
            tag = "可选" if r["optional"] else "必需"
            if not r["found"]:
                mark = "·" if r["optional"] else "✗"
                if not r["optional"]:
                    hard += 1
                print(f"  {mark} {r['name']:<22} [{tag}] 未找到")
                print(f"      用途：{r['purpose']}")
                print(f"      被引用：{', '.join(r['usedBy'])}")
                if r.get("locateDetail"):
                    print(f"      查找过：{r['locateDetail']}")
                if not r["optional"]:
                    print("      → 引用它的技能需走回退路线")
                continue
            link = r["link"] or {}
            state = link.get("state")
            if r["errors"]:
                mark = "✗"
                hard += 0 if r["optional"] else 1
            elif state != "ok":
                mark = "!"
            else:
                mark = "✓"
            print(f"  {mark} {r['name']:<22} [{tag}] {r['path']}")
            if state != "ok":
                print(f"      DSH 链接：{state} —— {link.get('note')}")
            for e_ in r["errors"]:
                print(f"      ERROR  {e_}")
            for w in r["warnings"]:
                print(f"      warn   {w}")
        print()
        missing = [r["name"] for r in results if not r["found"] and not r["optional"]]
        unlinked = [r["name"] for r in results
                    if r["found"] and (r["link"] or {}).get("state") != "ok"]
        if missing or unlinked:
            print("→ 修复：pwsh bin/redeploy-skills.ps1（会把找到的外部 skill 软链进 DSH 技能根）")
        else:
            print("✓ 全部就绪")
        if args.strict and hard:
            print(f"校验失败：{hard} 个必需依赖缺失或契约不合规")
            return 1

    if args.strict:
        hard = sum(1 for r in results
                   if not r["optional"] and (not r["found"] or r["errors"]))
        if hard:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
