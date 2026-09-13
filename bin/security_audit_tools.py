#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
security_audit_tools.py — 安全审计报告状态管理（审计 skill 的脚本工具）
科研骨架审计模块 | 依赖: 标准库

用法:
  python security_audit_tools.py list [--status open|fixed|deferred|not-fixed|partial] [--severity critical|high|medium|low] [--json]
  python security_audit_tools.py status [--report <SECURITY_AUDIT.md 路径>]
  python security_audit_tools.py diff-filter --commit <hash> [--report ...]
  python security_audit_tools.py mark-fixed SSRF-1 PATH-1 [--commit <hash>] [--report ...]
  python security_audit_tools.py mark-deferred SSRF-1 [--reason "文本"] [--report ...]

--report 缺省自动探测：cwd 的 docs/SECURITY_AUDIT.md → cwd 根 → 本仓库插件 docs/。

解析 SECURITY_AUDIT.md 里的 <!-- AUDIT:STATUS=... --> 注解；mark-* 直接改写注解行
（避免 Edit 工具 Unicode/空白匹配摩擦）。diff-filter 用 git diff 只列变更文件涉及的 findings。
"""

import argparse, json, os, re, subprocess, sys

# 仅在真实终端流上重配置（被 import 或 stdout 被替换时不炸）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ANNOT_RE = re.compile(
    r"<!--\s*AUDIT:STATUS=(\w+)\s+SEVERITY=(\w+)\s+FILE=(\S+)\s+LINES=([\d-]+)"
    r"(?:\s+COMMIT=(\S+))?\s*-->"
)
HEADING_RE = re.compile(r"^###\s+([A-Z]+-\d+)(?:\s*[—-]\s*(.*))?$")


def resolve_report(args_report):
    """定位 SECURITY_AUDIT.md。

    显式 --report 优先。否则按顺序探测：cwd 下的 docs/ 与根目录，
    再回退到本仓库插件的规范位置 <repo-root>/plugins/code-security-skills/docs/。
    探测不到时返回首选候选（交给 load_report 报清晰错误），而不是抛 FileNotFoundError。
    """
    if args_report:
        candidates = [args_report]
        if os.path.isfile(args_report):
            return args_report
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(here)
        candidates = [
            os.path.join("docs", "SECURITY_AUDIT.md"),
            "SECURITY_AUDIT.md",
            os.path.join(repo_root, "plugins", "code-security-skills",
                         "docs", "SECURITY_AUDIT.md"),
        ]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand
        return candidates[0]
    return candidates[0]


def load_report(path):
    """返回 [(id, title, {status,severity,file,lines,commit}, line_idx)]"""
    findings = []
    if not os.path.isfile(path):
        print(f"找不到审计报告：{path}", file=sys.stderr)
        print("用 --report <路径> 显式指定（例如 "
              "--report plugins/code-security-skills/docs/SECURITY_AUDIT.md）", file=sys.stderr)
        raise SystemExit(2)
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    cur_id = cur_title = None
    for i, ln in enumerate(lines):
        m = HEADING_RE.match(ln.strip())
        if m:
            cur_id, cur_title = m.group(1), (m.group(2) or "").strip()
            continue
        m = ANNOT_RE.search(ln)
        if m and cur_id:
            status, sev, file_, lines_, commit = m.groups()
            findings.append({
                "id": cur_id, "title": cur_title,
                "status": status, "severity": sev, "file": file_,
                "lines": lines_, "commit": commit, "line": i,
            })
            cur_id = cur_title = None
    return findings, lines


def cmd_list(args):
    findings, _ = load_report(resolve_report(args.report))
    if not findings:
        print("未找到 AUDIT 注解（检查报告是否含 <!-- AUDIT:STATUS=... --> 行）"); return
    if args.status:
        findings = [f for f in findings if f["status"] == args.status]
    if args.severity:
        findings = [f for f in findings if f["severity"] == args.severity]
    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2)); return
    for f in findings:
        cmt = f" commit={f['commit']}" if f["commit"] else ""
        print(f"{f['id']:10s} {f['status']:10s} {f['severity']:9s} {f['file']}:{f['lines']}  {f['title'][:40]}{cmt}")
    print(f"\n共 {len(findings)} 条")


def cmd_status(args):
    findings, _ = load_report(resolve_report(args.report))
    if not findings:
        print("未找到 AUDIT 注解"); return
    print(f"=== 修复进度 ({len(findings)} findings) ===")
    order = ["fixed", "not-fixed", "partial", "deferred", "open"]
    by_status = {}
    for f in findings:
        by_status.setdefault(f["status"], []).append(f)
    for s in order:
        n = len(by_status.get(s, []))
        if n:
            print(f"  {s:10s} {n}")
    other = sum(len(v) for k, v in by_status.items() if k not in order)
    if other:
        print(f"  other     {other}")
    fixed = len(by_status.get("fixed", []))
    print(f"  {'─'*16}\n  合计      {len(findings)}  ({fixed/len(findings)*100:.0f}% fixed)")
    nf = by_status.get("not-fixed", [])
    if nf:
        print("\n未修复：")
        for f in nf:
            print(f"  {f['id']:10s} {f['severity']:9s} {f['file']}:{f['lines']}")


def cmd_diff_filter(args):
    findings, _ = load_report(resolve_report(args.report))
    r = subprocess.run(["git", "diff", "--name-only", f"{args.commit}..HEAD"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"git diff 失败:\n{r.stderr}")
    changed = set(x.strip() for x in r.stdout.splitlines() if x.strip())
    touched = [f for f in findings if f["file"] in changed]
    print(f"变更文件 {len(changed)} 个，涉及 findings {len(touched)}/{len(findings)} 条：")
    for f in touched:
        print(f"  {f['id']:10s} {f['status']:10s} {f['file']}:{f['lines']}")
    unchanged = [f for f in findings if f["file"] not in changed]
    if unchanged:
        print(f"\n未变更文件 {len(unchanged)} 条（跳过，保持原状态）")


def _git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else ""


def cmd_mark(args, status_field, add_commit=True):
    path = resolve_report(args.report)
    findings, lines = load_report(path)
    by_id = {f["id"]: f for f in findings}
    missing = [i for i in args.ids if i not in by_id]
    if missing:
        sys.exit(f"找不到 ID: {', '.join(missing)}。现有: {', '.join(sorted(by_id))}")
    commit = getattr(args, "commit", None) or _git_head()
    changed = []
    for i in args.ids:
        f = by_id[i]
        if f["status"] == status_field:
            print(f"{i} 已是 {status_field}"); continue
        new = (f"<!-- AUDIT:STATUS={status_field} SEVERITY={f['severity']} FILE={f['file']} "
               f"LINES={f['lines']}")
        if add_commit and commit:
            new += f" COMMIT={commit}"
        new += " -->"
        lines[f["line"]] = re.sub(r"<!--.*?-->", new, lines[f["line"]], flags=re.S)
        changed.append((i, f["status"], status_field, commit))
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    for i, old, new, cmt in changed:
        c = f" (commit {cmt})" if cmt else ""
        print(f"{i}: {old} → {new}{c}")
    if not changed:
        print("无变更")


def cmd_mark_fixed(args):
    cmd_mark(args, "fixed")


def cmd_mark_deferred(args):
    cmd_mark(args, "deferred")


def main():
    p = argparse.ArgumentParser(description="安全审计报告状态管理")
    sub = p.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--report", help="报告路径（缺省自动探测 docs/、仓库根、本仓库插件 docs/）")

    l = sub.add_parser("list", parents=[common], help="列出 findings（可按状态/严重度过滤）")
    l.add_argument("--status"); l.add_argument("--severity"); l.add_argument("--json", action="store_true")

    s = sub.add_parser("status", parents=[common], help="修复进度汇总")
    d = sub.add_parser("diff-filter", parents=[common], help="git diff 变更文件 → 涉及 findings")
    d.add_argument("--commit", required=True, help="上次审计 commit hash")

    mf = sub.add_parser("mark-fixed", parents=[common], help="标记为已修复（改注解行，默认取当前 HEAD）")
    mf.add_argument("ids", nargs="+"); mf.add_argument("--commit")

    md = sub.add_parser("mark-deferred", parents=[common], help="标记为结构性延期")
    md.add_argument("ids", nargs="+"); md.add_argument("--reason", help="延期原因（写入标题后）")

    args = p.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "diff-filter":
        cmd_diff_filter(args)
    elif args.cmd == "mark-fixed":
        cmd_mark_fixed(args)
    elif args.cmd == "mark-deferred":
        cmd_mark_deferred(args)


if __name__ == "__main__":
    main()
