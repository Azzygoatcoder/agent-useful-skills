---
name: code-security-audit
description: Use when the user wants to audit a codebase for security vulnerabilities, run a 代码审计 or 安全审查, do penetration testing, or verify that security fixes were applied. Triggers on "audit this repo", "security review", "find vulnerabilities", "安全审计", "代码审计", "安全扫描", "再审计", "检查修复", "确认修复", "re-audit", "verify fixes", "/audit", "/reaudit". Covers full audit (Phase 1-3) plus incremental re-audit and fix-state tracking (Phase 4). To APPLY fixes use security-fix-skill.
---

# Code Security Audit

## Overview

Systematic security audit of any codebase using parallel domain exploration. Launch independent review agents across three security domains simultaneously, then synthesize findings into a structured audit report with severity ratings and concrete remediation steps.

**Core principle:** Coverage through parallelization. Three focused agents catch more than one broad agent — each domain has different grep patterns, different mental models, and different blind spots.

## 场景判定（先定深度，再走流程）

| 场景 | 触发 | 深度 | 产出 | 流程 |
|------|------|:--:|------|------|
| 快速风险扫描 | "快扫一眼" / "/audit quick" | L1 | 一页风险概览（不看全文） | Phase 1 单 agent + 摘要，跳过 Self-Check |
| **全面审计（默认）** | "audit this repo" / "安全审计" / "/audit" | L2-L3 | 完整 SECURITY_AUDIT.md | Phase 1-3 全流程 |
| 增量重审 | "再审计" / "检查修复" / "/reaudit" | 变更文件 | 重审段 + 状态更新 | Phase 4 |
| 状态追踪 | "/reaudit status" / "mark-fixed \<ID\>" | — | 状态汇总 / 注解更新 | 状态追踪（不读文件） |
| 快速修复 | "修漏洞" / "/security-fix" | — | 按 P1-P4 批量修复 | 走 security-fix 技能 |
| 单 PR / 单文件 | "review this PR" / "看下这个改动" | — | 代码评审 | 走 `dev-workflow`（自带代码评审清单），不进安全审计 |

> 默认是**全面审计**。用户要求"快扫/quick"才降级 L1；"修漏洞"走 security-fix、"再审计/检查修复"走 Phase 4。场景不清时按全面审计走，深度宁高勿低。

## Slash Commands / Modes

| Command | Action | Reads files? |
|---------|--------|-------------|
| `/audit` | 全面审计 — explore → verify → report (Phase 1–3) | 是 |
| `/reaudit` | 增量重审，验证先前 finding 是否已修复 (Phase 4) | 仅变更文件 |
| `/reaudit mark-fixed <ID>` | 标记为已修复（只改状态注解，不读文件） | 否 |
| `/reaudit mark-deferred <ID> [--reason "文本"]` | 标记为结构性延期 | 否 |
| `/reaudit status` | 认识态 + 修复进度汇总（按注解统计） | 否 |
| `/reaudit validate` | 注解契约校验（与 CI 门禁同款） | 否 |
| `/code-security-audit` | 同 `/audit`（规范名） | 是 |

> `/audit` 与 `/reaudit` 的入口说明见 [references/reaudit-modes.md](references/reaudit-modes.md)（含各模式逐步操作、报告路径探测、退出码约定）。

## When to Use

Trigger when the user asks to:
- Audit a repository or codebase for security issues
- Perform a security review or vulnerability assessment
- Check if security fixes were properly applied (re-audit)
- Find vulnerabilities before a release or deployment

Do NOT use for:
- Reviewing a single PR diff (use `dev-workflow`)
- Checking one specific function for bugs (use systematic-debugging)
- General code review for style/architecture (use `dev-workflow`, which ships its own code-review checklist)

## Audit Workflow

Full per-phase protocol: [references/audit-workflow.md](references/audit-workflow.md)

**Required before Phase 1:**
1. Read `references/vulnerability-patterns.md`
2. Run `git rev-parse HEAD` and record the audit commit
3. Probe the project language/framework
4. Check for a prior `docs/SECURITY_AUDIT.md` report

