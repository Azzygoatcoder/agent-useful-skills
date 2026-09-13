# 场景 C：Review（评审者侧 PR review）

> 共用判据（remote 约定 / push 权限 / 默认分支）见 SKILL.md 第 0 步，不在此重复。

评审者动作：看 PR → 评审 → 提交 approve/changes → 合并。与 [pr.md](pr.md)（作者提 PR）相对。

## 角色

本流程是「评审者」的 = 有 merge 权限的 maintainer / owner。作者侧走 [pr.md](pr.md)。

## 第 0 步：能力与状态预检（别盲 merge）

```bash
gh pr view <N> --json author,reviewDecision,mergeable,statusCheckRollup
gh api repos/{owner}/{repo} --jq .permissions.push     # 无 push 权限 → 只能评审，不能合并
```

- 无 merge 权限 → 只提交评审意见，然后交回作者 / maintainer
- 检查未通过（`statusCheckRollup` 有失败项）→ 报告状态，**不要** merge
- 作者就是自己 → 提示这属于作者侧，走 [pr.md](pr.md)

## 场景判定

| 子场景 | 触发 | 动作 |
|------|------|------|
| C1. 看 PR | "看这个 PR" / "review #N" | `gh pr view` + `gh pr diff` |
| C2. 评审代码 | 判断质量 | 按 `code-review-checklist.md`（找 bug + 复用/简化/效率）就地面向 diff 评审 |
| C3. 提交评审 | "approve" / "要求改" / "评论" | `gh pr review --approve/--request-changes/--comment` |
| C4. 合并 | "合了" / "merge" | `gh pr merge --merge/--squash/--rebase` |

> 安全类问题（注入 / 鉴权 / 密钥 / 依赖 CVE）不在本清单范围，走 `code-security-audit`。

## 流程

1. **预检**：按第 0 步拿 author / 权限 / 检查状态
2. **看 PR**：`gh pr view <N>` 读标题/正文/变更文件；`gh pr diff <N>` 读 diff
3. **评代码质量**：按 [code-review-checklist.md](code-review-checklist.md) 四类
   （bug / 复用 / 简化 / 效率）扫 diff；意见按严重度分，每条给 file:line + 为什么 + 怎么改
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

6. **交接**：合并后如果这批改动值得发版 → [release.md](release.md)；否则报告 PR URL 结束
