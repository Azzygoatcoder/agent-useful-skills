# /audit — 已合并

**状态：已归档，不再注册。**

2026-09-12 合并进 `code-security-audit`。

## 为什么合并

`/audit` 原本只是一个 15 行的前言，内容是「立即去读 `code-security-audit`，跑 Phase 1-3」。
它自己没有任何独立流程，却和 `code-security-audit`、`reaudit` 共享「安全审计」这一触发词
（实测两两触发词重叠 Jaccard 0.09），让「安全审计」类请求有机会命中一个只会转发的空壳。

审计与重审本来就是同一条工作流的两段，拆成同级技能只增加「我该调哪个」的决策成本，
不增加能力。

## 现在用什么

- `/audit` → **仍可用**，但它现在是 `code-security-audit` 内的一个模式
  （见该技能的场景判定表与 Slash Commands 表）
- 完整审计 → `code-security-audit`（Phase 1-3）
- 增量重审 / 状态追踪 → `code-security-audit` Phase 4，
  展开见 `plugins/code-security-skills/skills/code-security-audit/references/reaudit-modes.md`
