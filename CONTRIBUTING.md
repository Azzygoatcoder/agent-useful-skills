# Contributing

本仓库是**单人维护**的技能 monorepo。欢迎 issue 和 PR —— 但请先读这一页，因为**这里的契约是 CI 强制的**，
不知道就会拿到一个看不懂的红 CI。

> **本页只是索引，不复述规则。** 每条规则的权威文档在右列；**若本页与它不一致，以它为准** ——
> 重述必然漂移，这一整轮我们都在打这种漂移。

## 第一步：本地跑一遍门禁

CI 的每一步都能在本地原样复现，且**全部离线**（不调 LLM/MCP，不需要密钥）：

```bash
python -m compileall -q bin tests
python bin/check_skills.py --strict          # 最常红的一条
python tests/test_bin_contracts.py
npm install --no-audit --no-fund && node bin/verify-plugin.mjs
python bin/export_diagram.py --check plugins/code-security-skills/assets/audit-workflow.html
python bin/check_external.py
```

完整清单（含 Windows 上的部署校验）与四组合矩阵见 [README](README.md) 的「CI」一节。

## 规则 → 权威文档

| 你要动什么 | 必须先读 |
|---|---|
| 加/改一个技能（`SKILL.md`） | [`skeleton.md`](skeleton.md)（技能创作约定）+ `bin/check_skills.py --strict` 的报错信息 |
| 技能放在哪、要不要注册 | [`skills.manifest.json`](skills.manifest.json) + README「仓库结构」 |
| 加一个插件 | [`LICENSING.md`](LICENSING.md)（**要另带一份 LICENSE**）+ README「包含的模块」 |
| 改版本号 | [`VERSIONING.md`](VERSIONING.md)（**两层版本**：根快照 vs 插件独立） |
| 引用仓库外的技能 | [`skills.external.json`](skills.external.json)（声明式 + `check_external.py` 可校验） |
| 从别处 fork / 抄内容 | [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md) + [`LICENSING.md`](LICENSING.md) |
| 画配图 | `plugins/*/assets/*.html` 是**唯一图源**，SVG/PNG 由 `bin/export_diagram.py` 派生（CI 校验同步） |
| 发版 | [README](README.md) 的「发布」一节 + [`release-notes/`](release-notes/) |
| 报安全问题 | 走 [`SECURITY.md`](SECURITY.md)，**不要**开公开 issue |

## 三条最容易踩的

这几条会产生**看不懂的失败**，所以单独点出来（**一句话索引，细则以上表为准**）：

1. **技能目录必须单层**：`<技能根>/<技能名>/SKILL.md`。参考文件放 `references/`，
   再嵌一层 DSH 就发现不了了 —— `check_skills.py` 会报错。
2. **`description` 有 500 字符上限**（DSH catalog 会截断），且它**就是触发词**：
   写清了才命中，写短了弱模型命中率低。
3. **`## 自进化日志` 是必备段**：技能里吸收的实战教训写在这里，不是写进 commit message。
   归档技能时用 `archive/`（**不要直接删**），并附合并/归档原因。

## 提交 PR

- **标题与说明写"为什么"**，不只是"改了什么"。本仓库的 changelog 一贯写明**取舍**（哪些没做、为什么），
  PR 说明是它的上游
- **说明你跑了哪些门禁**。CI 会再跑一遍，但 PR 里写出来能省一轮
- 改了技能行为的话，说清**你怎么验证的**（在哪个仓库/场景试过）
- 不要顺手改无关文件；这个仓库有配图同步、清单双向一致之类的**跨文件契约**，无关改动会把 CI 弄红

## 我不太会合的东西

- 纯格式化的全仓库重排（diff 噪音 > 收益，且会打断 `git blame`）
- 新增一个和现有技能高度重叠的技能 —— 本仓库刚从 27 个精简到 12 个，
  合并的理由见 [`archive/`](archive/) 里各目录的 `README.md`
- 引入"第二份真相"的结构（例如把审计结论同时写成 Markdown 与 JSON，再写校验器保证两者一致）——
  `code-security-audit` 明确**未采纳**这类设计，理由见其自进化日志

## 许可

贡献即表示同意按本仓库的许可证发布（根 MIT；`plugins/*` 各自另带一份；
fork 来的内容保留上游署名）。见 [`LICENSING.md`](LICENSING.md)。
