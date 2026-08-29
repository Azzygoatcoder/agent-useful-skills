---
name: paper-reading
description: Use when 用户要求读论文、写阅读报告、精读文献、理解某篇工作——触发词"读这篇论文"、"写阅读报告"、"精读"、"paper reading"、"帮我读"、"这篇论文讲什么"。输入为论文 PDF / arXiv / DOI / 链接 / 已有笔记。
---

# Paper Reading — 论文阅读工作流

科研骨架的论文阅读模块。目标：把一篇论文读深读透，产出**符合自家格式、经得起对抗质疑**的阅读报告。

## 第 0 步：场景判定（先定深度，再选流程）

阅读需求不同，深度和产出完全不同。**先判定场景，再走对应流程**：

| 场景 | 触发 | 深度 | 产出 | 状态 |
|------|------|:--:|------|------|
| A. 搜索 | 找新论文 / 调研方向 | L1 | 候选表 + 入库 | ✅ 本轮 |
| B. 防撞车 | 组会前 related work | L1-L2 | 风险分级对比表 | ✅ 本轮 |
| C. 快速读 | 判断是否值得精读 | L1 | 一句话总结 + 定位 | ✅ 本轮 |
| **D. 精读报告** | 正式阅读 / 写报告 | L2-L3 | **六节模板 + 置信度 frontmatter** | ✅ 本轮 |
| E. 深挖对抗 | 跟进 / 定 PRP 方向 | L3-L4 | 脆弱假设 → 反例 → idea | 后续轮 |
| F. 引用审计 | 投稿 / 引用核实 | — | 每条引用三层验证 | 后续轮 |

> 本轮实现 A（搜索入库）+ B（防撞车）+ C（快速读）+ D（精读）。遇到 E/F 触发词，先确认是否真需要精读；不需要就按浅场景快速处理，不强行走 D。

## 场景指南

选择场景后，加载对应详细流程：

- **A 搜索与入库**：自动搜题、多信源、状态机 → [references/scenario-guides.md](references/scenario-guides.md)
- **B 防撞车检查**：定靶心 → 定范围 → 多源搜索 → 风险分级 → 产出 → [references/scenario-guides.md](references/scenario-guides.md)
- **C 快速读**：抓摘要 → 五问定位 → 一句话总结 → 处置三选一 → [references/scenario-guides.md](references/scenario-guides.md)
- **D 精读闭环**：定位抓原文 → 六节报告 → 置信度 frontmatter → 信息卫生 → 批判性验证 → [references/scenario-guides.md](references/scenario-guides.md)

核心不可丢的规则已在场景指南中；主文件只负责分流和索引。

## 自进化日志

每次阅读实践吸收的模式记录于此，skill 随之进化：

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-03 | 初始 17 篇 prp 报告 + RubricsTree 范本 | 六节模板=格式规格；RubricsTree 是唯一完整执行 frontmatter+六节的范本；prp 基线失败=缺 frontmatter、节被合并/删除 |
| 2026-08-03 | ARIS / PaperForge / kill-argument 调研 | 渐进阅读省 context；四类信息卫生映射置信度；承诺式攻击替代平衡弱点清单 |
| 2026-08-03 | CircuitFusion D 闭环首测 | D1 抓原文路径可用（元数据/数字全对上）；**代码链接不在 arXiv abs 页需直接访问 repo 核实**；批判从方法依赖链推导（summary 摘要谁写）；信息卫生落地=推断集中个人体会节；一句话总结设为可选 |
| 2026-08-05 | T²-GRPO GREEN 全量验证 | D 闭环端到端跑通、无需迭代：D1 元数据/数字核对、D3 frontmatter、D4 推断标注（可考虑/推测）、D5 承诺式批判（模拟器保真度循环论证）全部可执行；产出实习模板报告 |
| 2026-08-05 | T²-GRPO 去数学化试验 | **公式策略按受众分**：专业/技术→保留公式+规范 LaTeX（`$...$`/`$$...$$`）；一般组会→去公式抓核心思想（组会分享进度非数学课）。受众判定先于写作，与 figure-drawing 分场景同理 |
| 2026-08-05 | 现有防撞车检查模板（prp/notes） | **B 场景工作流**：定靶心→定范围→多源搜索→风险分级（高/中/低）→产出（分级表/全景矩阵/建议）；撞车判定=任务×方法维度组合全覆盖（非"提到类似词"）；中高风险升 D 精读确认；摘要级≠全文确认 |
| 2026-08-05 | arxiv_fetch.py 实战（A 场景） | **A 场景工作流**：arxiv_fetch.py（search/add/download/status/view）+ 状态机 candidate→fetched→read→report→cited；实战挖出 TACO 新撞车候选（手工漏掉）——自动化信源收集 > 手工检索 |
| 2026-08-05 | 时间线边界讨论 | 撞车时点基准 = 目标投稿 deadline（审稿可见性分水岭）；相似不互相影响三条件：时间错位(concurrent)/贡献点不重叠/上下游互补；灰色带保守当可见处理 |
| 2026-08-06 | DBLP + Semantic Scholar 接入 | arxiv_fetch.py 升级为多信源：--sources arxiv,dblp,semantic + cite(引用数) + bibtex(DBLP 权威)；S2 无 key 优雅降级（429 静默）教训：外部 API 必须有降级路径 |
| 2026-08-06 | S2 key 被拒 → OpenAlex 替代 | S2 个人申请被拒（优先学术/非营利）；OpenAlex 稳定无 key 但**引用数对近期论文滞后**（2025-2026 多 0）；cite=OpenAlex 底 + S2 兜底补当前数；教训：免费引用数对近期论文不可靠，够用即可 |
| 2026-08-06 | PubMed 接入 | `pubmed` 子命令（esearch+esummary 免费）：实习线临床证据源；`--save` 追加 markdown 表；教训：PowerShell GBK 显示乱码≠文件编码错（用 Read 验证 UTF-8）；f-string 表达式不能含反斜杠（3.11 限制） |
| 2026-08-06 | C 场景 GREEN 验证（TACO） | C 端到端可执行：抓摘要→五问→一句话→处置；防撞车中风险候选强制升 D 的判定成立；C5 边界「摘要≠全文」实战有效 |
| 2026-08-06 | D 配图嵌入需求 | D7 配图嵌入：extract 免费滤 + classify 精选 1-4 张重要原图 → markdown 嵌入报告对应章节；报告配原图可读性大增（组会/导师直接见图） |

## 工具

- 定位/搜索：WebSearch（已有）
- 抓全文：WebFetch（arXiv HTML）/ 本地 PDF / alphaxiv LaTeX（公式）
- 入库（可选，后续）：`arxiv_fetch.py`（搜索+元数据+PDF 下载）
- 验证：`review.py`（语义对抗复核）/ `vision.py`（读图表）/ md-format-fixer
