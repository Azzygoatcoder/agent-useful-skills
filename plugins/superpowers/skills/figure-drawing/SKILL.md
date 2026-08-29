---
name: figure-drawing
description: Use when 需要论文级架构图/流程图/示意图。产出可编辑 draw.io 矢量图，支持概念图、数据图和技术架构图。
---

# Figure Drawing — 论文制图工作流

科研骨架的制图模块。目标是产出论文级（DAC/ICML 水准）矢量图。

## 第 0 步：场景判定（先定给谁看，再选路线）

科研制图分场景，**先判定场景，再决定标准和工作流**：

| 场景 | 触发 | 要求 | 标准 | 路线 |
|------|------|------|------|------|
| **A. 内部理解** | 读别人论文精读、理解复杂架构、和 agent 对齐 | **中文可读**、结构清晰、快速、可迭代 | 结构 9/10 就够，设计 7.5 可接受 | **直接画矢量**（deepseek），不用 gpt-image-2 |
| **B. 对外发表** | 自己的论文、投稿/审稿、graphical abstract、封面 | **英文**、设计质量高、严格一致 | 设计系统等价、英文逐字、论文级 | **gpt-image-2 出设计** → 复刻英文矢量 → 一致性检查 |
| **C. 快速示意** | 组会 PPT、临时说明 | 最快、看懂就行 | 能表达即可 | mermaid 或直接画 |
| **D. 数据图** | 精确数据/实验结果（折线/柱状/散点/误差棒） | **数据准确**、可复现、期刊样式 | 数值与数据一致 + 视觉达标 | **代码驱动**（pandas/matplotlib，`bin/data_plot.py`） |

> 例：LLSM 架构图 = 场景 A（读别人论文做理解图）→ 中文、直绘、不 gpt-image-2 是对的。

> **场景 B 补位（2026-08-11）**：对外英文结构化图，尤其 **sequence/state/ER/loop/radar/swimlane** 等 draw.io 不擅长的类型 → 优先走独立 skill **diagram-design**（27 类型编辑器级，HTML+SVG 直绘，SVG 直接进 LaTeX `\includegraphics`）。draw.io 场景仍用本 skill 时，套用"编辑级别设计系统"当自查表。
>
> **技术/Agent 架构图补位（2026-08-12）**：Agent/多智能体/系统架构图 → **fireworks-tech-graph**（语义形状：LLM=双边框圆角矩形、Agent=六边形、向量库=环柱体；Agent/记忆/RAG 领域模式内建；SVG 结构校验→PNG 视觉回读→定向修订的有界验证环）。与 diagram-design（editorial 排版）和 drawio（可编辑）定位不重叠——它专攻技术语义图。

> **工具不堆积原则（2026-08-12）**：制图模块每个工具只占一个明确生态位（概念图=gpt-image-2 / editorial 图=diagram-design / 技术架构图=fireworks-tech-graph / 数据图=data_plot.py / 可编辑矢量=drawio）。新 skill 先判断：**有新东西才吸收，重复轮子不安装**——只把真正新增的能力/模式并进来，不平行堆工具。

## 核心工作流（5 步）

1. **gpt-image-2 生成概念图**（按需，看选路规则）— 用 generate_image MCP（默认 provider）或详细 prompt。适合示意/机制/封面。
   - prompt 用 PDCF 结构：**类型 + 内容逻辑 + 风格hex + 负面限制**（白底/扁平/≤3-4色组/无3D）
2. **提取显式规格（透明化，防黑盒）** — 用 Qwen3-VL 输出**完整结构 JSON**：所有节点/框（含**逐字英文文本，绝不翻译/改写/简化**）、箭头/连线（谁到谁+标签）、布局、视觉元素（图标/圆底数字等）。**规格先展示给用户确认**，缺什么提前指出——把"vision 读→写 XML"的黑盒变成可检查的显式规格
3. **构造带样式 draw.io XML** — 按下方 XML 约定写 `.drawio`（本 skill 自带规范）。**严格英文逐字复刻**（主流论文是英文，不翻译）。从规格构造，规格里有什么就画什么，不自行增删
4. **验证（布局）** — 用 drawio MCP 导出 PNG（`start_session` → `load_diagram` → `export_diagram`；本机装了 draw.io CLI 也可 `draw.io --export --format png`）→ `vision` 命令检查文字/布局/结构
5. **✅ 一致性检查（必做，防丢失）** — 把【原图 gpt-image-2 产物】和【矢量图导出 PNG】**同时**喂给 Qwen3-VL，显式要求：
   > "图A是原图，图B是矢量复刻。严格对比，逐条列出图B相比图A丢失/简化/改变的元素，重点关注文字省略、结构缺失、术语丢失。不要因为图B整洁就忽略差异。"
   有差异 → 修 `.drawio` → 重导 → 复检，直到差异最小化。

## 论文级标准

- 3 模块分色（≤3-4 色组）+ 图例
- 逻辑递进（问题→方法→部署/应用）
- 标注完整：模块名、子系统、关键指标、阶段编号
- 一图讲清叙事，不只是静态节点

## 设计细节（按需加载）

- **draw.io XML 约定 + 编辑级设计系统**：→ [references/drawio-design.md](references/drawio-design.md)
- **D 精确数据图（代码驱动）**：→ [references/data-plot.md](references/data-plot.md)
- **gpt-image-2 选路 / 设计语法 / Prompt 工程 / 提上限模式**：→ [references/prompt-design.md](references/prompt-design.md)

## 验证分工

- **布局/可读性** → vision.py 打分（目标 ≥8.5）
- **语义正确性** → review.py（可选，ARIS 对抗评审）
- 争议以项目文档为准（review 可能过度理论化）

