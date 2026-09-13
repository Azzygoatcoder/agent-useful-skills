# issue-skill — 已合并

**状态：已归档，不再注册。**

2026-09-12 合并进 `dev-workflow`（场景 A）。

## 为什么合并

issue → PR → review → release 是同一条协作链。原先拆成四个同级技能，它们共享同一套
remote 约定与 push 权限判据、互相引用，却各自占一条 catalog，还要在「我该调哪个」上
做一次决策。合并后第 0 步（remote 约定 / push 权限 / 默认分支）只写一次。

## 现在用什么

`dev-workflow` 的场景 A，完整流程见
`plugins/dev-workflow/skills/dev-workflow/references/issue.md`
（提 issue / 分诊 / 关闭 / issue→PR 闭环四段，内容与原技能一致）。
