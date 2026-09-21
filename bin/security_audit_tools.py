#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
security_audit_tools.py — 安全审计报告状态管理（审计 skill 的脚本工具）
科研骨架审计模块 | 依赖: 标准库

用法:
  python security_audit_tools.py list [--status open|fixed|deferred|not-fixed|partial]
                                      [--severity critical|high|medium|low]
                                      [--verdict confirmed|needs-validation|rejected] [--json]
  python security_audit_tools.py status [--report <SECURITY_AUDIT.md 路径>]
  python security_audit_tools.py validate [--report ...]
  python security_audit_tools.py diff-filter --commit <hash> [--report ...]
  python security_audit_tools.py mark-fixed SSRF-1 PATH-1 [--commit <hash>] [--report ...]
  python security_audit_tools.py mark-deferred SSRF-1 [--reason "文本"] [--report ...]

--report 缺省自动探测：cwd 的 docs/SECURITY_AUDIT.md → cwd 根 → 本仓库插件 docs/。

解析 SECURITY_AUDIT.md 里的 <!-- AUDIT:... --> 注解；mark-* 直接改写注解行
（避免 Edit 工具 Unicode/空白匹配摩擦）。diff-filter 用 git diff 只列变更文件涉及的 findings。
validate 校验注解契约，退出码 1 = 有问题（接入 CI：python bin/security_audit_tools.py validate）。

注解字段（顺序固定；除 FILE/LINES 外皆可选）：
  VERDICT  confirmed（缺省）/ needs-validation / rejected —— 认识态
  STATUS   open / fixed / deferred / not-fixed / partial —— 修复态（与 VERDICT 正交）
  SEVERITY critical / high / medium / low —— 仅 confirmed 允许；不确定就不许定级
  FILE     仓库根相对 POSIX 路径          LINES  行区间 <start>-<end>
  COMMIT   修复提交（fixed 必填，须为 HEAD 祖先）
  REASON   判定理由（rejected 必填 / deferred 可用）   BLOCKER 缺失事实（needs-validation 必填）
