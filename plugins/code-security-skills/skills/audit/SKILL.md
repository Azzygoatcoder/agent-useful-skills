---
name: audit
description: Use when the user types /audit. Quick entry to the full code security audit flow. Triggers ONLY on the exact slash command "/audit" — for natural language phrases like "security audit" or "安全审计", the code-security-audit skill handles those.
---

# /audit — Full Security Audit

Shortcut slash command. Immediately load and follow `code-security-audit` (Phase 1 through 3):

1. Launch 3 parallel exploration subagents (secrets, injection, auth/crypto/deps)
   — Claude Code: Explore agents; DeepSeek Harness: `subagent` tool（同一条消息内并发）
2. Verify findings, filter false positives, assign severity
3. Write structured report to `docs/SECURITY_AUDIT.md`

Read `code-security-audit/SKILL.md` for the full workflow. Do not skip phases.

## 自进化日志

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-09-12 | DSH 适配审计 | 把写死的 "Explore agents" 改为跨运行时表述（Claude Code Explore agents / DSH `subagent`），避免在 DSH 上找不到对应工具 |
