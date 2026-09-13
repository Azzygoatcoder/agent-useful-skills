---
name: dev-workflow
description: Use when the user wants GitHub collaboration operations — file or triage an issue, open a PR, review or merge a PR, or cut a release (bump / tag / publish). Triggers on "提 issue", "报 bug", "分诊", "关 issue", "提 PR", "开 PR", "review 这个 PR", "approve", "要求修改", "merge", "合了", "release", "发版本", "发 rc", "/issue", "/pr", "/review", "/release". Not for general code-quality review outside a PR, and not for CI/deployment automation.
---

# Dev Workflow — GitHub 协作与发布

issue → PR → review → merge → release 是一条链。本技能用一个入口覆盖全链，先判场景再走对应流程。

原先拆成 issue-skill / pr-skill / review-skill / release-skill 四个同级技能，它们共享同一套
remote 约定与 push 权限判据，互相引用，还各自占一条 catalog——2026-09-12 合并。

## 第 0 步：共用判据（所有场景先做）

**先统一 remote 命名，再谈角色。** `origin` 本身不携带含义——git 把「你 clone 的那个仓库」
叫 origin，所以它可能是权威仓库，也可能是你的 fork。

| remote | 含义 |
|--------|------|
| `origin` | **你 clone 的那份**（可能=权威仓库，也可能=你的 fork） |
| `upstream` | **权威仓库**（仅当它与 origin 不同时存在） |

判定用**权限**，不用 remote 名字：

```bash
gh api repos/{owner}/{repo} --jq .permissions.push   # true = 有直推权限
```

| push 权限 | 角色 | issue | PR | release |
|:--:|------|-------|----|---------|
| true | Owner / Maintainer | 分诊/关闭 | 直推即可，想要评审才开 PR | 场景 A 直推 |
| false | Contributor | 只能提 | fork-PR 是唯一路径 | 场景 B fork-PR |

若「只 clone 了自己的 fork」而没有 `upstream`，先补上：

```bash
git remote add upstream https://github.com/<权威owner>/<repo>.git
```

> ⚠️ 写操作（push / `gh release` / `gh pr` / `gh issue`）一律**显式指名 remote 或 `--repo`**，
> 不要依赖 `gh` 的自动推断——多 remote 时它可能挑错目标。

**默认分支**统一这样取（`git rev-parse --abbrev-ref HEAD` 返回的是**当前**分支，不能用）：

```bash
gh repo view <owner>/<repo> --json defaultBranchRef -q .defaultBranchRef.name
```

## 场景判定

| 场景 | 触发 | 详细流程 |
|------|------|---------|
| **A. issue** — 提 / 分诊 / 关闭 / 转 PR | "报 bug"、"提 feature"、"看 issue"、"分诊"、"关 issue"、"修这个 issue" | [references/issue.md](references/issue.md) |
| **B. PR** — 开 PR、推分支到 fork | "提 PR"、"开 PR"、"submit PR"、"做完一批改动想合入" | [references/pr.md](references/pr.md) |
| **C. review** — 看 / 评审 / 合并 PR | "review 这个 PR"、"看下这个 PR"、"approve"、"要求修改"、"merge"、"合了" | [references/review.md](references/review.md) |
| **D. release** — bump / tag / 发 Release | "release"、"发版本"、"发 rc"、"准备发 vX.Y.Z" | [references/release.md](references/release.md) |

## 链式交接（每个场景跑完该告诉用户下一步）

```
issue ──(需要改代码)──> pr ──(开好了)──> review ──(merge 后值得发版)──> release
  ↑                                                                      │
  └────────────────(发版后发现新问题 → 回 A 提 issue)────────────────────┘
```

- **A → B**：issue 需要改代码 → 走 pr.md（角色按第 0 步判）
- **B → C**：PR 开好后，评审者侧走 review.md；作者侧等评审
- **C → D**：merge 后若这批改动值得发版 → 走 release.md
- **D → A**：发版后发现问题 → 回 issues（不要直接热修，留下记录）

## 边界

- **不在 PR 语境下的通用代码质量评审** → 不属于本技能；PR 内的代码评审走
  [references/review.md](references/review.md)（自带评审清单）
- **安全审计**（漏洞/注入/鉴权/密钥/依赖 CVE）→ 走 `code-security-audit`，不要在 PR 评审里顺手做
- **CI / 部署自动化** → 本技能不含；release.md 只负责 bump/tag/Release，CI 状态只做检查与阻断

## 自进化日志

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-13 | 四技能各自成型 | issue 角色无关但分诊/关闭是 maintainer 专属；PR 判据=push 权限；review 是评审者侧（有 merge 权限）；release 按 push 权限分 A 直推 / B fork-PR |
| 2026-08-30 | 归档 meta skill 之后 | review-skill 补自带代码评审清单；description 重写做触发词卫生 |
| 2026-09-12 | **四技能合并为一个** | issue/pr/review/release 本是同一条链，共享同一套 remote 约定与 push 权限判据，拆成四个同级技能只增加「我该调哪个」的决策成本与触发词重叠。合并为一个入口 + 四份 references，第 0 步共用判据只写一次。同步修掉合并前发现的跨技能矛盾（见下） |
| 2026-09-12 | 合并前的 P1 修复（已并入本文件） | ①`origin` 在两个技能里定义相反 → 统一为 origin=你 clone 的那份/upstream=权威仓库，角色改用 `gh api .permissions.push` 判；②默认分支检测用 `git rev-parse --abbrev-ref HEAD`（返回当前分支）→ 改 `gh repo view --json defaultBranchRef`；③`reset --hard` 补 fetch 与未推送提交保护；④`--notes-file notes.md` 从未创建 → 补生成步骤；⑤「README 版本 badge」指向不存在的字符串 → 改为枚举真实位置；⑥bump 清单补全 package.json / VERSIONING.md / 根 README / 插件横幅 |
