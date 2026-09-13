# review-skill — 已合并

**状态：已归档，不再注册。**

2026-09-12 合并进 `dev-workflow`（场景 C）。

## 为什么合并

见 archive/issue-skill/README.md 的同一段说明：四技能本是一条链。

## 现在用什么

`dev-workflow` 的场景 C，完整流程见
`plugins/dev-workflow/skills/dev-workflow/references/review.md`；
自带代码评审清单见同目录 `code-review-checklist.md`（已随本次合并一起搬过去）。

## 合并时顺带修掉的问题

1. **幽灵依赖**：场景 B「评审代码」原先委托一个**全仓库不存在**的 `code-review` 技能
   （27 个 SKILL.md 里没有这个名字，archive 里也没有），于是 PR 级代码评审是死路。
   已改为自带 `code-review-checklist.md`（bug / 复用 / 简化 / 效率四类 + 输出格式 +
   安全类转 `code-security-audit`）。
2. **description 与正文不符**：原 description 声称能 "open a PR"，但正文没有
   `gh pr create`（提 PR 属 pr-skill）。已删掉该能力声明并加边界说明。
3. **无权限/检查预检**：原流程把 merge 当作 approve 后的默认动作，没有能力检查——
   无 merge 权限或检查失败时会直接失败。已补第 0 步预检
   （`gh pr view --json author,reviewDecision,mergeable,statusCheckRollup` +
   `gh api repos/{owner}/{repo} --jq .permissions.push`）。
