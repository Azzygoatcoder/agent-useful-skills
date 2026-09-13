# 场景 A：Issue

> 共用判据（remote 约定 / push 权限 / 默认分支）见 SKILL.md 第 0 步，不在此重复。

issue 是**角色无关**的（谁都能提），但「分诊 / 关闭」是 maintainer 专属。

| 子场景 | 触发 | 谁 | 动作 |
|------|------|----|----|
| A1. 提 issue | "报 bug"、"提 feature" | 任何人 | `gh issue create`（按模板写清） |
| A2. 分诊 | "看 issue"、"打标签"、"指派" | Maintainer / Owner | `gh issue list` + `edit --add-label/--add-assignee` |
| A3. 处理闭环 | "处理 issue #N"、"关掉" | Maintainer / Owner | `gh issue comment` / `close` |
| A4. issue→PR | "修这个 issue" | 有 push 或 fork | 建分支 → 改 → PR 引用 `fixes #N` |

## A1 提 issue

1. `gh issue create --title "..." --body "..."`（或交互式 `gh issue create`）
2. body 模板：
   - bug：复现步骤 / 期望 vs 实际 / 环境版本
   - feature：动机 / 建议方案 / 可选替代
3. 报 issue URL

## A2 分诊

```bash
gh issue list --state open --label "help wanted"
gh issue edit <N> --add-label "bug" --add-assignee @me
```

## A3 处理闭环

```bash
gh issue comment <N> --body "..."
gh issue close <N> --reason completed        # 或 --reason "not planned" / --reason duplicate
gh issue close <N> --reason "not planned"    # 注意是带空格的值，不是 not-planned
```

> `--reason` 的合法值只有 `completed` / `not planned` / `duplicate`（gh 2.92 实测：写成
> `not-planned` 会被客户端直接拒绝）。判为重复时用 `--reason duplicate`，可另加
> `--duplicate-of <N>` 指向原 issue。

## A4 issue → PR 闭环

1. **建分支 + checkout**：

   ```bash
   gh issue develop <N> --checkout                            # 对权威仓库有写权限时
   gh issue develop <N> --checkout --branch-repo <你的fork>    # contributor：分支建在自己的 fork 上
   ```

   - 注意两点：`--checkout` 不是默认行为；分支建在**远端**仓库上，所以 contributor 必须给
     `--branch-repo`，否则会因无写权限失败
   - 都不支持时手建：`git checkout -b fix/<N>-<简述>`

2. 改代码 → commit
3. **PR 正文**写 `fixes #N`（必要时也写进 commit message），**别只放在标题**——GitHub 按
   PR 描述 / commit message 关联并自动关闭；标题单独写不保证生效。另注意：只有合入
   「拥有该 issue 的仓库的默认分支」才会自动关闭（fork 流程下尤其要确认 base）
4. 提 PR → 见 [pr.md](pr.md)

## 交接

需要改代码 → [pr.md](pr.md)；改完 merge → 若值得发版 → [release.md](release.md)
