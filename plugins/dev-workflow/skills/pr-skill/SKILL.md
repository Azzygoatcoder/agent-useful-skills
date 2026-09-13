---
name: pr-skill
description: Use when the user wants to open a PR, submit changes for review, or push a branch to their fork (fork workflow). Triggers on "create PR", "open PR", "submit PR", "提 PR", "开 PR", "/pr", 或用户做完一批改动想合入上游。
---

# PR — 提 Pull Request 工作流

fork 工作流提 PR。用于「无上游 push 权限」或「有权限但想走评审」的场景。

## 何时用 / 何时不用（看 push 权限）

判据同 release-skill，统一约定见插件 README「共用判据」：

| remote | 含义 |
|--------|------|
| `origin` | 你 clone 的那份（可能=权威仓库，也可能=你的 fork） |
| `upstream` | 权威仓库（仅当与 origin 不同时存在） |

```bash
gh api repos/{owner}/{repo} --jq .permissions.push   # true = 有直推权限
```

| 角色 | 要不要用 pr-skill |
|------|------------------|
| Owner（有 push 权限，且不需要评审） | ❌ 不需要——直接 push，不用 PR |
| Maintainer（团队 repo 写权限） | 可选——想走评审才用 |
| Contributor（只有 fork，无 push 权限） | ✅ 必须——fork-PR 是唯一路径 |

## Prerequisites

- `gh` CLI 已登录
- remotes：按上表统一命名（无 `upstream` 时先 `git remote add upstream <权威仓库>`）
- 工作区干净（先 commit）
- **默认分支在动手前先取**（见第 1 步）——`git rev-parse --abbrev-ref HEAD` 返回的是**当前**分支，不是默认分支，别用它

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
   > ⚠️ `reset --hard` 会丢弃本地未推送提交。上面那条 `log` 非空时**停下来问用户**，不要直接 reset。
5. **取 fork owner**：`git remote get-url origin` 拼 `--head`
6. **建 PR**（目标显式指权威仓库）：
   ```bash
   gh pr create --repo <权威owner>/<repo> --title "<conventional-commit>" \
     --base <default-branch> --head <fork-owner>:<branch> --body "..."
   ```
   - title 用 conventional commit（`fix:` / `feat:` / `refactor:` / `chore:` / `docs:`）
   - body 1-2 段说明改了什么、为什么；多文件改动加 "What changed" 节
7. **报 PR URL** 给用户，并告诉下一步：评审者侧走 `review-skill`

## Edge cases

- 工作区不干净：先 commit 或 stash
- 分支已在 fork 存在：force-push 或换名
- gh 未登录：`gh auth login`
- 多 remote：按 README「共用判据」确认命名后再推
- 无 `upstream` remote：说明是「只 clone 了 fork」，先 `git remote add upstream <权威仓库>`

## 自进化日志

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-13 | 角色化梳理（owner/maintainer/contributor） | 加「何时用」判据：owner 直接 push 不需要 PR，只有 contributor（或走评审的 maintainer）才用；与 release-skill 共用「push 权限」判据；默认分支自动判；中文化 + 场景表 + 自进化日志对齐科研骨架规范 |
| 2026-09-12 | origin 语义冲突修复 | 此前本 skill 定义 `origin`=权威仓库（`fork`=你的 fork），而 release-skill 定义 `origin`=你的 fork——同一句话 `git push origin vX.Y.Z` 在两套约定下推往不同仓库。根因是 `origin` 本身无固定含义（git 把「你 clone 的那个」叫 origin）。改为统一约定：`origin`=你 clone 的那份、`upstream`=权威仓库，角色改用 `gh api .permissions.push` 判而非 remote 名；写操作显式 `--repo`。另修：默认分支检测原本用 `git rev-parse --abbrev-ref HEAD`（返回当前分支，且步骤顺序保证取到错值）→ 改用 `gh repo view --json defaultBranchRef` 且提前到第 1 步；`reset --hard` 补 `git fetch` 与「未推送提交非空则停下」保护 |
