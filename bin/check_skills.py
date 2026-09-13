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
import json
import re
import sys
from pathlib import Path

# 输出含中文与 ✅/✗：Windows 上 stdout 默认 cp1252，不重配置会 UnicodeEncodeError
# （在自家 CI 的 windows runner 上真实踩到过）。与 office_tools/data_plot 保持一致。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BOOLEAN_FIELDS = {"disable-model-invocation", "user-invocable"}
# DSH 运行时 catalog 的 description 截断上限（dsh-tool-skill: DEFAULT_CATALOG_DESCRIPTION_MAX_LENGTH）
CATALOG_DESC_MAX = 500

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
    """返回 (errors, warnings, infos)。

    全仓库统一校验，**不区分** plugins/superpowers：那虽然 fork 自 superpowers，但已经过本地
    改造、是我们要维护并改进的代码（见 plugins/superpowers/CLAUDE.md：「永不更新上游，
    原版 MIT 可自由修改」）。"不跟随上游"是为了可以自由改，不是不去动它。
    """
    errors, warnings, infos = [], [], []
    name = skill_dir.name
    if not SKILL_NAME_RE.match(name):
        warnings.append(f"目录名 '{name}' 不是 kebab-case（DSH 发现不校验，但建议与 name 一致）")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        # 归档目录刻意把 SKILL.md 改名，避免被单层发现当成现役技能
        if (skill_dir / "archived-SKILL.md").is_file():
            return errors, warnings, infos
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
    elif len(desc) > CATALOG_DESC_MAX:
        warnings.append(
            f"{skill_md.name}: description 超长（{len(desc)} > {CATALOG_DESC_MAX} 字符）"
            f"——DSH catalog 会截断，末尾触发词会丢"
        )

    for field in BOOLEAN_FIELDS:
        if field in meta and meta[field].strip().lower() not in ("true", "false"):
            errors.append(f"{skill_md.name}: '{field}' 必须是 true/false，实际 '{meta[field]}'")

    # legacy camelCase 键会让 DSH 加载器直接抛错 → 技能被静默丢弃
    for legacy, canonical in (("disableModelInvocation", "disable-model-invocation"),
                              ("modelInvocable", "disable-model-invocation"),
                              ("userInvocable", "user-invocable")):
        if legacy in meta:
            errors.append(f"{skill_md.name}: legacy 键 '{legacy}' 会让 DSH 丢弃该技能，改用 '{canonical}'")

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


# ─────────────────────────────────────────────────────────────
# 仓库级校验
# ─────────────────────────────────────────────────────────────

