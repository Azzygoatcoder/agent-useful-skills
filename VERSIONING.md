# 版本管理

monorepo 两层版本，分开管。

## 根快照（pyproject.toml）

- 用途：`pip install -e .`（bin 脚本）+ GitHub Release
- bump 时机：发整仓 release 时（走 `dev-workflow` 技能的 release 场景）
- 语义：整仓在某个时间点的 coherent 快照，不代表「最新」
- **发版方式：推 tag，由 CI 建 Release 并挂产物**

  ```bash
  git tag -a vX.Y.Z -m "vX.Y.Z — 一句话主题"
  git push origin vX.Y.Z
  ```

  `.github/workflows/release.yml` 先复用 `verify.yml` 的全部门禁（不在红的提交上发版），
  再 `python -m build` 产出 **sdist + wheel** 挂上去；notes 优先读 `release-notes/<tag>.md`。
  **不要手跑 `gh release create`** —— 它会与 CI 的创建步骤抢跑，且**失败是静默的**（产物缺失但不报错）。
  完整说明见根 README 的「发布」一节

## 插件独立（各 .claude-plugin/plugin.json）

| 插件 | 当前版本 | 说明 |
|------|---------|------|
| code-security-skills | 1.5.1 | `claude plugins install` 更新追踪，独立 semver |
| dev-workflow | 2.0.2 | 同上（2.0.0 = 四技能合并为 dev-workflow，破坏性） |
| superpowers | —（fork） | junction 加载，不独立发版；「6.2.0-local」是上游基线标识 |

- bump 时机：该插件 skills 变化时（加 skill / 大改 = minor，修 bug / 小改 = patch）
- 根 release 是快照，捕获当时各插件状态；插件改了只 bump 插件，根不动

## bump 策略

| 改了什么 | bump 哪个 |
|---------|----------|
| 某个插件的 skills | 那个插件的 `plugin.json` |
| bin 脚本 / 发整仓 release | 根 `pyproject.toml` |
| 两个都改 | 两个都 bump |

## 防失配

改插件 skills 时，**同步**它的 README changelog + `plugin.json` version，别只改一个（code-security-skills 曾 plugin.json 1.3.1 vs changelog 1.4.0 失配）。`dev-workflow` 技能的 release 场景会提示检查。