**Phase summary:**
- **Phase 1 — Parallel Exploration:** launch 3 domain agents (secrets, injection, auth/crypto/deps)；L2/L3 另加 **Agent D**（业务逻辑 / 功能滥用 / 链式信任边界 / Wildcard）；并行失败时回退到单个综合 agent。
- **Phase 2 — Deep-Dive Verification:** 先过 `vulnerability-patterns.md` 的「不算 Finding 判别表」，读回被标记的代码，去重，跑 5 点 Self-Check；**Critical/High 由没参与该条发现的新 agent 回读源码复核**（可再叠加 review.py 跨模型对抗）；最后定严重度、稳定前缀 ID 与 `VERDICT`。
- **Phase 3 — Report Compilation:** write the report with `references/audit-report-template.md`；**必须含非空 `## Coverage` 段**；every finding carries `<!-- AUDIT:... -->` annotations.
- **Phase 4 — Re-Audit:** parse annotations, diff-filter to changed files, verify each changed finding, update status and commit.

## Vulnerable Patterns Reference

Grep patterns and remediation templates per category live in `references/vulnerability-patterns.md` — read it before Phase 2 (Pre-Flight requires it). **它的「不算 Finding 判别表」是 Phase 2 的第一道闸**：先过表，再谈严重度。

`references/attack-surfaces.md` 覆盖另外 5 个面（AI/LLM、供应链/CI、桌面/本地 IPC、资源耗尽、数据隔离）—— 主流程三域不查这些。**按需懒加载**：只在侦察发现对应边界时才读那一段，不要一次性读全文。

**认识态（`VERDICT`）不是修复态（`STATUS`）** —— 两者正交，见 `references/vulnerability-patterns.md` §18：

| VERDICT | 何时用 | 严重度 |
|---------|--------|:--:|
| `confirmed`（缺省） | 源码证据 + 有界本地验证齐全 | ✅ 必填 |
| `needs-validation` | 源码路径成立，但卡在仓库外的事实上（写 `BLOCKER=`） | ❌ 禁止 |
| `rejected` | 已被推翻的候选（写 `REASON=`，留档以免下轮重打） | ❌ 禁止 |

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
- **Do NOT 给 `needs-validation` / `rejected` 定严重度。** 不确定就不许定级 —— 把"证据不足的严重问题"降级成"证据充分的轻微问题"，是审计里最贵的错误。
- **Do NOT 丢掉 `rejected` 记录。** 留档（附 `REASON=`）才能让下一轮不重打同一枪。
- **Do NOT 让发现者复核自己。** Critical/High 必须由一个**没参与该条发现**的新 agent 回读源码复核。
- **Do NOT 省略 `## Coverage` 段。** 没交代"哪些面没审计"，报告就是在暗示完整覆盖。

## Critical Reminders — read before every audit phase

These rules are NON-NEGOTIABLE and take precedence over all other considerations:

1. **Gate before code**: Pre-Flight checks are unconditional. Never touch a file before they complete.
2. **Verify before reporting**: Every finding passes the 5-point Self-Check. Fail any check → not a finding.
3. **Two methods for severity**: Critical/High cannot rest on a single grep hit. Independent confirmation or downgrade.
4. **Rationalization = escalation**: "probably fine" / "won't reach this code" / "obvious fix" → STOP and re-verify.
5. **Confidence is reported, not filtered**: Low-confidence findings enter Phase 2. Phase 2 decides, not Phase 1.
6. **Stable IDs always**: Category-prefixed, sequential within prefix. Never shift existing IDs in re-audits.
7. **不确定不许定级**: `needs-validation` / `rejected` 不带 `SEVERITY` —— 只有 `confirmed` 配严重度。
8. **单次运行 ≠ 完整覆盖**: 报告只声明 `## Coverage` 表所列范围，不写"仓库已安全"。

## After the Audit

