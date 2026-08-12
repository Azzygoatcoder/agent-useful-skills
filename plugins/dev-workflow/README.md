# Dev Workflow

Git 协作与发布技能集合：提 PR、发版本。

## Skills

| Skill | 角色 | 判据 |
|-------|------|------|
| [pr-skill](skills/pr-skill/SKILL.md) | 提 PR（fork 工作流） | 无上游 push 权限（contributor）或想走评审（maintainer） |
| [release-skill](skills/release-skill/SKILL.md) | 发版本（tag + release） | 有 push 权限 → 直推；无 → fork-PR |
| [issue-skill](skills/issue-skill/SKILL.md) | issue（提/分诊/处理/转 PR） | 角色无关（谁都能提）；分诊关闭是 maintainer 专属 |

## 共用判据

`git remote -v` 看 origin 是「权威仓库」还是「你的 fork」：

- origin = 权威仓库 → Owner / Maintainer → 直推（release 走 A，pr 不需要）
- origin = 你的 fork → Contributor → fork-PR（release 走 B，pr 必须）

## 后续方向

GitHub 协作流不止 PR 和 release，issue（创建/分诊/关闭）、code review 等同类流程可继续按「角色判据」补齐。
