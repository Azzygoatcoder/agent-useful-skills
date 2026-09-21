"""Offline self-test for bin/review.py's truncation contract, and for
bin/security_audit_tools.py's annotation contract.

review.py: stubs the LLM call so no network/key is needed. Asserts:
  - untruncated input  -> exit 0, payload["truncated"] is False
  - truncated input    -> exit 3, payload carries original/reviewed/max chars
  - the verdict object is preserved under the wrapper

security_audit_tools.py:
  - mark-deferred --reason round-trips, and `list` surfaces it
  - `validate`: VERDICT/SEVERITY 互斥、BLOCKER/REASON 必填、FILE 必须是安全的
    仓库根相对路径且存在、LINES 不越界（含逗号 span）、表外 ID 前缀、
    `fixed` 必须有 COMMIT、`## Coverage` 段非空
  - 旧注解（无 VERDICT）缺省为 confirmed —— 向后兼容

Run: python tests/test_bin_contracts.py
"""
from __future__ import annotations

import importlib
import io
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))

# 输出含中文：Windows 上 stdout 默认 cp1252，不重配置会 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

failures = []


def check(label, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + label + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def run_review(text, max_chars):
    """Import review fresh with a stubbed llm, run main(), return (exit_code, payload)."""
    os.environ["MAX_INPUT_CHARS"] = str(max_chars)
    for mod in ("llm", "review"):
        sys.modules.pop(mod, None)
    llm = importlib.import_module("llm")
    llm.chat_json = lambda model, messages, **kw: {
        "score": 7, "verdict": "ALMOST", "strongest_objection": "stub",
        "minimal_fix": "stub", "other_weaknesses": [],
    }
    sys.modules["llm"] = llm
    review = importlib.import_module("review")
    review.llm = llm

    sys.argv = ["review.py", text, "--json"]
    buf, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = buf, err
    code = 0
    try:
        review.main()
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, buf.getvalue(), err.getvalue()


print("review.py truncation contract")
code, out, _ = run_review("short text", 120000)
try:
    payload = json.loads(out)
    check("untruncated -> exit 0", code in (0, None), f"exit={code}")
    check("untruncated -> truncated=False", payload["truncated"] is False)
    check("untruncated -> verdict preserved", payload["verdict"]["score"] == 7)
except Exception as exc:  # noqa: BLE001
    check("untruncated -> valid JSON", False, repr(exc))

code, out, err = run_review("A" * 900, 200)
try:
    payload = json.loads(out)
    check("truncated -> exit 3", code == 3, f"exit={code}")
    check("truncated -> truncated=True", payload["truncated"] is True)
    check("truncated -> original_chars=900", payload["original_chars"] == 900,
          str(payload["original_chars"]))
    check("truncated -> max_input_chars surfaced", payload["max_input_chars"] == 200)
    check("truncated -> stderr warning", "截断" in err)
except Exception as exc:  # noqa: BLE001
    check("truncated -> valid JSON", False, repr(exc))

print("security_audit_tools.py --reason round-trip")
import tempfile  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="aus-audit-"))
report = tmp / "SECURITY_AUDIT.md"
report.write_text(
    "## High Findings\n\n"
    "### SSRF-1 — fetch navigates to unvalidated URL\n"
    "<!-- AUDIT:STATUS=open SEVERITY=high FILE=src/fetch.py LINES=10-20 -->\n",
    encoding="utf-8")

sys.modules.pop("security_audit_tools", None)
sat = importlib.import_module("security_audit_tools")


def run_sat(argv):
    sys.argv = ["x"] + argv
    buf, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = buf, err
    code = 0
    try:
        sat.main()
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, buf.getvalue(), err.getvalue()


reason = "需要上游库先修 TLS 默认值"
code, out, _ = run_sat(["mark-deferred", "SSRF-1", "--reason", reason, "--report", str(report)])
check("mark-deferred -> exit 0", code in (0, None), f"exit={code}")
findings, _ = sat.load_report(str(report))
f = next((x for x in findings if x["id"] == "SSRF-1"), None)
check("status persisted as deferred", f is not None and f["status"] == "deferred")
check("--reason persisted (not dropped)", f is not None and f.get("reason") == reason,
      repr(f.get("reason") if f else None))
code, out, _ = run_sat(["list", "--report", str(report)])
check("list surfaces the reason", "原因" in out and reason in out)

print("security_audit_tools.py validate 契约")

