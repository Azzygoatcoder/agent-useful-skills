---
name: code-security-audit
description: Use when the user wants to audit a codebase for security vulnerabilities, perform a security review, do penetration testing, run a 代码审计 or 安全审查, check for security issues, or verify that security fixes have been applied. Triggers on phrases like "audit this repo", "security review", "find vulnerabilities", "安全审计", "代码审计", "再审计", "verify fixes", "安全扫描".
---

# Code Security Audit

## Overview

Systematic security audit of any codebase using parallel domain exploration. Launch independent review agents across three security domains simultaneously, then synthesize findings into a structured audit report with severity ratings and concrete remediation steps.

**Core principle:** Coverage through parallelization. Three focused agents catch more than one broad agent — each domain has different grep patterns, different mental models, and different blind spots.

## 场景判定（先定深度，再走流程）

| 场景 | 触发 | 深度 | 产出 | 流程 |
|------|------|:--:|------|------|
| 快速风险扫描 | "/audit quick" / "快扫一眼" | L1 | 一页风险概览（不看全文） | Phase 1 单 agent + 摘要，跳过 Self-Check |
| **全面审计（默认）** | "audit this repo" / "安全审计" / "/audit" | L2-L3 | 完整 SECURITY_AUDIT.md | Phase 1-3 全流程 |
| 增量重审 | "/reaudit" / "检查修复" | 变更文件 | 重审段 + 状态更新 | Phase 4 |
| 单 PR / 单文件 | "review this PR" / "看下这个改动" | — | 代码评审 | 委托 code-review，不进安全审计 |
| 快速修复 | "/security-fix" / "修漏洞" | — | 按 P1-P4 批量修复 | security-fix-skill |

> 默认是**全面审计**。用户要求"快扫/quick"才降级 L1；"修漏洞/再审计"分别走 security-fix / reaudit。场景不清时按全面审计走，深度宁高勿低。

## Slash Commands

| Command | Action |
|---------|--------|
| `/audit` | Full security audit — explore → verify → report (Phase 1–3) |
| `/reaudit` | Verify previous audit fixes were applied (Phase 4) |
| `/reaudit mark-fixed <ID>` | Lightweight: mark a finding as fixed (update status annotation only, no file read) |
| `/reaudit mark-deferred <ID>` | Mark a finding as structurally deferred |
| `/reaudit status` | Show current fix progress (count by status from annotations) |
| `/code-security-audit` | Same as `/audit` (canonical name) |

## When to Use

Trigger when the user asks to:
- Audit a repository or codebase for security issues
- Perform a security review or vulnerability assessment
- Check if security fixes were properly applied (re-audit)
- Find vulnerabilities before a release or deployment

Do NOT use for:
- Reviewing a single PR diff (use `/security-review` or manual review)
- Checking one specific function for bugs (use systematic-debugging)
- General code review for style/architecture (use `/code-review`)

## Audit Workflow

Full per-phase protocol: [references/audit-workflow.md](references/audit-workflow.md)

**Required before Phase 1:**
1. Read `references/vulnerability-patterns.md`
2. Run `git rev-parse HEAD` and record the audit commit
3. Probe the project language/framework
4. Check for a prior `docs/SECURITY_AUDIT.md` report

**Phase summary:**
- **Phase 1 — Parallel Exploration:** launch 3 domain agents (secrets, injection, auth/crypto/deps); fallback to one comprehensive agent if parallel agents fail.
- **Phase 2 — Deep-Dive Verification:** read flagged code, filter false positives, deduplicate, run the 5-point Self-Check, optional cross-model adversarial review, assign severity and stable category-prefixed IDs.
- **Phase 3 — Report Compilation:** write the report with `references/audit-report-template.md`; every finding carries `<!-- AUDIT:STATUS=... -->` annotations.
- **Phase 4 — Re-Audit:** parse annotations, diff-filter to changed files, verify each changed finding, update status and commit.

