# /reaudit — 已合并

**状态：已归档，不再注册。**

2026-09-12 合并进 `code-security-audit`。

## 为什么合并

`reaudit` 是 `code-security-audit` 的 **Phase 4** 加三个轻量状态操作（mark-fixed /
mark-deferred / status）。它与 `code-security-audit` 的触发词重叠是实测最高的一对
（Jaccard 0.15，共享「再审计」「verify fixes」）——两个技能都声称能处理「再审计」，
于是同一个请求可能命中重量级的完整四阶段审计，而不是这个只跑 Phase 4 的快捷入口。

## 现在用什么

- `/reaudit` 与 `/reaudit mark-fixed|mark-deferred|status` → **仍可用**，
  现在是 `code-security-audit` 内的模式
- 完整操作说明（四种模式逐步、祖先性检查、diff-filter 的 FILE 基准约定、
  `security-audit-tools` 用法）已完整保留在
  `plugins/code-security-skills/skills/code-security-audit/references/reaudit-modes.md`
- 状态追踪脚本：仓库根 `bin/security_audit_tools.py`（`security-audit-tools` 控制台命令）

## 合并时顺带修掉的问题

1. **无祖先性检查**：`git diff <audit-commit>..HEAD` 在 commit 被 rebase 掉后会成功返回
   一堆无关文件（本仓库实测返回 151 个路径），静默产生错误的重审范围。现在 Mode 1 第 2 步
   强制 `git merge-base --is-ancestor` 检查，失败则声明历史已重写并重新建立基线。
2. **FILE 基准未定义**：匹配是字面集合成员判断，而文档没规定相对谁。现在规范为
   「仓库根相对 POSIX 路径」，并要求子目录审计时逐条带前缀，且 HEAD 处不存在的 FILE
   按已变更处理。
3. **Mode 1 缺路径校验**：`/reaudit` 这条实际入口此前只说"读取标注位置的文件"，
   没有「先确认 FILE 落在项目根内」的校验（该修复在别处已做，这里漏了）。已补进
   Mode 1 第 4 步。
4. **状态词汇不统一**：原 Mode 4 的输出示例只列 fixed/open/deferred，会让
   `partial` / `not-fixed` 被静默吞掉。现在要求逐条列出。