vtmp = pathlib.Path(tempfile.mkdtemp(prefix="aus-validate-"))
COV = "## Coverage\n\n| 面 | 类 | 结果 |\n|---|---|---|\n| bin/ | injection | 覆盖 |\n\n"
TARGET = "bin/security_audit_tools.py"  # 存在，且是仓库根相对路径


def mk(name, findings_md, with_coverage=True):
    p = vtmp / name
    p.write_text("# T\n\n" + (COV if with_coverage else "") + findings_md, encoding="utf-8")
    return p


def ent(heading, annot):
    return f"### {heading}\n{annot}\n\n"


# 好报告：PATH-1 无 VERDICT（旧格式，应缺省 confirmed）+ PROMPT-1 带逗号 span
good = mk("good.md",
          ent("PATH-1 — x", f"<!-- AUDIT:STATUS=open SEVERITY=low FILE={TARGET} LINES=1-5 -->")
          + ent("PROMPT-1 — y",
                f'<!-- AUDIT:VERDICT=needs-validation STATUS=open FILE={TARGET} '
                f'LINES=10,20 BLOCKER="线上配置未知" -->'))
code, out, err = run_sat(["validate", "--report", str(good)])
check("好报告 -> exit 0", code == 0, f"exit={code} err={err.strip()[:200]}")
check("好报告 -> PASS", "PASS" in out, out.strip()[:120])
check("两条 finding 都被数到（含逗号 span）", "2 findings" in out, out.strip()[:120])

# 缺 VERDICT 的旧注解 -> 认识态缺省 confirmed（向后兼容）
old_findings, _ = sat.load_report(str(good))
check("旧注解缺省 VERDICT=confirmed",
      next(f for f in old_findings if f["id"] == "PATH-1")["verdict"] == "confirmed")

cases = [
    ("needs-validation 带 SEVERITY",
     mk("sev.md", ent("PROMPT-2 — z",
                      f'<!-- AUDIT:VERDICT=needs-validation STATUS=open SEVERITY=high '
                      f'FILE={TARGET} LINES=1-5 BLOCKER="x" -->')),
     "不得带 SEVERITY"),
    ("needs-validation 缺 BLOCKER",
     mk("blk.md", ent("PROMPT-3 — z",
                      f"<!-- AUDIT:VERDICT=needs-validation STATUS=open FILE={TARGET} LINES=1-5 -->")),
     "必须有 BLOCKER"),
    ("rejected 缺 REASON",
     mk("rej.md", ent("XSS-9 — z", f"<!-- AUDIT:VERDICT=rejected FILE={TARGET} LINES=1-5 -->")),
     "必须有 REASON"),
    ("FILE 是穿越路径",
     mk("trav.md", ent("PATH-9 — z",
                       "<!-- AUDIT:STATUS=open SEVERITY=low FILE=../../etc/passwd LINES=1-5 -->")),
     "不是安全的仓库根相对"),
    ("LINES 超出文件行数",
     mk("lines.md", ent("DEP-9 — z",
                        f"<!-- AUDIT:STATUS=open SEVERITY=low FILE={TARGET} LINES=1-999999 -->")),
     "超出"),
    ("fixed 缺 COMMIT",
     mk("nocommit.md", ent("CMD-9 — z",
                           f"<!-- AUDIT:STATUS=fixed SEVERITY=low FILE={TARGET} LINES=1-5 -->")),
     "必须有 COMMIT"),
    ("表外 ID 前缀",
     mk("prefix.md", ent("FOO-1 — z",
                         f"<!-- AUDIT:STATUS=open SEVERITY=low FILE={TARGET} LINES=1-5 -->")),
     "不在 ID 前缀表内"),
    ("缺 ## Coverage 段",
     mk("nocov.md", ent("BAR-1 — z",
                        f"<!-- AUDIT:STATUS=open SEVERITY=low FILE={TARGET} LINES=1-5 -->"),
        with_coverage=False),
     "## Coverage"),
]

for label, path, expect in cases:
    code, out, err = run_sat(["validate", "--report", str(path)])
    ok = code == 1 and expect in err
    check(f"{label} -> exit 1 且报错", ok,
          f"exit={code} err={err.strip().splitlines()[-1][:140] if err.strip() else '(空)'}")

print()
if failures:
    print(f"{len(failures)} FAILED: {', '.join(failures)}")
    sys.exit(1)
print("all bin contract checks passed")
