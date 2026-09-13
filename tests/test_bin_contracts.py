"""Offline self-test for bin/review.py's truncation contract.

Stubs the LLM call so no network/key is needed. Asserts:
  - untruncated input  -> exit 0, payload["truncated"] is False
  - truncated input    -> exit 3, payload carries original/reviewed/max chars
  - the verdict object is preserved under the wrapper

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

print()
if failures:
    print(f"{len(failures)} FAILED: {', '.join(failures)}")
    sys.exit(1)
print("all bin contract checks passed")
