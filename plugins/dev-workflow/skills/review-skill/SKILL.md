---
name: review-skill
description: Use when the user wants GitHub PR review operations — read and comment on a PR, approve or request changes, or merge it. This is the operational GitHub flow (issue → PR → review → merge), not the general code-review methodology. To CREATE a PR use pr-skill; this skill starts once a PR URL/number exists. Triggers on "review 这个 PR", "看下这个 PR", "approve", "要求修改", "request changes", "merge", "合了", "/review".
---

# Review — GitHub PR Review 工作流

评审者动作：看 PR → 评审 → 提交 approve/changes → 合并。与 pr-skill（作者提 PR）相对。

## 角色

本 skill 是「评审者」的 = 有 merge 权限的 maintainer / owner。作者侧走 pr-skill。

## 第 0 步：能力与状态预检（别盲 merge）

```bash
gh pr view <N> --json author,reviewDecision,mergeable,statusCheckRollup
gh api repos/{owner}/{repo} --jq .permissions.push     # 无 push 权限 → 只能评审，不能合并
```

- 无 merge 权限 → 只提交评审意见，然后交回 pr-skill / maintainer
- 检查未通过（`statusCheckRollup` 有失败项）→ 报告状态，**不要** merge
- 作者就是自己 → 提示这属于作者侧，走 pr-skill

## 场景判定

| 场景 | 触发 | 动作 |
|------|------|------|
| A. 看 PR | "看这个 PR" / "review #N" | `gh pr view` + `gh pr diff` |
| B. 评审代码 | 判断质量 | 按 `references/code-review-checklist.md`（找 bug + 复用/简化/效率）就地面向 diff 评审 |
| C. 提交评审 | "approve" / "要求改" / "评论" | `gh pr review --approve/--request-changes/--comment` |
| D. 合并 | "合了" / "merge" | `gh pr merge --merge/--squash/--rebase` |

> 安全类问题（注入 / 鉴权 / 密钥 / 依赖 CVE）不在本清单范围，走 `code-security-audit`。

## 流程

1. **预检**：按第 0 步拿 author / 权限 / 检查状态
2. **看 PR**：`gh pr view <N>` 读标题/正文/变更文件；`gh pr diff <N>` 读 diff
3. **评代码质量**：按 `references/code-review-checklist.md` 四类（bug / 复用 / 简化 / 效率）扫 diff；意见按严重度分，每条给 file:line + 为什么 + 怎么改
4. **提交评审**：
   ```bash
   gh pr review <N> --approve                        # 通过
   gh pr review <N> --request-changes --body "..."   # 要求改（列具体点，别空泛）
   gh pr review <N> --comment --body "..."           # 仅评论，不表态
   ```
5. **合并**（approve 且检查通过后）：
   ```bash
   gh pr merge <N> --merge      # 或 --squash / --rebase，按团队规范
   gh pr close <N>              # 不合并就关
   ```
6. **交接**：合并后如果这批改动值得发版 → 走 `release-skill`；否则报告 PR URL 结束

## 自进化日志

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-13 | 协作流梳理（pr/release/issue 之后补 review） | review 是「评审者」的 skill（有 merge 权限），与 pr-skill 作者侧相对；本 skill 管 GitHub 机制（approve/changes/merge） |
| 2026-09-12 | 修复幽灵依赖 | 此前场景 B 委托一个**全仓库不存在**的 `code-review` skill（默认 18 个技能里没有任何技能拥有通用代码评审），PR 级评审是死路。改为自带 `references/code-review-checklist.md`（bug/复用/简化/效率四类 + 输出格式 + 安全类转 code-security-audit）；description 去掉 "open a PR"（本 skill 没有 `gh pr create`，提 PR 属 pr-skill）；补第 0 步权限/检查预检，避免无权限或检查失败时盲目 merge |
