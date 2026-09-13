---
name: release-skill
description: Use when the user wants to cut a release — bump version, tag, and publish to GitHub Releases. Triggers on "release", "发版本", "bump version", "cut release", "publish release", "/release", "准备发 rc", "发 rc", "tag and release", 或用户做完一批功能说"准备发 vX.Y.Z"。
---

# Release — 发版本工作流

半自动发版本：定版本 → bump → tag → GitHub Release。按仓库类型分流。

## 第 0 步：场景判定（看 push 权限，不看仓库归属）

统一约定（同 pr-skill，见插件 README「共用判据」）：

| remote | 含义 |
|--------|------|
| `origin` | 你 clone 的那份（可能=权威仓库，也可能=你的 fork） |
| `upstream` | 权威仓库（仅当与 origin 不同时存在） |

判定用权限，不用 remote 名：

```bash
gh api repos/{owner}/{repo} --jq .permissions.push   # true = 有直推权限
```

| push 权限 | 你的角色 | 场景 |
|-----------|---------|------|
| true | Owner / Maintainer | A. 直推 |
| false | Contributor | B. fork-PR |

> 有 push 权限 → A；无 → B。默认 A。同一个人对不同 repo 角色不同，每次按判据现判。

## 通用准备

- `gh` CLI 已登录；工作区干净
- **默认分支先取**：`gh repo view <owner>/<repo> --json defaultBranchRef -q .defaultBranchRef.name`
  （master / main 皆可，别硬编码；**不要**用 `git rev-parse --abbrev-ref HEAD`——它返回当前分支）
- 版本号在 `pyproject.toml`（`[project] version = "X.Y.Z"`）；有包 `__init__.py` 的 `__version__` 要同步——monorepo 可能只有 pyproject、无 `__init__`，跳过即可
- **monorepo 有插件**（`plugins/*/.claude-plugin/plugin.json`）：bump 根版本时顺带查各插件 version 是否与各自 README changelog 同步（失配例子：code-security-skills 曾 plugin.json 1.3.1 vs changelog 1.4.0），见 VERSIONING.md

## bump 清单（逐项确认，别只改一处）

版本号散落在多处，改完**逐项 grep 旧版本号**确认无残留：

| 位置 | 何时需要 |
|------|---------|
| `pyproject.toml` `[project] version` | 总是 |
| `package.json` `version` | 仓库根有 package.json 时（本仓库有） |
| 包 `__init__.py` `__version__` | 存在时 |
| 各插件 `plugins/*/.claude-plugin/plugin.json` | 改了哪个插件的 skills 就 bump 哪个 |
| 各插件 README **横幅**（`> **vX.Y.Z** —`）与**版本历史表** | 同上（VERSIONING.md 要求两者同步） |
| `VERSIONING.md` 插件版本表 | 同上 |
| 根 `README.md` 插件表 | 同上 |
| CHANGELOG / 版本历史表 | 有则加一行（如实写，不要改写历史行） |

## 场景 A：自有仓库直推（默认）

1. **定版本**：读 `pyproject.toml` 当前版本 + `git tag --list` 看上次 tag；按 commit 增量建议
   - Patch（X.Y.Z+1）：bug 修复 / 安全补丁 / 小文档
   - Minor（X.Y+1.0）：新特性 / 无破坏重构
   - Major（X+1.0.0）：破坏性变更（0.x 少见）
   - RC 后缀（v0.2.0-rc9）：可去 RC（v0.3.0）或加 RC 号（v0.2.0-rc10）
2. **bump**：按上面「bump 清单」逐项改；版本已对就跳过。改了哪个插件的 skills 就 bump 哪个插件的 `plugin.json` + README
3. **写 notes.md**（下一步要读它，别跳过）：
   ```bash
   git log <last-tag>..HEAD --oneline > notes.md
   ```
   按主题分组（核心重构 / 打包 / 特性 / 文档）。也可完全交给 `gh`：用 `--generate-notes [--notes-start-tag <last-tag>]` 省掉本步。
