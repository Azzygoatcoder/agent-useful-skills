# Claude Useful Skills

**模块化 AI 科研/工程技能集合（Claude Code）。** 把「读论文 → 画图 → 写文档 → 安全审计」这些重复任务，沉淀成可复用的 skill + 脚本，每个模块自带验证环。

> 一句话：**LLM 写中间产物 → 脚本固化格式 → 跨模型验证环兜底**。

## 设计原则（为什么这么设计）

| 原则 | 含义 |
|------|------|
| **验证环** | AI 生成的图/内容，用独立的跨模型检查兜底——vision 渲染复核、review 对抗评审。不盲信单次输出 |
| **场景判定 + 自进化日志** | 每个 skill 先判「给谁看、什么深度」，每次实战把教训写回 skill，越用越强 |
| **工具不堆积** | 新工具先问「有没有真正新增的能力」，有才吸收，重复轮子不装 |
| **配置走 env** | 脚本优先读环境变量，兜底 Claude Code 本地设置。**仓库不硬编码任何供应商端点或密钥** |

> **设计灵感**：科研骨架的设计哲学（跨模型评审循环、对抗验证）受 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)（arXiv:2605.03042）启发，未直接使用其代码。详见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。

## 仓库结构（monorepo）

```
claude-useful-skills/
├── plugins/     # 可独立安装的插件（有 .claude-plugin）
│   ├── code-security-skills/
│   └── superpowers/
├── skills/      # 独立 skill（单 SKILL.md，非插件）
│   └── storage-analyzer/
├── bin/         # 共享辅助脚本
└── latex-templates/
```

## 包含的模块

### 插件（`plugins/`）

| 插件 | 版本 | 说明 |
|------|------|------|
| [Code Security Skills](plugins/code-security-skills/) | v1.4.0 | 系统化安全审计：场景分流 → 并行探索 → 深度验证（跨模型对抗）→ 报告 → 增量重审计 + 状态追踪工具 |
| [Superpowers（本地改版）](plugins/superpowers/) | 6.2.0-local | superpowers fork + 科研骨架自定义 skill |

### 自定义 Skills（`plugins/superpowers/skills/`）

| Skill | 用途 |
|-------|------|
| figure-drawing | 论文制图：概念图 / 精确数据图 / 技术架构图 场景分流，vision 渲染验证 |
| paper-reading | 论文阅读：搜索入库 / 防撞车 / 快速读 / 精读（六节模板 + 置信度分级） |
| office-tools | Office 写作：md→docx/pptx（公式转原生方程）、Excel 处理、提图 |
| paper-writing | 论文写作一条龙：venue 选模板 → 模块化写作 → 编译页数检查 |

### 独立 Skill（`skills/`）

| Skill | 用途 |
|-------|------|
| [storage-analyzer](skills/storage-analyzer/) | 只读磁盘存储分析：三色分级清理决策 + 交互式 HTML 报告（第三方改编，MIT） |

### Helper 脚本（`bin/`）

| 脚本 | 用途 | 依赖 |
|------|------|------|
| vision.py | 识图（Qwen3-VL-32B，OpenAI 兼容） | `LLM_API_URL` + key（env） |
| review.py | 跨模型对抗评审（kill-argument 结构化 JSON，Qwen3.5-397B） | `LLM_API_URL` + key（env） |
| gen-image-mcp.js | 通用生图 MCP server（OpenAI 兼容） | `GEN_IMAGE_URL` / `GEN_IMAGE_PROVIDERS`（env） |
| office_tools.py | Office 处理（Excel / pandoc md→docx/pptx / 提图） | openpyxl + pandoc |
| latex_build.py | LaTeX 模板库管理（new/build/pages） | latexmk + xelatex |
| data_plot.py | 期刊级数据图（样式 / 数据耦合保存） | matplotlib/pandas/numpy |
| security-audit-tools.py | 安全审计报告状态管理 | 标准库 |
| fig2drawio.py | 论文图 → draw.io 复刻 | `LLM_API_URL` + key（env） |
| consistency_check.py | 矢量图一致性检查 | `LLM_API_URL` + key（env） |

## 快速开始

```bash
# 识图（环境变量配好 LLM_API_URL + key）
python bin/vision.py <image_path> "描述这张图"

# markdown → Word（公式转 OMML 原生方程）
python bin/office_tools.py md2docx 笔记.md 报告.docx --toc

# 期刊级数据图（自动双出 pdf+png+csv）
python bin/data_plot.py demo

# 安全审计
#   触发 code-security-audit skill，或直接用 /audit
```

## 安装

### 插件

```bash
claude plugins install https://github.com/<your-org>/claude-useful-skills --path code-security-skills
```

### Skills

`superpowers/skills/` 下的 skill 复制或符号链接到 `~/.claude/skills/`：

```bash
# macOS / Linux
ln -s "$(pwd)/superpowers/skills/paper-reading" ~/.claude/skills/paper-reading
# Windows（junction）
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\paper-reading" -Target "$pwd\superpowers\skills\paper-reading"
```

### Helper 脚本

`bin/` 下的脚本可直接 `python bin/<script>.py` 调用，也支持 `pip install -e .` 一键安装为 console 命令（推荐，不依赖 junction）：

```bash
pip install -e .
review file.md           # 跨模型对抗评审（结构化 JSON）
vision img.png "描述"    # 识图
office-tools md2docx a.md b.docx
latex-build list
```

## 密钥配置

脚本优先读环境变量，兜底 `~/.claude/settings.json`（Claude Code 本地设置）：

```bash
export LLM_API_URL="https://api.siliconflow.cn/v1/chat/completions"
export SILICONFLOW_API_KEY="sk-..."
```

## 许可证

[MIT](LICENSE) · 第三方内容归属见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)
