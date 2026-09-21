# Third-Party Notices

本仓库包含或借鉴以下第三方开源内容，均保留原作者许可与署名。

三类要分清：**①设计来源**（受其启发，未使用其代码）／**②随本仓库分发**（改自上游或含上游内容）／**③外部依赖**（不随本仓库分发，仅声明依赖）。

---

## ① 设计来源（未直接使用代码）

### cloudflare/security-audit-skill

- **来源**: [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill)（MIT License，Copyright (c) 2025-2026 Cloudflare, Inc.）
- **吸收的设计模式**：审计结论的三态认识论（`confirmed` / `needs-validation` / `rejected`，**不确定就不许定级**）、每类模式自带「不算 Finding」排除条款、报告必须声明**覆盖率与未审计面**、**发现者不得复核自己**的独立性规则、重审前先做**祖先性检查**、重放攻击式的「留档被推翻的候选以免下轮重打」
- **明确未采纳**：`findings.json` + JSON Schema + 两个约 30 KB 校验器（合计约 132 KB）、覆盖率账本 JSON 与 canonical `coverage_id`、11 步 artifact promotion、OS 沙箱前置、10 份域伴读（约 170 KB）。理由：那套面向「全公司舰队 + 不受信目标代码 + CI 产品」，本仓库的威胁模型是「在已受信的仓库里做审计」——取舍记于 `plugins/code-security-skills/skills/code-security-audit/SKILL.md` 的自进化日志
- **说明**: `code-security-audit` 在设计哲学上受其启发，**未使用其代码**；三态注解、判别表、覆盖率段、独立性规则、`validate` 均为自研实现

### ARIS

- **来源**: [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)（arXiv:2605.03042，Markdown-skill 自主科研系统）
- **吸收的设计模式**: 跨模型评审循环（review.py 对抗评审）、kill-argument 承诺式攻击验证、idea discovery 理念
- **说明**: 本仓库的科研骨架（论文阅读 / 制图 / 写作 skill）在设计哲学上受 ARIS 启发，**未直接使用其代码**；核心模式（验证环 / 场景判定 / 自进化日志）是自研实现

---

## ② 随本仓库分发

### storage-analyzer

- **来源**: [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills)（AI Skills 合集，MIT License）
- **原功能**: 扫描 macOS/Windows 整机磁盘，三色分级给清理决策，网页一键移废纸篓
- **本仓库的修改**: Windows 实测与修复（scan.py UTF-8 输出、`/tmp`→`$TEMP` 路径适配）、对齐科研骨架设计语言（自进化日志）、迁移至本仓库管理
- **许可证**: MIT（遵循上游）

### superpowers

- **来源**: [obra/superpowers](https://github.com/obra/superpowers)（原 prime-radiant-inc/superpowers，已迁移；MIT License）
- **本仓库的修改**: 本地 fork（永不更新上游），新增 figure-drawing / paper-reading / office-tools / paper-writing 四个自定义 skill
- **许可证**: MIT（遵循上游）

### diagram-design（用其设计系统产出的图随本仓库分发）

- **来源**: [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)（**MIT License**，Copyright (c) 2025 Cathryn Lavery）
  > 2026-09-21 更正：此前本文件写作「Apache-2.0 / MIT」。按其 `LICENSE` 与 `.claude-plugin/plugin.json` 核实为**纯 MIT**，无误导性的双许可。
- **随本仓库分发的是什么**: `plugins/code-security-skills/assets/` 下的 `audit-workflow.*` 与 `verdict-model.*` 是**自绘**图形 —— 依其设计系统绘制（语义色角色、字号阶梯、SVG 连接线六条硬规则、无障碍 SVG 契约），并使用其 `self_check.py` / `verify-geometry.py` 在产出前校验
- **未使用其打包素材**: 我们的 SVG 全部自绘、内联、无外部图片，**未引用**其 `primitive-icons` 中的 Tabler Icons（MIT）、Simple Icons（CC0-1.0）、log-z/logos（MIT）素材 —— 因此**无需转承**这三项许可。这一点经检索确认（assets 下无 icons / tabler / simple-icons / logz 引用）
- **设计系统模式**亦被吸收进 `superpowers/skills/figure-drawing` 的自查清单，该 skill 内已注明出处
- **许可证**: MIT

---

## ③ 外部依赖（不随本仓库分发）

这些由 `skills.external.json` 声明，`bin/check_external.py` 跨根查找并校验；找不到时 `redeploy-skills.ps1` 会跳过并提示。

> **注意「external」≠「第三方」。** `skills.external.json` 里的 external 指「不在本仓库内、需跨根查找」，与版权归属无关。
> 2026-09-21：原先按 external 列在此的 **`md-format-fixer` 实为本仓库作者自研**，已收进 `skills/md-format-fixer/`，故从本文件与 `skills.external.json` 一并移出 —— 它是自研内容，本就不该出现在第三方说明里。

### fireworks-tech-graph

- **来源**: 本地副本 `G:/AI4Application/fireworks-tech-graph`，其 git remote 指向 [ninehills/fireworks-tech-graph](https://github.com/ninehills/fireworks-tech-graph)；该仓库 README 内又指向更上游 [yizhiyanhua-ai/fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph)
- **用途**: 技术/Agent 架构图 —— 7 视觉风格 / 14 图类型 + 完整 UML，输出 SVG（可经 `rsvg-convert` 导 PNG）；被 `figure-drawing` 引用
- **许可证**: MIT（Copyright (c) 2025 fireworks-tech-graph contributors）

### wiretext（可选，本机未安装）

- **来源**: 未找到公开仓库。公开可查的身份是“**Wiretext: Figma, but everything is text**”这一文本线框图工具（作者 Daniel Howells）—— 见 [Product Hunt](https://www.producthunt.com/products/wiretext) 与 [gihyo 报道](https://gihyo.jp/article/2026/02/text-based-wireframe-tools)
- **用途**: 快速文本/unicode 线框图，是 diagram-design 自己推荐的轻量替代；**不是本仓库技能的硬依赖**（未安装时 diagram-design 自身用法不受影响）
- **许可证**: **未知** —— 未找到公开仓库与许可声明。本机未安装、未使用，因此不涉及分发