4. **tag + release**：
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "vX.Y.Z — 一句话主题" --notes-file notes.md
   ```

## 场景 B：上游贡献（fork-PR-CI 完整流程）

1. **定版本**：同上（读 pyproject + `__init__`，问用户，建议增量）
2. **bump**：按「bump 清单」逐项改 → `git commit -m "chore: bump version to X.Y.Z"`
3. **release PR**：
   ```bash
   git checkout -b release/vX.Y.Z
   git push origin release/vX.Y.Z -u        # origin = 你 clone 的那份
   git fetch upstream
   git checkout <default-branch>
   git log upstream/<default-branch>..HEAD --oneline   # 非空则停下问用户
   git reset --hard upstream/<default-branch>
   gh pr create --repo <权威owner>/<repo> --title "chore: bump version to X.Y.Z" \
     --base <default-branch> --head <fork-owner>:release/vX.Y.Z --body "..."
   ```
   - PR body 含 "Changes since <last-tag>"，逐条列 merged PR
4. **CI**：`gh pr checks <pr>`；失败不 merge，先修
5. **merge + tag**（在权威仓库上操作）：
   ```bash
   gh pr merge <pr> --repo <权威owner>/<repo> --merge --delete-branch
   git fetch upstream
   git checkout <default-branch> && git merge --ff-only upstream/<default-branch>
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push upstream vX.Y.Z          # tag 推到权威仓库（有权限的话）
   ```
   > 无 tag push 权限时：tag 由 maintainer 打，或改走场景 A 的 CI 流程——先确认再动手。
6. **GitHub Release**：先写 `notes.md`（同场景 A 第 3 步），再
   `gh release create vX.Y.Z --repo <权威owner>/<repo> --title ... --notes-file notes.md`
   （非 RC 写全面 notes，RC/patch 只列上次 tag 后的 PR）
7. **同步版本号**：按「bump 清单」逐项确认已同步（各插件 README 横幅 + 版本历史表、VERSIONING.md 表、根 README 插件表）
8. **cleanup**：`git branch -d release/vX.Y.Z`

## Edge cases

- 工作区不干净：警告用户，release 应从未提交状态出
- CI 超时（>10min）：手动查 run URL
- tag 已存在：多半要下一个 RC 号或 patch
- release PR 冲突：rebase 到最新默认分支
- 多包仓库：问清 bump 哪个包

## 自进化日志

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-13 | claude-useful-skills v1.1.0 发版 dogfooding | 加场景 A 自有仓库直推（无 fork/CI 走 bump→tag→release，别硬套 fork-PR）；默认分支自动判（master≠main）；monorepo 可能无 `__init__.py`，版本只在 pyproject；补场景判定表 + 中文 + 自进化日志，对齐科研骨架 skill 规范 |
| 2026-08-13 | 角色化梳理（owner/maintainer/contributor） | 场景判定从「仓库归属」改为「push 权限」：origin 是权威仓库（owner/maintainer）→ A 直推；origin 是 fork（contributor）→ B fork-PR。与 pr-skill 共用同一判据 |
| 2026-09-12 | origin 语义冲突 + 不可执行命令修复 | 统一约定：`origin`=你 clone 的那份、`upstream`=权威仓库，角色改用 `gh api .permissions.push` 判（原来两 skill 对 `origin` 的定义相反，同一句 `git push origin vX.Y.Z` 会推往不同仓库）。另修四处会直接失败/落空的指令：①默认分支检测用 `git rev-parse --abbrev-ref HEAD`（返回当前分支）→ 改 `gh repo view --json defaultBranchRef`；②`--notes-file notes.md` 从不创建 → 补写 notes.md 步骤并给出 `--generate-notes` 替代；③「README 版本 badge（当前版本：**vX.Y.Z**）」该字符串全仓库不存在 → 改为按 bump 清单枚举真实位置；④bump 清单缺 `package.json`/`VERSIONING.md` 表/根 README 插件表/插件 README 横幅（上次 1.2.0 bump 实际改了 8 个文件） |
