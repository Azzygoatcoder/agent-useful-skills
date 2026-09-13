# pr-skill — 已合并

**状态：已归档，不再注册。**

2026-09-12 合并进 `dev-workflow`（场景 B）。

## 为什么合并

见 archive/issue-skill/README.md 的同一段说明：四技能本是一条链。

## 现在用什么

`dev-workflow` 的场景 B，完整流程见
`plugins/dev-workflow/skills/dev-workflow/references/pr.md`。

## 合并时顺带修掉的问题

1. **`origin` 语义冲突**：本技能定义 `origin`=权威仓库（`fork`=你的 fork），而 release-skill
   定义 `origin`=你的 fork。两者都自称「与对方共用同一判据」，于是同一句
   `git push origin vX.Y.Z` 在两套约定下推往不同仓库。根因是 `origin` 本身无固定含义
   （git 把「你 clone 的那个」叫 origin）。已统一为：`origin`=你 clone 的那份、
   `upstream`=权威仓库，角色改用 `gh api .permissions.push` 判而非 remote 名。
2. **默认分支检测错误**：原用 `git rev-parse --abbrev-ref HEAD`，它返回**当前**分支；
   而本技能的步骤顺序（先建特性分支、后取默认分支）保证在第 3 步取到错值，再拿去做
   `git reset --hard`。已改用 `gh repo view --json defaultBranchRef` 并提前到第 1 步。
3. **`reset --hard` 无保护**：原先直接重置，会静默丢弃本地未推送提交。已补 `git fetch`
   与「未推送提交非空则停下问用户」。
