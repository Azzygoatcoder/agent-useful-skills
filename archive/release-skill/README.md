# release-skill — 已合并

**状态：已归档，不再注册。**

2026-09-12 合并进 `dev-workflow`（场景 D）。

## 为什么合并

见 archive/issue-skill/README.md 的同一段说明：四技能本是一条链。

## 现在用什么

`dev-workflow` 的场景 D，完整流程见
`plugins/dev-workflow/skills/dev-workflow/references/release.md`。

## 合并时顺带修掉的问题

1. **`origin` 语义冲突**：本技能定义 `origin`=你的 fork，而 pr-skill 定义 `origin`=权威仓库。
   已统一（详见 archive/pr-skill/README.md）。
2. **默认分支检测错误**：`git rev-parse --abbrev-ref HEAD` 返回当前分支，不是默认分支。
   已改用 `gh repo view --json defaultBranchRef`。
3. **`--notes-file notes.md` 从不创建**：场景 A 与 B 都用它，但没有任何步骤写这个文件，
   照做会直接报缺文件。已补写 notes.md 的步骤，并给出 `--generate-notes` 替代。
4. **指向不存在的字符串**：第 7 步说「更新版本 badge（`当前版本：**vX.Y.Z**`）」，
   而该字符串全仓库只出现在这一行本身（真实的版本位点是插件 README 横幅、版本历史表、
   `VERSIONING.md` 表、根 README 插件表、`package.json`）。已改为按 bump 清单枚举真实位置。
5. **bump 清单不完整**：原先只提 `pyproject.toml` + `__init__.py` + 插件 `plugin.json` +
   「各自 README changelog」，漏了 `package.json`、`VERSIONING.md` 表、根 README 插件表、
   插件 README 的版本横幅（上一次 1.2.0 bump 实际改了 8 个文件）。
6. **`git pull origin <default>` 在 fork 流程下拉错源**：contributor 场景下 origin 是自己的
   fork，会拉到不含刚合并提交的陈旧分支。已改为 `git fetch upstream` +
   `git merge --ff-only upstream/<default>`。
