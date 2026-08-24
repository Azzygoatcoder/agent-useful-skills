# Third-Party Notices

本仓库包含以下第三方开源内容，均保留原作者许可与署名。

## ARIS（设计灵感来源，未直接使用代码）

- **来源**: [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)（arXiv:2605.03042，Markdown-skill 自主科研系统）
- **吸收的设计模式**: 跨模型评审循环（review.py 对抗评审）、kill-argument 承诺式攻击验证、idea discovery 理念
- **说明**: 本仓库的科研骨架（论文阅读 / 制图 / 写作 skill）在设计哲学上受 ARIS 启发，**未直接使用其代码**；核心模式（验证环 / 场景判定 / 自进化日志）是自研实现

## storage-analyzer

- **来源**: [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills)（AI Skills 合集，MIT License）
- **原功能**: 扫描 macOS/Windows 整机磁盘，三色分级给清理决策，网页一键移废纸篓
- **本仓库的修改**: Windows 实测与修复（scan.py UTF-8 输出、`/tmp`→`$TEMP` 路径适配）、对齐科研骨架设计语言（自进化日志）、迁移至本仓库管理
- **许可证**: MIT（遵循上游）

## superpowers

- **来源**: [obra/superpowers](https://github.com/obra/superpowers)（原 prime-radiant-inc/superpowers，已迁移；MIT License）
- **本仓库的修改**: 本地 fork（永不更新上游），新增 figure-drawing / paper-reading / office-tools / paper-writing 四个自定义 skill

## diagram-design（不随本仓库分发，仅文档引用）

- **来源**: [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)（Apache-2.0 / MIT）
- 设计系统模式被吸收进 superpowers/skills/figure-drawing 的自查清单，skill 内已注明出处
