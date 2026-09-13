# Dev Workflow

> **v1.0.2** — Git 协作与发布技能集合：提 PR、发版本、issue、code review。

## Skills

| Skill | 角色 | 判据 |
|-------|------|------|
| [pr-skill](skills/pr-skill/SKILL.md) | 提 PR（fork 工作流） | 无上游 push 权限（contributor）或想走评审（maintainer） |
| [release-skill](skills/release-skill/SKILL.md) | 发版本（tag + release） | 有 push 权限 → 直推；无 → fork-PR |
| [issue-skill](skills/issue-skill/SKILL.md) | issue（提/分诊/处理/转 PR） | 角色无关（谁都能提）；分诊关闭是 maintainer 专属 |
| [review-skill](skills/review-skill/SKILL.md) | PR review（看/评审/合并） | 评审者（有 merge 权限的 maintainer/owner） |

## 共用判据

**先统一 remote 命名，再谈角色。** `origin` 本身不携带含义——git 把「你 clone 的那个仓库」叫 origin，所以它可能是权威仓库，也可能是你的 fork。四个技能共用下面这套约定：

| remote | 含义 |
|--------|------|
| `origin` | **你 clone 的那份**（可能=权威仓库，也可能=你的 fork） |
| `upstream` | **权威仓库**（仅当它与 origin 不同时存在） |

判定用**权限**而不是名字：

```bash
gh api repos/{owner}/{repo} --jq .permissions.push   # true = 有直推权限
```

- 有 push 权限 → Owner / Maintainer → 直推（release 走 A，pr 不需要）
- 无 push 权限 → Contributor → fork-PR（release 走 B，pr 必须）

若你是「只 clone 了自己的 fork」而没有 `upstream`，先补上再按上面判：

```bash
git remote add upstream https://github.com/<权威owner>/<repo>.git
```

> ⚠️ 写操作（push / gh release / gh pr）一律**显式指名 remote**，不要依赖 `gh` 的自动推断——多 remote 时它可能挑错目标。

<p align="center"><img src="assets/push-access-flowchart.png" width="560" alt="push 权限判定"/></p>

## 协作流全景

PR / release / issue / review 四个协作流已覆盖。剩余：GitHub Discussion（无专用 gh 命令）、CI 自动化（release 后自动跑测试）暂缓。

## 版本历史

| 版本 | 日期 | 变更 |
| ---- | ---- | ---- |
| 1.0.2 | 2026-09-12 | 统一 remote 约定（`origin`=你 clone 的那份 / `upstream`=权威仓库），角色改用 `gh api .permissions.push` 判——此前 pr-skill 与 release-skill 对 `origin` 的定义相反；按 gh 2.92 实测修正 `issue close --reason "not planned"`、`issue develop --checkout/--branch-repo`、`fixes #N` 位置；默认分支检测改用 `gh repo view --json defaultBranchRef`（原命令返回当前分支）；补 `reset --hard` 的 fetch 与未推送提交保护；release-skill 补 notes.md 生成步骤与完整 bump 清单（package.json / VERSIONING.md / 根 README / 插件 README 横幅）；补 1.0.1 遗漏的四技能 description 重写记录 |
| 1.0.1 | 2026-08-30 | review-skill 去除对归档流程 skill 的依赖，description 精简；四技能 description 重写（触发词卫生） |
| 1.0.0 | 2026-08-13 | 初始：pr / release / issue / review 四技能，push 权限判定 |