"""

import argparse, json, os, re, subprocess, sys

# 仅在真实终端流上重配置（被 import 或 stdout 被替换时不炸）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 字段顺序固定：VERDICT? STATUS? SEVERITY? FILE LINES COMMIT? REASON? BLOCKER?
# 解析器刻意宽松（缺字段也读得出来），严格性交给 validate —— 这样 status/list
# 在报告写歪时仍然可用，而 validate 负责指出歪在哪。
ANNOT_RE = re.compile(
    r"<!--\s*AUDIT:\s*"
    r"(?:VERDICT=(\S+)\s+)?"
    r"(?:STATUS=(\w+)\s+)?"
    r"(?:SEVERITY=(\w+)\s+)?"
    r"FILE=(\S+)\s+LINES=([\d,\-]+)"
    r"(?:\s+COMMIT=(\S+))?"
    r"(?:\s+REASON=\"([^\"]*)\")?"
    r"(?:\s+BLOCKER=\"([^\"]*)\")?"
    r"\s*-->"
)
HEADING_RE = re.compile(r"^###\s+([A-Z]+-\d+)(?:\s*[—-]\s*(.*))?$")

VERDICTS = ("confirmed", "needs-validation", "rejected")
STATUSES = ("open", "fixed", "deferred", "not-fixed", "partial")
SEVERITIES = ("critical", "high", "medium", "low")
# 前缀表（与 references/audit-workflow.md 的 ID 表保持一致）
ID_PREFIXES = ("SSRF", "PATH", "AUTH", "CMD", "XSS", "SECRET",
               "CRYPTO", "DEP", "STATE", "CODE", "META",
               # attack-surfaces.md 的 5 个面
               "PROMPT", "SUPPLY", "IPC", "RES", "TENANT")


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
    """返回 (findings, lines)。

    finding = {id,title,verdict,status,severity,file,lines,commit,reason,blocker,line}
    VERDICT 缺省为 confirmed —— 旧报告（无该字段）无需改动即可继续解析。
    """
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
            verdict, status, sev, file_, lines_, commit, reason, blocker = m.groups()
            findings.append({
                "id": cur_id, "title": cur_title,
                "verdict": verdict or "confirmed",
                "status": status, "severity": sev, "file": file_,
                "lines": lines_, "commit": commit, "reason": reason,
                "blocker": blocker, "line": i,
            })
            cur_id = cur_title = None
    return findings, lines


def render_annot(f):
    """按固定字段顺序渲染注解行，只写有值的字段。

    mark-* 走这里而不是拼字符串，保证改写时 VERDICT / BLOCKER 不会被丢掉。
    """
    fields = []
    if f.get("verdict"):
        fields.append(f"VERDICT={f['verdict']}")
    if f.get("status"):
        fields.append(f"STATUS={f['status']}")
    if f.get("severity"):
        fields.append(f"SEVERITY={f['severity']}")
    fields.append(f"FILE={f['file']}")
    fields.append(f"LINES={f['lines']}")
    if f.get("commit"):
        fields.append(f"COMMIT={f['commit']}")
    if f.get("reason"):
        fields.append(f'REASON="{f["reason"]}"')
    if f.get("blocker"):
        fields.append(f'BLOCKER="{f["blocker"]}"')
    return "<!-- AUDIT:" + " ".join(fields) + " -->"


def _sev(f):
    return f["severity"] or "—"


def cmd_list(args):
    findings, _ = load_report(resolve_report(args.report))
    if not findings:
        print("未找到 AUDIT 注解（检查报告是否含 <!-- AUDIT:... --> 行）"); return
    if args.status:
        findings = [f for f in findings if f["status"] == args.status]
    if args.severity:
        findings = [f for f in findings if f["severity"] == args.severity]
    if args.verdict:
        findings = [f for f in findings if f["verdict"] == args.verdict]
    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2)); return
    for f in findings:
        cmt = f" commit={f['commit']}" if f["commit"] else ""
        rsn = f"  原因: {f['reason']}" if f.get("reason") else ""
        blk = f"  缺口: {f['blocker']}" if f.get("blocker") else ""
        st = f["status"] or "—"
        print(f"{f['id']:10s} {f['verdict']:16s} {st:10s} {_sev(f):9s} "
              f"{f['file']}:{f['lines']}  {f['title'][:40]}{cmt}")
        if rsn:
            print(rsn)
        if blk:
            print(blk)
    print(f"\n共 {len(findings)} 条")


def cmd_status(args):
    findings, _ = load_report(resolve_report(args.report))
    if not findings:
        print("未找到 AUDIT 注解"); return

    print(f"=== 认识态 ({len(findings)} findings) ===")
    by_verdict = {}
    for f in findings:
        by_verdict.setdefault(f["verdict"], []).append(f)
    for v in VERDICTS:
        n = len(by_verdict.get(v, []))
        if n:
            print(f"  {v:16s} {n}")
    other_v = sum(len(x) for k, x in by_verdict.items() if k not in VERDICTS)
    if other_v:
        print(f"  {'other':16s} {other_v}")

    # 修复进度只在"要修的东西"上算 —— rejected 不是工作项，不拉低百分比
    todo = [f for f in findings if f["verdict"] != "rejected"]
    by_status = {}
    for f in todo:
        by_status.setdefault(f["status"], []).append(f)
    print(f"\n=== 修复进度 (分母 {len(todo)}，已排除 rejected) ===")
    for s in ("fixed", "not-fixed", "partial", "deferred", "open"):
        n = len(by_status.get(s, []))
        if n:
            print(f"  {s:10s} {n}")
    untracked = len(by_status.get(None, []))
    if untracked:
        print(f"  {'(无 STATUS)':10s} {untracked}")
    fixed = len(by_status.get("fixed", []))
    if todo:
        print(f"  {'─'*16}\n  合计      {len(todo)}  ({fixed/len(todo)*100:.0f}% fixed)")

    # not-fixed 与 partial 都要逐条列出 —— 只报计数会把"部分修复"静默吞掉
    for s in ("not-fixed", "partial"):
        rows = by_status.get(s, [])
        if rows:
            print(f"\n{s}：")
            for f in rows:
                print(f"  {f['id']:10s} {_sev(f):9s} {f['file']}:{f['lines']}")


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
        print(f"  {f['id']:10s} {f['status'] or '—':10s} {f['file']}:{f['lines']}")
    unchanged = [f for f in findings if f["file"] not in changed]
    if unchanged:
        # 未变更 ≠ 可以静默沿用旧结论：修复可能落在别的文件（共享工具里加 guard）。
        print(f"\n未变更文件 {len(unchanged)} 条（跳过重读，保持原状态）——"
              f"须在报告的 Coverage / Re-audit 段逐条列出：")
        for f in unchanged:
            print(f"  {f['id']:10s} {f['status'] or '—':10s} {f['verdict']:16s} "
                  f"{f['file']}:{f['lines']}")


def _git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else ""


def _have_git():
    r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                       capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "true"


def _is_ancestor(commit):
    r = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                       capture_output=True, text=True)
    return r.returncode == 0


def _src_root():
    """FILE 字段的基准目录。

    契约是"仓库根相对" —— 所以基准取 git 顶层（与 `git diff --name-only` 的输出
    同一基准），而不是 cwd。两者不一致时以 git 顶层的匹配为准，避免"审计目标是子目录
    时 FILE 全部匹配不上、被静默判为未变更"（安全工具里这是漏报来源）。
    """
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip().replace("\\", "/")
    return os.getcwd().replace("\\", "/")


def _parse_spans(lines_str):
    """解析 LINES：一个或多个 span，逗号分隔；每个 span 是 `N` 或 `A-B`。

    返回 [(a, b), ...]；格式非法返回 None。支持逗号是必要的 —— 历史报告里出现过
    `LINES=475,510`（两个独立位置），旧正则 `[\\d-]+` 匹配不上，那条 finding
    会被**静默丢掉**（status/list/count 全都少一条）。
    """
    if not lines_str:
        return None
    spans = []
    for part in lines_str.split(","):
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not m:
            return None
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        if a < 1 or b < a:
            return None
        spans.append((a, b))
    return spans or None


def _safe_repo_path(p):
    """仓库根相对 POSIX 路径：禁绝对路径、盘符、反斜杠、`~`、空段与 `..`。"""
    if not p or p.startswith("/") or p.startswith("~") or p.startswith("\\"):
        return False
    if "\\" in p or ":" in p:
        return False
    return all(seg not in ("", ".", "..") for seg in p.split("/"))


def _count_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return None


def _baseline_rewritten(lines):
    """报告是否显式声明了"基线 commit 已不可达（历史被重写）"。

    这是 COMMIT 祖先校验的**唯一**合法豁免，且必须写在报告里 —— 不允许静默跳过。
    触发场景：rebase/squash 之后原审计基线不在 HEAD 祖先链上（本仓库实测过，
    `git diff` 会返回上百个无关路径）。
    """
    return any(re.match(r"^\*\*Provenance:\*\*\s*baseline-rewritten\b", ln.strip())
               for ln in lines)


def _has_coverage_section(lines):
    """报告必须有非空的 `## Coverage` 段 —— 覆盖率不能只靠一句口号。"""
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^##\s+Coverage\b", ln.strip()):
            start = i
            break
    if start is None:
        return False
    for ln in lines[start + 1:]:
        if re.match(r"^##\s+\S", ln.strip()):
            break
        if ln.strip():
            return True
    return False


def cmd_validate(args):
    """校验注解契约。退出码 0 = 通过，1 = 有问题。

    只做六类真检查 —— 不引入 JSON Schema，不复制一份真相：
      1. ID 唯一且前缀在表内
      2. VERDICT 合法；needs-validation / rejected 禁带 SEVERITY；confirmed 必须有 SEVERITY；
         needs-validation 必须有 BLOCKER；rejected 必须有 REASON
      3. STATUS 合法
      4. FILE 是安全的仓库根相对路径，且文件存在
      5. LINES 合法，且 end 不超过文件实际行数
      6. STATUS=fixed 必须有 COMMIT，且该 commit 是 HEAD 的祖先（provenance）
      7. 报告含非空 `## Coverage` 段
    """
    path = resolve_report(args.report)
    findings, lines = load_report(path)
    src_root = _src_root()
    baseline_rewritten = _baseline_rewritten(lines)
    errs = []

    if not findings:
        errs.append("报告里没有任何 finding（需要 `### <PREFIX>-<N>` 标题 + 紧随其后的 <!-- AUDIT:... --> 注解）")

    # 1. ID
    seen = {}
    for f in findings:
        if f["id"] in seen:
            errs.append(f"{f['id']}: ID 重复（第 {seen[f['id']]+1} 与第 {f['line']+1} 行）")
        else:
            seen[f["id"]] = f["line"]
        prefix = f["id"].split("-")[0]
        if prefix not in ID_PREFIXES:
            errs.append(f"{f['id']}: 前缀 '{prefix}' 不在 ID 前缀表内 "
                        f"（{'/'.join(ID_PREFIXES)}）")

    for f in findings:
        loc = f"{f['id']} (第 {f['line']+1} 行)"
        v = f["verdict"]

        # 2. VERDICT / SEVERITY 契约 —— 不确定就不许定级
        if v not in VERDICTS:
            errs.append(f"{loc}: VERDICT '{v}' 非法（{'/'.join(VERDICTS)}）")
        if v in ("needs-validation", "rejected") and f["severity"]:
            errs.append(f"{loc}: VERDICT={v} 不得带 SEVERITY —— "
                        f"不确定就不许定级（改标 BLOCKER 或降为 needs-validation）")
        if v == "confirmed" and not f["severity"]:
            errs.append(f"{loc}: VERDICT=confirmed 必须有 SEVERITY")
        if f["severity"] and f["severity"] not in SEVERITIES:
            errs.append(f"{loc}: SEVERITY '{f['severity']}' 非法（{'/'.join(SEVERITIES)}）")
        if v == "needs-validation" and not f["blocker"]:
            errs.append(f"{loc}: VERDICT=needs-validation 必须有 BLOCKER=\"缺失的那个事实\"")
        if v == "rejected" and not f["reason"]:
            errs.append(f"{loc}: VERDICT=rejected 必须有 REASON=\"判定理由\"")

        # 3. STATUS
        if f["status"] and f["status"] not in STATUSES:
            errs.append(f"{loc}: STATUS '{f['status']}' 非法（{'/'.join(STATUSES)}）")

        # 4. FILE（基准 = git 顶层，与 git diff 输出一致）
        rel = f["file"]
        if not _safe_repo_path(rel):
            errs.append(f"{loc}: FILE '{rel}' 不是安全的仓库根相对 POSIX 路径"
                        f"（禁绝对路径/盘符/反斜杠/`..`/`~`）")
        else:
            abs_path = os.path.join(src_root, rel)
            if not os.path.isfile(abs_path):
                errs.append(f"{loc}: FILE '{rel}' 不存在"
                            f"（基准 = git 顶层 {src_root}；若报告是按子目录基准写的，"
                            f"每条 FILE 都要带该子目录前缀）")

        # 5. LINES
        spans = _parse_spans(f["lines"])
        if spans is None:
            errs.append(f"{loc}: LINES '{f['lines']}' 格式应为 N、A-B，"
                        f"或逗号分隔的多个 span")
        elif os.path.isfile(os.path.join(src_root, rel)):
            total = _count_lines(os.path.join(src_root, rel))
            if total is not None:
                for a, b in spans:
                    if b > total:
                        errs.append(f"{loc}: LINES {a}-{b} 超出 {rel} 实际行数 {total}")

        # 6. provenance：fixed 必须有祖先 commit
        #    唯一豁免 = 报告显式声明 `**Provenance:** baseline-rewritten`（历史被重写）。
        #    豁免不静默：结束时打印 NOTE，且仍要求 COMMIT 字段存在。
        if f["status"] == "fixed":
            if not f["commit"]:
                errs.append(f"{loc}: STATUS=fixed 必须有 COMMIT=<修复提交>")
            elif not baseline_rewritten and not _is_ancestor(f["commit"]):
                errs.append(f"{loc}: COMMIT={f['commit']} 不是 HEAD 的祖先"
                            f"（历史被重写或 commit 不存在）—— 若确认历史被重写，"
                            f"在报告里加一行 `**Provenance:** baseline-rewritten` 并重新建立基线")

    # 7. Coverage 段
    if not _has_coverage_section(lines):
        errs.append("报告缺少非空的 `## Coverage` 段 —— "
                    "必须交代看了哪些面、哪些面未审计及原因（覆盖率不是口号）")

    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    if errs:
        print(f"FAIL: {len(errs)} 个问题（{path}）", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {len(findings)} findings 契约通过（{path}）"
          f"{'' if _have_git() else ' [非 git 仓库：已跳过 COMMIT 祖先校验]'}")
    if baseline_rewritten:
        print("NOTE: 报告声明 `**Provenance:** baseline-rewritten` —— "
              "已跳过 COMMIT 祖先校验；基线需重新建立（见 reaudit-modes.md Mode 1）")


def cmd_mark(args, status_field, add_commit=True):
    path = resolve_report(args.report)
    findings, lines = load_report(path)
    by_id = {f["id"]: f for f in findings}
    missing = [i for i in args.ids if i not in by_id]
    if missing:
        sys.exit(f"找不到 ID: {', '.join(missing)}。现有: {', '.join(sorted(by_id))}")
    commit = getattr(args, "commit", None) or _git_head()
    # --reason（mark-deferred 用）：写成 REASON="..." 注解字段，避免"延期原因无处可存"
    reason = (getattr(args, "reason", None) or "").strip().replace('"', "'")
    changed = []
    for i in args.ids:
        f = by_id[i]
        if f["verdict"] == "rejected":
            sys.exit(f"{i} 的 VERDICT=rejected —— 已推翻的候选不进修复队列"
                     f"（要改认识态请手工编辑注解）")
        if f["status"] == status_field:
            print(f"{i} 已是 {status_field}"); continue
        updated = dict(f)
        updated["status"] = status_field
        if add_commit and commit:
            updated["commit"] = commit
        if reason:
            updated["reason"] = reason
        lines[f["line"]] = re.sub(r"<!--.*?-->", render_annot(updated),
                                  lines[f["line"]], flags=re.S)
        changed.append((i, f["status"], status_field, commit, reason))
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    for i, old, new, cmt, rsn in changed:
        c = f" (commit {cmt})" if cmt else ""
        r = f' [reason: "{rsn}"]' if rsn else ""
        print(f"{i}: {old or '—'} → {new}{c}{r}")
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

    l = sub.add_parser("list", parents=[common], help="列出 findings（可按状态/严重度/认识态过滤）")
    l.add_argument("--status"); l.add_argument("--severity"); l.add_argument("--verdict")
    l.add_argument("--json", action="store_true")

    s = sub.add_parser("status", parents=[common], help="认识态 + 修复进度汇总")

    v = sub.add_parser("validate", parents=[common],
                       help="校验注解契约（VERDICT/SEVERITY 互斥、FILE 存在、LINES 合法、"
                            "fixed 的 COMMIT 是 HEAD 祖先、报告含 ## Coverage）")

    d = sub.add_parser("diff-filter", parents=[common], help="git diff 变更文件 → 涉及 findings")
    d.add_argument("--commit", required=True, help="上次审计 commit hash")

    mf = sub.add_parser("mark-fixed", parents=[common], help="标记为已修复（改注解行，默认取当前 HEAD）")
    mf.add_argument("ids", nargs="+"); mf.add_argument("--commit")

    md = sub.add_parser("mark-deferred", parents=[common], help="标记为结构性延期")
    md.add_argument("ids", nargs="+"); md.add_argument("--reason", help="延期原因（写入注解）")

    args = p.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "validate":
        cmd_validate(args)
    elif args.cmd == "diff-filter":
        cmd_diff_filter(args)
    elif args.cmd == "mark-fixed":
        cmd_mark_fixed(args)
    elif args.cmd == "mark-deferred":
        cmd_mark_deferred(args)


if __name__ == "__main__":
    main()
