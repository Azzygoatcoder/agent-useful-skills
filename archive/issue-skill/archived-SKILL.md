---
name: issue-skill
description: Use when the user wants to create an issue, triage issues, close or resolve issues, or turn an issue into a PR on GitHub. Triggers on "提 issue", "报 bug", "提 feature request", "开 issue", "/issue", "看 issue", "分诊", "处理 issue", "关 issue", "修这个 issue", "issue 转 PR".
---

# Issue — GitHub Issue 工作流

issue 是**角色无关**的（谁都能提），但「分诊/关闭」是 maintainer 专属。

## 场景判定

| 场景 | 触发 | 谁 | 动作 |
|------|------|----|----|
| A. 提 issue | "报 bug"/"提 feature" | 任何人 | `gh issue create`（按模板写清） |
| B. 分诊 | "看 issue"/"打标签"/"指派" | Maintainer / Owner | `gh issue list` + `edit --add-label/--add-assignee` |
| C. 处理闭环 | "处理 issue #N"/"关掉" | Maintainer / Owner | `gh issue comment` / `close` |
| D. issue→PR | "修这个 issue" | 有 push 或 fork | 建分支 → 改 → PR 引用 `fixes #N` |

## 场景 A：提 issue

1. `gh issue create --title "..." --body "..."`（或交互式 `gh issue create`）
2. body 模板：
   - bug：复现步骤 / 期望 vs 实际 / 环境版本
   - feature：动机 / 建议方案 / 可选替代
3. 报 issue URL

## 场景 B：分诊

```bash
gh issue list --state open --label "help wanted"
gh issue edit <N> --add-label "bug" --add-assignee @me
```

## 场景 C：处理闭环

```bash
gh issue comment <N> --body "..."
gh issue close <N> --reason completed        # 或 --reason "not planned" / --reason duplicate
gh issue close <N> --reason "not planned"    # 注意是带空格的值，不是 not-planned
```

> `--reason` 的合法值只有 `completed` / `not planned` / `duplicate`（gh 2.92 实测：写成 `not-planned` 会被客户端直接拒绝）。判为重复时用 `--reason duplicate`，可另加 `--duplicate-of <N>` 指向原 issue。

## 场景 D：issue → PR 闭环

1. **建分支 + checkout**：
   ```bash
   gh issue develop <N> --checkout                        # 对权威仓库有写权限时
   gh issue develop <N> --checkout --branch-repo <你的fork>  # contributor：分支建在自己的 fork 上
   ```
   - 注意两点：`--checkout` 不是默认行为；分支建在**远端**仓库上，所以 contributor 必须给 `--branch-repo`，否则会因无写权限失败
   - 都不支持时手建：`git checkout -b fix/<N>-<简述>`
2. 改代码 → commit
3. **PR 正文**写 `fixes #N`（必要时也写进 commit message），**别只放在标题**——GitHub 按 PR 描述/commit message 关联并自动关闭；标题单独写不保证生效。另注意：只有合入「拥有该 issue 的仓库的默认分支」才会自动关闭（fork 流程下尤其要确认 base）
4. 提 PR 走 pr-skill（角色判据见插件 README「共用判据」）

## 自进化日志

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-13 | 协作流梳理（pr/release 之后补 issue） | issue 角色无关（谁都能提），但 B/C 分诊处理是 maintainer 专属；D 闭环复用 pr-skill 的 push 权限判据；`fixes #N` 让 PR 合并自动关 issue |
| 2026-09-12 | gh 实测校对 | 三处按 gh 2.92 实测修正：①`--reason not-planned` 是非法值（客户端直接拒绝），应为 `--reason "not planned"`，并补 `duplicate` + `--duplicate-of`；②`gh issue develop` 不会自动 checkout（需 `--checkout`），且分支建在远端仓库上，contributor 必须加 `--branch-repo` 否则因无写权限失败；③`fixes #N` 应在 PR **正文**/commit message（GitHub 只文档化这两条路径，标题单独写不保证生效），并补充「必须合入拥有该 issue 的仓库默认分支」这一前提 |