## 自进化日志

每次从参考图/实践中吸收设计模式，记录于此，skill 随之进化：

| 日期 | 学习来源 | 吸收的模式 |
|------|---------|-----------|
| 2026-08-03 | 3 张参考图（EDA方法/TurnOPD/ChipMATE） | 叙事逻辑（问题→方法→验证）、多元素整合、主题色+2-3辅助色、视觉层级、图例清晰 |
| 2026-08-03 | gpt-image-2 复刻实践 | ①透明化：先提取显式规格给用户确认 ②严格英文逐字（不翻译） ③一致性检查必做（原图+矢量同喂 vision 显式找差异）④XML HTML 转义 |
| 2026-08-03 | 用户战略 | 设计是论文差异化价值；目标=设计系统等价（配色/构图/层级），非像素复刻；分层媒介（主体矢量+少量像素） |
| 2026-08-03 | 直接画vs gpt-image-2 对比 | gpt-image-2 地位=设计质量提供者（deepseek 直接画结构9/设计7.5）；选路规则：设计价值>成本才用 gpt-image-2 |
| 2026-08-03 | 用户场景化思考 | **分场景制图**：A内部理解（中文/直绘/结构够）/ B对外发表（英文/gpt-image-2设计/论文级）/ C快速示意。先判场景再选路线 |
| 2026-08-03 | **LLSM 控制变量实验**（直绘 vs gpt-image-2，同素材同英文，第三方盲评） | **结构化图直绘 > gpt-image-2 复刻**（9.5vs7，布局9vs6）。修正：gpt-image-2 只用于示意/概念/封面；结构化图直绘。另：一致性检查模型会幻觉误报（报"缺失"实则在），需单图细读交叉验证 |
| 2026-08-03 | 制图 prompt 工程调研 | **写规格不写描述**：六大要素+几何形态语义映射（数据=平行四边形/算法=矩形/决策=菱形/结论=圆角）+三色域/80-20配色+两种字号+`Do not simplify`强化句 |
| 2026-08-03 | 提上限模式设计 | **理解深度决定 prompt 上限**（L1定位/L2结构/L3机制/L4设计洞察）。提上限=深读原文→6问框架提炼洞察→三部分 prompt（意图/结构/系统）。**隐喻定稿人参与**（AI 给候选，人把关上限） |
| 2026-08-03 | **提上限模式首个成功案例**（CircuitFusion） | 隐喻=三棱镜分光谱（白光→三色光→全光谱），gpt-image-2 画出顶会级 graphical abstract，vision 验证隐喻+结构全对。工作流 5 阶段端到端跑通。附带：502 自动切备用端点（多端点救场） |
| 2026-08-11 | 吸收 diagram-design（5.4k⭐） | 编辑级别设计系统进 draw.io 自查：反 AI-slop 清单（禁阴影/对角连线/圆角>10px/强调>2处/图例漂移）+ 节点语义→填色描边表 + 连接线硬规则（正交直角 r=8/标签遮罩 6-10px/连接点沿边≥12px 展开/穿盒虚线例外）+ 4px 网格 + 复杂度预算≤9节点。**场景 B 对外结构化图 → diagram-design skill 补位**（sequence/state/ER/loop/radar，SVG 直进 LaTeX） |
| 2026-08-12 | 数据图模块落地 | **D 数据图场景**：数据→代码→渲染（AI 不能画数据图，值必须来自数据）；`bin/data_plot.py`（期刊样式 pub_style + 数据耦合 save_fig + demo 实测通过）；vision 渲染检查循环（图例/截断/溢出/配色）；投稿前升 PGFPlots 接 LaTeX。MatPlotAgent 模式参照 |
| 2026-08-12 | fireworks-tech-graph 集成 | **技术/Agent 架构图补位**：语义形状（LLM 双边框/Agent 六边形/向量库环柱）+ 14 类 + 有界验证环（SVG 结构校验→PNG 视觉回读→定向修订≤2轮）。实测 CareRuler 培训 agent 架构图 vision 全过。**工具不堆积原则**：每个工具一个明确生态位，新东西吸收提取、重复轮子不安装 |
| 2026-08-13 | 开源 repo 配图 dogfooding（claude-useful-skills） | **README/文档图是场景 B 之外的缺口**（对外但非论文、术语英文受众可中文）：结构化图仍走直绘 + 编辑设计系统，标签英文（术语保留英文）。**导出走 drawio MCP**（start_session→load_diagram→export_diagram 出 PNG），本机 draw.io CLI 未装；`.drawio` 入库作可编辑源 + `.png` 引用。实测 2 张图（验证环 9.5 / 论文一条龙 9/10）vision 全过 |
| 2026-08-13 | diagram-design dogfooding（dev-workflow push 权限 flowchart） | 3 个摩擦：①first-run style-guide gate 对无品牌项目偏重（默认 rust 色，只能 proceed-default）②4px 网格（字号整除 4）与 typography 规范（9px sublabel / 7-8px eyebrow）自相矛盾 ③flowchart 形状即语义，底置图例冗余。另：SVG 用 rsvg-convert 光栅化后字体回落但可读（vision 9/10） |

## 工具

- 生图：`generate_image` MCP（OpenAI 兼容，provider 由 env 配置）
- 读图：`vision.py`（Qwen3-VL-32B，SiliconFlow）
- 导出：drawio MCP（`start_session` → `load_diagram` → `export_diagram` 出 PNG）；draw.io CLI（`draw.io --export --format png`，本机未装，以 MCP 为准）
- 评审：`review.py`（可选）
- 数据图：`bin/data_plot.py`（pandas/matplotlib 期刊样式 + 数据耦合保存 + 演示）
