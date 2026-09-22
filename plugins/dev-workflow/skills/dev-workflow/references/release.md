# 场景 D：Release（发版本）

> 共用判据（remote 约定 / push 权限 / 默认分支）见 SKILL.md 第 0 步，不在此重复。

半自动发版本：定版本 → bump → tag → GitHub Release。按 push 权限分流。

## 场景判定

| push 权限 | 角色 | 场景 |
|:--:|------|------|
| true | Owner / Maintainer | **A. 直推**（默认） |
| false | Contributor | **B. fork-PR** |

## 通用准备

- `gh` CLI 已登录；工作区干净
- 默认分支按 SKILL.md 第 0 步取
- 版本号在 `pyproject.toml`（`[project] version = "X.Y.Z"`）；有包 `__init__.py` 的
  `__version__` 要同步——monorepo 可能只有 pyproject、无 `__init__`，跳过即可
- **monorepo 有插件**（`plugins/*/.claude-plugin/plugin.json`）：bump 根版本时顺带查各插件
  version 是否与各自 README changelog 同步（失配例子：code-security-skills 曾
  plugin.json 1.3.1 vs changelog 1.4.0），见 `VERSIONING.md`
- **先探测发布机制** —— 见下一节。这一步**必须最先做**：机制搞错不是报错，是静默少东西

## 发布机制：Release 由谁创建（先确认，别默认手动）

**同一个仓库里，Release 只能有一个创建者。** 两种机制都可能存在：

| 机制 | 怎么认 | 你该做什么 |
|------|--------|-----------|
| **CI 自动**（tag 触发） | `.github/workflows/*.yml` 里有 `on: push: tags:`，且步骤里出现 `gh release create` / `softprops/action-gh-release` / `--upload-file` 之类 | **只推 tag**，然后等 workflow。**不要**手跑 `gh release create` |
| **手动**（无相应 workflow） | 没有 tag 触发的 release workflow | 按场景 A 第 4 步手跑 |

```bash
ls .github/workflows/
grep -l -e 'tags:' -e 'release' .github/workflows/*.yml
```

### 手跑 + CI 抢跑会怎样：不报错，而是静默少产物

两个机制**会抢跑**，典型后果**不是报错**：

1. workflow 里「创建 Release」那步看到 Release 已存在 → **跳过**（幂等设计本身没错）
2. 但「上传产物」那步往往挂在创建步骤的输出上（`if: steps.create.outputs.upload_url` 之类）→ **一并跳过**
3. 结果：Release **有 notes、看着正常，却一个产物都没有** —— 而前几版都有

**"看起来完整"是最难发现的一种失败**，所以第 5 步的产物核对不是可选项。

### 恢复：删 Release 不动 tag

```bash
gh release delete vX.Y.Z --repo <owner>/<repo> --yes      # 只删 Release
gh workflow run release.yml --repo <owner>/<repo> -f tag=vX.Y.Z   # 或 gh run rerun <run-id>
```

> **`gh release delete` 不会删 tag** —— 非直觉但关键：所以删掉手动那条、重跑 workflow 就能拿到正确产物，tag 不受影响。
> 除非确定要弃版，**不要** `git push --delete origin vX.Y.Z`。

### 如果你在写这个 workflow

创建步骤要**幂等但不吞上传**：Release 已存在时不要整个跳过，而要仍把产物传上去，
或者干脆 `gh release upload --clobber`。`if: steps.create.outputs.upload_url` 这种把上传
挂在创建输出上的写法，正是上面静默失败的根源。

## bump 清单（逐项确认，别只改一处）

版本号散落在多处，改完**逐项 grep 旧版本号**确认无残留：

| 位置 | 何时需要 |
|------|---------|
| `pyproject.toml` `[project] version` | 总是 |
| `package.json` `version` | 仓库根有 package.json 时 |
| 包 `__init__.py` `__version__` | 存在时 |
| 各插件 `plugins/*/.claude-plugin/plugin.json` | 改了哪个插件的 skills 就 bump 哪个 |
| 各插件 README **横幅**（`> **vX.Y.Z** —`）与**版本历史表** | 同上（VERSIONING.md 要求两者同步） |
| `VERSIONING.md` 插件版本表 | 同上 |
| 根 `README.md` 插件表 | 同上 |
| CHANGELOG / 版本历史表 | 有则加一行（**如实写，不要改写历史行**） |

