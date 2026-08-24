# Superpowers — 本地改版说明（科研骨架 fork）

> 本目录是 superpowers 的个人 fork（永不更新上游，原版 MIT 可自由修改）。
> **上游贡献者指南不适用**——不向 prime-radiant-inc 提 PR。本文件替代原贡献指南。

## 定位

科研骨架的 skill 载体。17 个 skill = 13 上游 + 4 自定义：

- **figure-drawing** — 论文制图工作流（gpt-image-2 → vision → draw.io XML → 验证）
- **paper-reading** — 论文阅读（A 搜索 / B 防撞车 / C 快速读 / D 精读 / 六节模板）
- **office-tools** — Office 写作（pandoc md→docx/pptx，Excel，提图）
- **paper-writing** — 论文写作一条龙（venue 选模板 → 模块化写作 → 编译页数检查）

## 约定

- **新 skill 按科研骨架设计语言写**：场景判定表（先判深度再走流程）+ 自进化日志 + 跨模型验证 + 边界。参考 figure-drawing / paper-reading 的 SKILL.md 结构
- **不覆盖/不改写上游已调优内容**（Red Flags 表、rationalization 清单、"human partner" 措辞）除非有实战证据改进
- **skill 改动流程**：`superpowers:writing-skills` 起草 → 实战验证（如 paper-reading 的 GREEN 验证）→ 自进化日志记录
- **工具脚本在仓库根 `bin/`**（vision.py / review.py / office_tools.py / latex_build.py / security-audit-tools.py / style_reference_docx.py）；`pip install -e .` 后可作 console 命令调用（review / vision / office-tools / latex-build / ...，不依赖 junction）

## 相关

- 科研骨架全景与工具：上级仓库（agent-useful-skills）README + skeleton.md（全貌索引）
- 上游原版：github.com/prime-radiant-inc/superpowers（作参考，不更新）
