---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## 场景判定（先定轻重，再定流程）

| 场景 | 力度 |
|------|------|
| 生产环境、正式项目、共享代码、反复出现的 bug | **完整四阶段**：根因 → 模式 → 假设验证 → 实施 |
| 个人业余项目、低风险探索、一次性脚本 | **轻量调试**：至少做到「稳定复现 → 定位根因 → 验证修复」；不需要形式上把四阶段全走一遍 |
| 纯 throwaway / 临时现象 | 可不深挖，但不要把这个修复当作“已验证”提交 |

> 判断标准：**这个 bug 会浪费别人/后续/生产多少时间？** 低风险就快走，高成本就按完整流程。完整流程不是仪式，是“这个错误值得花时间”时的护城河。

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

完整四阶段、Red Flags、Common Rationalizations 和 Supporting Techniques 见 [references/debugging-guide.md](references/debugging-guide.md)。

## 轻量路径（个人/低风险项目）

1. **先复现**：能不能稳定触发？不能，先补数据/日志，别猜。
2. **定位根因**：读错误信息、看最近改动、追到数据源头。至少确定“是哪里错了”，而不是“哪里看起来像错”。
3. **最小修复**：一次只改一个变量，验证修复是否生效。
4. **验收**：确认问题消失；如果影响真实使用，补一个最小回归测试。

## Red Flags（速记）

- 还没定位根因就开始改
- “先快速修一下，之后再查”
- 一次改多个地方
- 3 次以上修复失败还在继续

遇到这些，STOP 回到根因调查。

## Supporting Techniques

- **`root-cause-tracing.md`** — Trace bugs backward through call stack to find original trigger
- **`defense-in-depth.md`** — Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** — Replace arbitrary timeouts with condition polling

完整展开见 [references/debugging-guide.md](references/debugging-guide.md)。