## 场景 A：自有仓库直推（默认）

1. **定版本**：读 `pyproject.toml` 当前版本 + `git tag --list` 看上次 tag；按 commit 增量建议
   - Patch（X.Y.Z+1）：bug 修复 / 安全补丁 / 小文档
   - Minor（X.Y+1.0）：新特性 / 无破坏重构
   - Major（X+1.0.0）：破坏性变更（0.x 少见）
   - RC 后缀（v0.2.0-rc9）：可去 RC（v0.3.0）或加 RC 号（v0.2.0-rc10）
2. **bump**：按上面「bump 清单」逐项改；版本已对就跳过
3. **写 notes.md**（下一步要读它，别跳过）：

   ```bash
   git log <last-tag>..HEAD --oneline > notes.md
   ```

   按主题分组（核心重构 / 打包 / 特性 / 文档）。也可完全交给 `gh`：用
   `--generate-notes [--notes-start-tag <last-tag>]` 省掉本步。

4. **tag**（并按「发布机制」分叉——**这一步最容易搞错**）：

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

   - **CI 自动**：到此为止，**不要**再手跑 `gh release create`。等 workflow 跑完，走第 5 步核对。
   - **手动**（仓库没有 tag 触发的 release workflow）：
     ```bash
     gh release create vX.Y.Z --title "vX.Y.Z — 一句话主题" --notes-file notes.md
     ```
     > 手跑时**别忘产物**：若这个项目历来附产物，就显式带上
     > （`gh release create ... ./dist/*` 或事后 `gh release upload vX.Y.Z ./dist/*`），
     > 否则照样是个"空"Release。

5. **核对产物（必做，不是可选项）**：产物缺失**不会报错**，只能靠对比发现。

   ```bash
   gh release view <上一版 tag> --json assets -q '.assets[].name'
   gh release view vX.Y.Z       --json assets -q '.assets[].name'
   ```

   - 两边**对不上**（上一版有、这一版没有）→ 别告诉用户"发好了"，按「恢复」一节重来
   - 这个项目**本来就**不附产物（仓库本身即交付物）→ 两边都是空的才算通过，
     并在给用户的总结里**明说**"本仓库 Release 不含产物" —— 别让用户自己发现

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

6. **GitHub Release**：**先按「发布机制」确认由谁创建。**
   - **CI 自动**：tag 推上去就够了，等 workflow 跑完 → 跳到第 7 步前先核对产物（同场景 A 第 5 步）
   - **手动**：先写 `notes.md`（同场景 A 第 3 步），再
     `gh release create vX.Y.Z --repo <权威owner>/<repo> --title ... --notes-file notes.md`
     （非 RC 写全面 notes，RC/patch 只列上次 tag 后的 PR）
7. **同步版本号**：按「bump 清单」逐项确认已同步
8. **cleanup**：`git branch -d release/vX.Y.Z`

## Edge cases

- **Release 被 workflow 抢先创建**：症状是**产物缺失而非报错**。按「发布机制 → 手跑会怎样」判断，
  用 `gh release delete` + 重跑 workflow 恢复（**tag 不受影响**）
- **这一版产物比上一版少**：默认按失败处理，不要当成"这次恰好没有" ——
  先 `gh release view <上一版> --json assets` 与这一版对比
- **tag 已推但 Release 没建**：CI 自动的仓库里用 `gh workflow run` 补建；
  **别**手建盖过去 —— 那正是抢跑的起点
- 工作区不干净：警告用户，release 应从未提交状态出
- CI 超时（>10min）：手动查 run URL
- tag 已存在：多半要下一个 RC 号或 patch
- release PR 冲突：rebase 到最新默认分支
- 多包仓库：问清 bump 哪个包

## 交接

发版后发现问题 → 回 [issue.md](issue.md) 提 issue（不要直接热修，留下记录）