- **Report location:** Place the report at `docs/SECURITY_AUDIT.md` by default. Add it to `.gitignore` so it stays local.
- **Contract check:** 收工前跑 `python bin/security_audit_tools.py validate` —— 校验 `VERDICT`/`SEVERITY` 互斥、`FILE` 存在且是仓库根相对路径、`LINES` 不越界、`fixed` 的 `COMMIT` 是 HEAD 祖先、`## Coverage` 段非空。
- **Follow-up:** Offer to fix the highest-priority findings (P1 items)。`VERDICT=confirmed` 的才进修复队列。
- **Pattern collection:** After the audit, review `references/vulnerability-patterns.md`. Add any new patterns you discovered **以及它的排除条件**（`不算 Finding 判别表`里补一行）—— 没有排除条件的模式是误报来源。This is how the skill evolves.

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
| 2026-09-12 | **技能合并（27→18 之后的第二轮瘦身）** | `audit` 与 `reaudit` 合并回本技能：`audit` 只是 15 行前言（"去读 code-security-audit"），无独立流程却共享「安全审计」触发词；`reaudit` 是本技能 Phase 4 加三个状态操作，与本技能触发词重叠实测最高（Jaccard 0.15，共享「再审计」「verify fixes」）——同一请求可能命中重量级完整审计而非 Phase 4 快捷入口。两者已归档到 archive/（附合并说明与原件）。Phase 4 完整操作外移 references/reaudit-modes.md，并顺带补上：祖先性检查（audit commit 被 rebase 后 `git diff` 会返回一堆无关文件——本仓库实测 151 个路径）、FILE 的仓库根相对基准约定、Mode 1 的路径校验、status 输出不得吞掉 partial/not-fixed |
| 2026-09-20 | 对标 `cloudflare/security-audit-skill`（**轻量升级：只取认识论，不取工程学**） | ①注解加 `VERDICT`（`confirmed`/`needs-validation`/`rejected`，**缺省 confirmed ⇒ 旧报告零改动兼容**）—— 认识态与修复态拆成两条正交轴，`deferred` 不再兼背"测不出来"；**不确定就不许定级**，`rejected` 留档以免下轮重打。②`security_audit_tools.py validate` 七条真检查接 CI；给"历史被重写"留**唯一显式豁免** `**Provenance:** baseline-rewritten`。③「不算 Finding 判别表」17 行 + 4 条全局规则 —— 直击 30-40% 误报，且不用新增任何域文件。④报告模板加必填 `## Coverage` + `## Needs Validation` 段与「未重验」表。⑤Phase 2 独立性硬化为"发现者不得复核自己"（Critical/High 换新 agent 回读源码 + review.py 喂 finding+源码而非散文草稿）。⑥Phase 4 修两个洞（修复落在别的文件时 `fixed` 认不出、静默沿用旧结论）+ prior-run 纪律。⑦新增 `attack-surfaces.md`（5 个空白面，懒加载、不并入主流程三域）与 Agent D（业务逻辑/功能滥用/链式信任边界/Wildcard）。**明确未采纳**：`findings.json` + JSON Schema + 两个 30KB 校验器（132KB）、覆盖率账本 JSON 与 canonical coverage_id、11 步 artifact promotion、OS 沙箱前置 —— 那套是给"全公司舰队 + 不受信目标代码"设计的，搬过来是大炮打蚊子。**实证**：validate 上线当天在本仓库自己身上抓出 3 个真问题（SECRET-3 因 `LINES=475,510` 被旧正则静默丢弃、报告 `FILE` 是子目录基准会让 diff-filter 静默漏判、PATH-2 行号随 SKILL.md 瘦身失效） |
| 2026-09-21 | **重验轮：让独立 agent 复核我自己刚写的代码** | ①「发现者不得复核自己」当场兑现 —— **我自己做的重验把两条「半修」判成了「已修」**（PATH-2 只在 `reaudit-modes` 写了格式约定、agent 的读取路径上并无包含性指令；DEP-1 点名两个文件而我只核了一个），换独立 agent 重扫同一批文件，立刻报出 **5 条新问题 + 2 条纠正**。教训入档：**只核对注解里那一个 `FILE`/`LINES`，会漏掉「同一句话在别处还有一份」—— 多文件 finding 必须逐个文件核。** ②新报 5 条全部带可执行证据：`META-2` 解析不了的注解让该 finding **整条跳过全部逐条检查**却仍打印 `PASS`（**门禁退化成摆设**，P1）；`PATH-3` 路径围栏只 append 错误、读却照做（越界读出仓库外文件行数）；`CMD-1` `--commit=--output=…` 的 git 选项注入（写文件 + diff-filter 静默返回「0 个变更」）；`RES-1` `LINES` 无位数上界（py3.11+ 抛异常把门禁搞崩、py3.9 二次方）；`META-3` prose 声明了 `validate` 并不提供的保证。③`validate` 由 7 条检查变 **8 条**：新增**标题↔注解对账**并置于所有逐条检查**之前** —— 没有它，其余检查都能靠「让注解解析不了」整条绕过。④回归测试补 8 条，其中 PATH-3 用**成对**用例（陷阱 + 对照）避免空转，因为复核指出原测试只断言报错文案、从不断言「文件没被读」。⑤**有价值的否定结果同样入档**：排除 10 类候选（`COMMIT=` 注入 git 本就 fail-closed、`FILE=` 词法逃逸不可达、CI 步骤退出码传播是对的）—— 免得下一轮重打。⑥顺带修 `export_diagram.py` 的 PNG 导出在 Windows 上恒失败（`shutil.which` 返回 `…rsvg-convert.EXE`，`endswith("rsvg-convert")` 为假）。 |
