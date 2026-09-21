# Code Security Audit — Report Templates

> 被 `SKILL.md`（code-security-audit）引用。Phase 3 用「审计报告模板」；增量重审（Phase 4）用「Re-Audit 段模板」。按需取用，不必整段背下来。

## 审计报告模板（Phase 3 使用）

```
# [Project Name] Security Audit Report

**Date:** [date]
**Audit commit:** [git rev-parse HEAD]
**Scope:** [what was reviewed]
**Methodology:** Three parallel reviews covering (1) secrets & credentials,
  (2) input validation & injection, (3) authentication, cryptography & dependencies
[仅当基线 commit 已不可达（历史被重写）时加这一行，别的情况不要加：]
**Provenance:** baseline-rewritten — [原基线 hash] 不在 HEAD 祖先链上，fixed 结论未在当前 HEAD 重验

## Executive Summary
One paragraph: total findings by severity, most critical issues, overall risk posture.

## Risk Distribution
Table: | Severity | Count | Finding IDs |

## Coverage   ← 必填且不得为空（`validate` 会检查这一节存在且有内容）
本轮审计了哪些面、用了哪些攻击类、结果如何，以及**哪些面未审计及原因**：

| 面 | 检查的攻击类 | 结果 |
|----|-------------|------|
| src/api/ | injection, access control | 覆盖 |
| deploy/ | IaC, secrets | **未审计** —— 本轮无 K8s 清单 |

**单次运行 ≠ 完整覆盖。** 只声明上表所列范围，不写"仓库已安全"。

## Critical Findings
One subsection per finding:

### SSRF-1 — [title]
<!-- AUDIT:VERDICT=confirmed STATUS=open SEVERITY=critical FILE=path/to/file.py LINES=123-145 -->

- **Finding:** title
- **Severity:** Critical
- **File:** path (line numbers)
- **Description:** what and why it matters
- **Vulnerable code:** fenced code block
- **Remediation:** concrete fix with corrected code

## High Findings
[Same format with category-prefixed IDs]

## Medium Findings
[Same format with category-prefixed IDs]

## Low Findings
[Same format with category-prefixed IDs]

## Needs Validation   ← 只有存在这类 finding 时才写这一节
源码路径成立、但卡在**仓库外的事实**上的候选。**不得给严重度**（`validate` 会拦下），
且必须写清缺的是什么、怎么解：

### PROMPT-1 — [title]
<!-- AUDIT:VERDICT=needs-validation STATUS=open FILE=src/rag.py LINES=88-104 BLOCKER="线上是否启用工具调用未知" -->

- **声称的根因:** 一句话
- **源码路径:** file:line → file:line
- **缺的事实:** 一句话（就是 `BLOCKER`）
- **有界本地验证:** 用 dummy 数据能怎么验
- **owner 可观测检查:** 让属主看哪个配置 / 路由 / 策略

> 被推翻的候选写 `VERDICT=rejected` 并保留在报告里（附 `REASON=`），以免下轮重打同一枪；
> 但**不得写成 finding**、不得给严重度、不进修复队列。

## Cross-Cutting Recommendations
Themes spanning multiple findings.

## Remediation Priority Matrix
Table: | ID | Finding | Effort | Impact | Priority (P1-P4) |

## Appendix
Commit hash, verification guidance per finding.
```

## Re-Audit 段模板（Phase 4 使用，加在报告顶部）

```
## Re-Audit ([date])

**Diff range:** <audit-commit>..<current-commit>
**Files changed:** N

### Status Summary
Table: | Status | Count |
       | fixed | N |
       | not-fixed | N |
       | partial | N |
       | deferred | N |
       | unchanged | N |

### Fixed (N of total)
Table: | ID | Finding | Fix Verified At |

### Not Fixed (N of total)
Table: | ID | Finding | Status/reason |

### Partially Fixed (N of total)
Table: | ID | Finding | What's done vs. remaining |

### 未重验，沿用旧结论（N of total）   ← 必填
"文件没变所以跳过"必须**逐条列出**，不能只报一个数字 —— 静默沿用旧结论是漏报来源：
- 修复可能落在**别的文件**（例如共享工具里加了 guard），此时本条 finding 的 `FILE` 没变，
  但结论已经过时，`fixed` 会永远认不出来；
- 长期 `open` 的 finding 会一直 stale，而报告里看不出来。

Table: | ID | Finding | STATUS | 为什么跳过 |

### New Findings
Any issues introduced by the fixes.

### Verdict
One paragraph summary.
```