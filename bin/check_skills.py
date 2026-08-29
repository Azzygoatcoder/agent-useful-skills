#!/usr/bin/env python3
"""check_skills.py - 校验本仓库所有 SKILL.md 是否符合 DSH/AgentSkills 规则。

规则（与 @deepseek-ai/dsh-skill-filesystem 一致）：
  1. 技能目录必须是单层：<技能根>/<技能名>/SKILL.md（DSH 只发现这一层）
  2. frontmatter 必须含 name（kebab-case ^[a-z0-9]+(?:-[a-z0-9]+)*$）与 description（非空）
  3. 可选调用策略字段：whenToUse / disable-model-invocation / user-invocable（布尔）
  4. 运行时耦合提示（agent（Claude）等），保持跨运行时通用

用法：python bin/check_skills.py [--root 仓库根] [--strict]
退出码：0 = 全部通过；1 = 有错误（--strict 时警告也计错）
标准库实现，零第三方依赖（与仓库其余脚本一致）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BOOLEAN_FIELDS = {"disable-model-invocation", "user-invocable"}

# 运行时耦合提示（warning 级）：把 agent 假设写成特定模型
COUPLING_PATTERNS = [
    (re.compile(r"agent（Claude）|agent\s*\(\s*Claude\s*\)"), "把 agent 写死为 Claude（应写 'agent'）"),
]
# 运行时提及（info 级）：多运行时文档中合法出现，仅提示确认
RUNTIME_MENTIONS = [
    (re.compile(r"~/.claude|Claude Code"), "提及 Claude Code（多运行时文档中合法，确认非独占假设）"),
]


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str):
    """返回 (meta, errors)。minimal YAML：顶层标量 + >/| 块标量。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["缺少 frontmatter（必须以 --- 开头）"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, ["frontmatter 未闭合（找不到收尾 ---）"]
    meta: dict[str, str] = {}
    errors: list[str] = []
    i = 1
    while i < end:
        line = lines[i]
        m = re.match(r"^(\S+):\s*(.*)$", line)
        if m:
            key, rest = m.group(1), m.group(2).strip()
            if key in meta:
                errors.append(f"重复字段 '{key}'")
                i += 1
                continue
            if rest in ("", ">", "|", ">-", "|-"):
                # 块标量：收集后续缩进行
                j = i + 1
                block = []
                while j < end and (not lines[j].strip() or lines[j][0] in " \t"):
                    if lines[j].strip():
                        block.append(lines[j].strip())
                    j += 1
                meta[key] = " ".join(block)
                i = j
                continue
            meta[key] = unquote(rest)
        i += 1
    return meta, errors


def iter_skill_dirs(root: Path):
    """遍历所有技能根（skills/、plugins/*/skills/ 与 archive/）下的单层技能目录。"""
    roots = [root / "skills"]
    plugins = root / "plugins"
    if plugins.is_dir():
        roots += sorted(p / "skills" for p in plugins.iterdir() if p.is_dir())
    archive = root / "archive"
    if archive.is_dir():
        roots.append(archive)
    for base in roots:
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if entry.is_dir():
                yield entry


def check_skill(skill_dir: Path):
    """返回 (errors, warnings, infos)。"""
    errors, warnings, infos = [], [], []
    name = skill_dir.name
    if not SKILL_NAME_RE.match(name):
        warnings.append(f"目录名 '{name}' 不是 kebab-case（DSH 发现不校验，但建议与 name 一致）")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{skill_dir}: 缺少 SKILL.md（DSH 单层发现要求 <技能根>/<技能名>/SKILL.md）")
        return errors, warnings, infos
    text = skill_md.read_text(encoding="utf-8")
    meta, ferr = parse_frontmatter(text)
    if meta is None:
        errors += [f"{skill_md.name}: {e}" for e in ferr]
        return errors, warnings, infos
    errors += [f"{skill_md.name}: {e}" for e in ferr]

    fm_name = meta.get("name")
    if fm_name is None:
        errors.append(f"{skill_md.name}: frontmatter 缺少 name")
    elif not SKILL_NAME_RE.match(fm_name):
        errors.append(f"{skill_md.name}: name '{fm_name}' 非法（须 kebab-case ^[a-z0-9]+(?:-[a-z0-9]+)*$）")
    elif fm_name != name:
        warnings.append(f"{skill_md.name}: frontmatter name '{fm_name}' 与目录名 '{name}' 不一致")

    desc = meta.get("description")
    if desc is None:
        errors.append(f"{skill_md.name}: frontmatter 缺少 description（DSH 必需）")
    elif not desc.strip():
        errors.append(f"{skill_md.name}: description 为空")
    elif len(desc) < 20:
        warnings.append(f"{skill_md.name}: description 过短（{len(desc)} 字符）——弱模型触发命中率低，建议加触发词")

    for field in BOOLEAN_FIELDS:
        if field in meta and meta[field].strip().lower() not in ("true", "false"):
            errors.append(f"{skill_md.name}: '{field}' 必须是 true/false，实际 '{meta[field]}'")

    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    for pat, msg in COUPLING_PATTERNS:
        if pat.search(body):
            warnings.append(f"{skill_md.name}: {msg}")
    for pat, msg in RUNTIME_MENTIONS:
        if pat.search(body):
            infos.append(f"{skill_md.name}: {msg}")

    # 深层 SKILL.md：DSH 单层发现看不到，参考文件应改名或移入 references/
    nested = [p for p in skill_dir.rglob("SKILL.md") if p != skill_md]
    for p in nested:
        warnings.append(f"{p}: 嵌套超过单层，DSH 不会发现（参考文件请改名或移入 references/）")
    return errors, warnings, infos


def main() -> int:
    ap = argparse.ArgumentParser(description="校验 SKILL.md 是否符合 DSH/AgentSkills 规则")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="仓库根目录")
    ap.add_argument("--strict", action="store_true", help="警告也按错误计（退出码 1）")
    args = ap.parse_args()
    root: Path = args.root
    n_skills = n_err = n_warn = 0
    problems: list[str] = []
    for skill_dir in iter_skill_dirs(root):
        n_skills += 1
        errors, warnings, infos = check_skill(skill_dir)
        for w in infos:
            print(f"  info   {w}")
        for w in warnings:
            n_warn += 1
            problems.append(f"  warn   {w}")
        for e in errors:
            n_err += 1
            problems.append(f"  ERROR  {e}")
    print(f"检查 {n_skills} 个技能目录（root={root}）")
    if problems:
        print("\n".join(problems))
    print(f"结果：{n_err} 错误 / {n_warn} 警告")
    if n_err or (args.strict and n_warn):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
