# 场景 B：PR（fork 工作流提 PR）

> 共用判据（remote 约定 / push 权限 / 默认分支）见 SKILL.md 第 0 步，不在此重复。

用于「无上游 push 权限」或「有权限但想走评审」的场景。

| 角色 | 要不要走本流程 |
|------|--------------|
| Owner（有 push 权限，且不需要评审） | ❌ 不需要——直接 push |
| Maintainer（有写权限） | 可选——想走评审才用 |
| Contributor（只有 fork，无 push 权限） | ✅ 必须——fork-PR 是唯一路径 |

## Prerequisites

- `gh` CLI 已登录
- remotes 按 SKILL.md 第 0 步统一命名（无 `upstream` 时先 `git remote add upstream <权威仓库>`）
- 工作区干净（先 commit）
- **默认分支在动手前先取**（见第 1 步）

## 步骤

1. **先取默认分支名**（必须在建分支之前——建完分支后 HEAD 就不再指向默认分支了）：

   ```bash
   gh repo view <权威owner>/<repo> --json defaultBranchRef -q .defaultBranchRef.name
   # 或：git symbolic-ref --short refs/remotes/upstream/HEAD | sed 's|^upstream/||'
   ```

2. **定分支名**：问用户，或从 commit 主题推（如 `fix/feishu-deadlock`、`feat/aihot-push`）
3. **建分支 + 推到你的 fork**：

   ```bash
   git checkout -b <branch>
   git push origin <branch> -u          # origin = 你 clone 的那份
   ```

4. **把本地默认分支对齐权威仓库**（工作留在 feature 分支）：

   ```bash
   git fetch upstream
   git checkout <default-branch>
   git log upstream/<default-branch>..HEAD --oneline   # 必须为空；非空说明有未推送提交
   git reset --hard upstream/<default-branch>
   ```

   > ⚠️ `reset --hard` 会丢弃本地未推送提交。上面那条 `log` 非空时**停下来问用户**，
   > 不要直接 reset。

5. **取 fork owner**：`git remote get-url origin` 拼 `--head`
6. **建 PR**（目标显式指权威仓库）：

   ```bash
   gh pr create --repo <权威owner>/<repo> --title "<conventional-commit>" \
     --base <default-branch> --head <fork-owner>:<branch> --body "..."
   ```

   - title 用 conventional commit（`fix:` / `feat:` / `refactor:` / `chore:` / `docs:`）
   - body 1-2 段说明改了什么、为什么；多文件改动加 "What changed" 节

7. **报 PR URL**，并告诉下一步：评审者侧走 [review.md](review.md)

## Edge cases

- 工作区不干净：先 commit 或 stash
- 分支已在 fork 存在：force-push 或换名
- gh 未登录：`gh auth login`
- 多 remote：按 SKILL.md 第 0 步确认命名后再推
- 无 `upstream` remote：说明是「只 clone 了 fork」，先 `git remote add upstream <权威仓库>`

## 交接

PR 开好 → [review.md](review.md)（评审者）或等评审（作者）
