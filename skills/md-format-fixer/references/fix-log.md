# Fix Log

本 skill 的实战回写位：每次修完 markdown 后追加一条。写法见 `SKILL.md` 的「自进化日志（The Fix Log）」段。

出现 3 次以上的同类问题，说明是系统性习惯，应当主动提醒用户。

---

### 2026-09-21 — 收编进本仓库

- **Found**: 本 skill 原先只装在 `~/.claude/skills/md-format-fixer`（并软链到 DSH 技能根），作为**外部依赖**由 `skills.external.json` 声明。它被 `plugins/superpowers/skills/paper-reading` 引用，但不在仓库内 —— 于是出现「技能里写着跑 md-format-fixer，换台机器就找不到」的风险；而它其实是本仓库作者自研，不是第三方内容，本不该走外部依赖那条路。
- **Fixed**: 收进 `skills/md-format-fixer/`，加入 `skills.manifest.json` 默认清单，从 `skills.external.json` 移出；`description` 由 532 字符压到 500 以内（DSH catalog 上限，超了会被截断）；补 `references/fix-log.md`（原先正文引用它但文件不存在）。
- **Root cause**: 把「作者自研但不在仓库内」误当成「第三方外部依赖」—— `skills.external.json` 的 `upstreamLicense` 字段名加深了这个误解（该文件里的 external 指**发现路径在仓库外**，与版权归属无关）。