## Vulnerable Patterns Reference

Grep patterns and remediation templates per category live in `references/vulnerability-patterns.md` — read it before Phase 2 (Pre-Flight requires it).

## Do NOT — Negative Heuristics

These actions are FORBIDDEN during an audit. They are the most common ways audits silently degrade:

- **Do NOT skip the Pre-Flight checks** even on a "quick scan." The gate is unconditional.
- **Do NOT accept an agent finding without reading the flagged code yourself.** Agents summarize; you verify.
- **Do NOT assign Critical or High severity from a single grep match.** Must be confirmed by a different method.
- **Do NOT suppress a finding because confidence is low.** That decision belongs to Phase 2, not Phase 1.
- **Do NOT close a finding because "it's probably fine."** See Meta-Cognition Trap.
- **Do NOT write the audit report before completing Phase 2 verification.** Phase 3 only after Phase 2.
- **Do NOT skip status annotations on findings.** Without `<!-- AUDIT:STATUS=... -->`, mark-fixed and incremental re-audit break.
- **Do NOT use sequential IDs (N1, N2...).** Use category-prefixed IDs (SSRF-1, PATH-1).

## Critical Reminders — read before every audit phase

These rules are NON-NEGOTIABLE and take precedence over all other considerations:

1. **Gate before code**: Pre-Flight checks are unconditional. Never touch a file before they complete.
2. **Verify before reporting**: Every finding passes the 5-point Self-Check. Fail any check → not a finding.
3. **Two methods for severity**: Critical/High cannot rest on a single grep hit. Independent confirmation or downgrade.
4. **Rationalization = escalation**: "probably fine" / "won't reach this code" / "obvious fix" → STOP and re-verify.
5. **Confidence is reported, not filtered**: Low-confidence findings enter Phase 2. Phase 2 decides, not Phase 1.
6. **Stable IDs always**: Category-prefixed, sequential within prefix. Never shift existing IDs in re-audits.

## After the Audit

- **Report location:** Place the report at `docs/SECURITY_AUDIT.md` by default. Add it to `.gitignore` so it stays local.
- **Follow-up:** Offer to fix the highest-priority findings (P1 items).
- **Pattern collection:** After the audit, review `references/vulnerability-patterns.md`. Add any new patterns you discovered. This is how the skill evolves.

## 自进化日志

每次审计实践吸收的模式记录于此，skill 随之进化：

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-06-14 | v1.0 初始 | 4 阶段审计 + 17 类漏洞模式 + 3 并行 agent |
| 2026-06-18 | v1.1 | 状态注解 + 稳定前缀 ID + 增量重审 + Phase 2 去重 |
| 2026-06-19 | 3 轮真实审计反馈 | 并行失败→单 agent 兜底；误报 30-40%→confidence 标注；Edit 摩擦→脚本化；增量没真跑过；新代码自动发现；依赖变更检查 |
| 2026-06-21 | v1.3 | FABLE-5 风格重写：Pre-Flight Gate、Confidence、Self-Check、Meta-Cognition Trap |
| 2026-08-12 | 对齐科研骨架新范式 | 场景判定表（快速/全面/增量/单 PR 四路分流）；review.py 跨模型对抗验证进 Phase 2；security-audit-tools.py 脚本化状态追踪 |
| 2026-08-12 | demo-caregiver-training 首审 | 小代码库（1474 行）直读全量等效并行探索；**review.py 对抗实际抓出 3 个问题**（PROMPT-1 严重度低估→升 High、AUTH/STATE 威胁模型自相矛盾、SECRET-1 是噪音→移建议区）——跨模型对抗验证价值实证；威胁模型必须先声明（本地 vs 暴露）再定级 |
| 2026-08-24 | P0 瘦身 | 报告模板（report + re-audit）外移 references/audit-report-template.md；Quick Reference 压缩为指针、Common Mistakes 并入 Do NOT（SKILL.md 466→约 300 行） |