def _skill_dirs_by_name(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in iter_skill_dirs(root):
        out[d.name] = d
    return out


def check_manifest(root: Path):
    """skills.manifest.json ↔ 实际技能目录 双向一致（注册契约）。"""
    errors = []
    mf = root / "skills.manifest.json"
    if not mf.is_file():
        return [f"缺少 skills.manifest.json（DSH 插件与 redeploy-skills.ps1 的注册契约）"]
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
        names = data["default"]
        if not isinstance(names, list) or not names:
            return ["skills.manifest.json 的 default 必须是非空数组"]
    except Exception as exc:
        return [f"skills.manifest.json 解析失败：{exc}"]

    dirs = _skill_dirs_by_name(root)
    # archive/ 不参与注册
    registered = {n for n in names}
    for n in names:
        if n not in dirs:
            errors.append(f"skills.manifest.json 注册了 '{n}'，但仓库内没有对应技能目录")
        elif n != dirs[n].name:
            errors.append(f"'{n}' 的目录名与清单不一致")
    live_dirs = {
        d.name for d in iter_skill_dirs(root)
        if "archive" not in d.parts
    }
    for extra in sorted(live_dirs - registered - CATALOG_EXCLUDED):
        errors.append(
            f"技能目录 '{extra}' 存在但未在 skills.manifest.json 注册"
            f"（要么加入清单，要么移入 archive/）"
        )
    dupes = [n for n in registered if names.count(n) > 1]
    for d in sorted(set(dupes)):
        errors.append(f"skills.manifest.json 中 '{d}' 重复")
    return errors


def check_evolution_log(root: Path):
    """已注册技能缺 '## 自进化日志' 时提示。

    上游派生技能按 plugins/superpowers/CLAUDE.md「不覆盖上游已调优内容」有意豁免，
    在此显式列出豁免名单，避免每次都在同一处报噪音。
    """
    warnings = []
    upstream_exempt = {
        "using-superpowers", "test-driven-development", "systematic-debugging",
        "verification-before-completion", "subagent-driven-development",
    }
    try:
        names = json.loads((root / "skills.manifest.json").read_text(encoding="utf-8"))["default"]
    except Exception:
        return warnings
    dirs = _skill_dirs_by_name(root)
    for n in names:
        d = dirs.get(n)
        if d is None:
            continue
        sm = d / "SKILL.md"
        if not sm.is_file():
            continue
        if "自进化日志" in sm.read_text(encoding="utf-8"):
            continue
        if n in upstream_exempt:
            continue
        warnings.append(f"{n}: 缺少 '## 自进化日志'（skeleton.md 约定的实战回写位）")
    return warnings


def check_plugin_manifests(root: Path):
    """plugins/*/.claude-plugin/plugin.json 必须有 name/version，版本不得与 README 横幅矛盾。"""
    errors = []
    plugins = root / "plugins"
    if not plugins.is_dir():
        return errors
    for pj in sorted(plugins.glob("*/.claude-plugin/plugin.json")):
        rel = pj.relative_to(root).as_posix()
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel}: JSON 解析失败：{exc}")
            continue
        for key in ("name", "version"):
            if not data.get(key):
                errors.append(f"{rel}: 缺少 '{key}'")
        readme = pj.parent.parent / "README.md"
        if readme.is_file() and data.get("version"):
            head = readme.read_text(encoding="utf-8")[:1200]
            ver = str(data["version"])
            m = re.search(r"\*\*v(\d+\.\d+\.\d+)\*\*", head)
            if m and m.group(1) != ver:
                errors.append(
                    f"{rel}: version={ver} 与 {readme.name} 横幅 v{m.group(1)} 不一致"
                    f"（VERSIONING.md 要求同步）"
                )
    return errors


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# 刻意不参与模型自动调用、但仍在技能目录里的技能（须设 disable-model-invocation: true）
CATALOG_EXCLUDED = {"using-superpowers"}
CODE_PATH_RE = re.compile(
    r"`([A-Za-z0-9_./\\-]+\.(?:py|mjs|cjs|js|ps1|md|json|yml|yaml|toml|sh|tex|bib|html|svg))`"
)
# 本仓库自有顶层目录：只有落在这些目录下的反引号路径才做存在性校验
REPO_OWNED_ROOTS = {"bin", "skills", "plugins", "latex-templates", "assets", "archive"}
# 幽灵 skill 引用：只认「反引号包住的名字 + 紧跟 skill/技能」这一种确定写法。
# 负向前瞻排除文件续写（`xxx-code-review-checklist.md` 里 -checklist 会被误当后缀词），
# 避免把 `code-review-checklist.md`、prose 里的 "code-review methodology" 误报。
CITE_RE = re.compile(
    r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`(?![-\w.])"
    r"\s*(?:skill|技能)"
)


def _mask_evolution_log(text: str) -> str:
    """把 '## 自进化日志' 段（到下一个同级/更高级标题为止）整体遮蔽成空行。

    自进化日志是历史记录：「此前委托了不存在的 X」这类句子必须能写，否则修复本身
    就报错。遮蔽保留行数，让报错行号依然准确。
    """
    lines = text.splitlines()
    out = []
    in_log = False
    for ln in lines:
        m = re.match(r"^(#{1,6})\s", ln)
        if m:
            in_log = "自进化日志" in ln
        out.append("" if in_log else ln)
    return "\n".join(out)


def check_references(root: Path):
    """解析每个技能目录内的 md 相对链接与反引号路径；检出幽灵 skill 引用与孤儿参考文件。

    只检查**非归档**技能：archive/ 是刻意不维护的存档，对它报断链只会制造噪音。
    """
    errors, warnings = [], []
    dirs = _skill_dirs_by_name(root)
    live = {n: d for n, d in dirs.items() if "archive" not in d.parts}
    known = set(dirs)
    archived = {d.name for d in iter_skill_dirs(root) if "archive" in d.parts}

    for name, d in sorted(live.items()):
        mds = sorted(d.rglob("*.md"))
        # 孤儿参考文件：references/ 下的文件没被同技能任何 md 提到
        refdir = d / "references"
        if refdir.is_dir():
            all_text = "\n".join(
                p.read_text(encoding="utf-8", errors="replace") for p in mds
            )
            for rf in sorted(refdir.glob("*")):
                if rf.is_file() and rf.name not in all_text:
                    warnings.append(
                        f"{name}: references/{rf.name} 未被任何文件引用（孤儿，DSH 不会加载）"
                    )
        for md in mds:
            try:
                text = md.read_text(encoding="utf-8")
            except Exception:
                continue
            rel = md.relative_to(root).as_posix()
            for m in LINK_RE.finditer(text):
                t = m.group(1)
                if t.startswith(("http://", "https://", "mailto:", "#", "data:")):
                    continue
                part = t.split("#", 1)[0]
                if not part:
                    continue
                # 文档里的占位符示例（assets/xxx.png、path/to/...）不算断链
                if re.search(r"\bxxx+\b|your-|path/to|<[^>]+>", part):
                    continue
                if not (md.parent / part).exists():
                    errors.append(f"{rel}: 相对链接失效 -> {t}")
            for m in CODE_PATH_RE.finditer(text):
                tok = m.group(1).replace("\\", "/")
                # 只对「看起来是路径」的 token 报（含斜杠）。裸文件名（server.py）多为
                # 同目录引用或叙述，误报率高，交给相对链接检查即可。
                if "/" not in tok or tok.startswith("/"):
                    continue
                if re.search(r"\bxxx+\b|your-|<[^>]+>", tok):
                    continue
                # 只报「指向本仓库自有目录」的路径（bin/ skills/ plugins/ latex-templates/ assets/）。
                # 被审计项目里的路径（docs/SECURITY_AUDIT.md、papers/arxiv_fetch.py、
                # .superpowers/...）不归本仓库管，报了全是噪音。
                if tok.split("/", 1)[0] not in REPO_OWNED_ROOTS:
                    continue
                anchors = [md.parent, root, d, root / "bin", root / "plugins", root / "skills"]
                if any((a / tok).exists() for a in anchors):
                    continue
                warnings.append(f"{rel}: 反引号路径可能失效 -> {tok}")
            # 幽灵 skill 引用：`name` skill / `name` 技能
            #   跳过「## 自进化日志」段：那里记录的是历史（如"此前委托了不存在的 X"），
            #   不是当前指令；对历史报错会把"记录一次修复"变成新的错误。
            phantom = _mask_evolution_log(text)
            for m in CITE_RE.finditer(phantom):
                cand = m.group(1)
                if cand in known or cand in archived:
                    continue
                errors.append(
                    f"{rel}: 引用了不存在的 skill '{cand}'（既不在注册清单也不在 archive/）"
                )
            # 把已归档 skill 当现役宣传
            for a in sorted(archived):
                for pat in (rf"`{re.escape(a)}`\s+skill", rf"委托\s+`{re.escape(a)}`"):
                    if re.search(pat, text):
                        warnings.append(
                            f"{rel}: 把已归档的 '{a}' 当现役技能引用（默认不注册）"
                        )
    return errors, warnings


def check_diagrams(root: Path):
    """配图一致性：每个 `assets/*.html` 图源必须有同步的派生素材。

    配图约定是「HTML 唯一图源，SVG/PNG 由 bin/export_diagram.py 派生」。
    此前这条靠手工，漂移过两次（孤儿 HTML/SVG、缺 xmlns 导致 <img> 不渲染）。
    """
    errors = []
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from export_diagram import build_svg  # 复用同一份导出逻辑，避免两处漂移
    except Exception as exc:
        # 不能静默降级：否则这条检查会在 CI 里"看起来通过"却什么都没查
        return [f"无法加载 bin/export_diagram.py，配图一致性无法校验：{exc}"]

    sources = sorted(p for p in root.rglob("assets/*.html") if "archive" not in p.parts)
    for html in sources:
        rel = html.relative_to(root).as_posix()
        text = html.read_text(encoding="utf-8")
        # 只有内联 SVG 的才是"配图图源"；报告模板等普通 HTML 不参与派生
        if not re.search(r"<svg\b", text):
            continue
        svg_path = html.with_suffix(".svg")
        if not svg_path.is_file():
            errors.append(f"{rel}: 缺派生 SVG（跑 python bin/export_diagram.py {rel}）")
            continue
        try:
            want = build_svg(text)
        except ValueError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        if svg_path.read_text(encoding="utf-8") != want:
            errors.append(
                f"{rel}: 派生 SVG 已漂移（跑 python bin/export_diagram.py {rel} 重新导出）"
            )
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="校验 SKILL.md 是否符合 DSH/AgentSkills 规则")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="仓库根目录")
    ap.add_argument("--strict", action="store_true", help="警告也按错误计（退出码 1）")
    ap.add_argument("--no-refs", action="store_true", help="跳过跨文件引用解析（快，但漏掉断链/幽灵引用）")
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

    # 仓库级检查：清单一致 / 归档引用 / 自进化日志 / 插件清单
    for e in check_manifest(root):
        n_err += 1
        problems.append(f"  ERROR  {e}")
    for w in check_evolution_log(root):
        n_warn += 1
        problems.append(f"  warn   {w}")
    for e in check_plugin_manifests(root):
        n_err += 1
        problems.append(f"  ERROR  {e}")
    for e in check_diagrams(root):
        n_err += 1
        problems.append(f"  ERROR  {e}")

    # 跨文件引用解析（断链 / 幽灵 skill 引用 / 孤儿参考文件）
    if not args.no_refs:
        ref_err, ref_warn = check_references(root)
        for e in ref_err:
            n_err += 1
            problems.append(f"  ERROR  {e}")
        for w in ref_warn:
            n_warn += 1
            problems.append(f"  warn   {w}")

    print(f"检查 {n_skills} 个技能目录（root={root}）")
    if problems:
        print("\n".join(problems))
    print(f"结果：{n_err} 错误 / {n_warn} 警告")
    if n_err or (args.strict and n_warn):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
