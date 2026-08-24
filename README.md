# Agent Useful Skills

**模块化 AI 科研/工程技能集合（Claude Code / DeepSeek Harness 通用）。** 把「读论文 → 画图 → 写文档 → 安全审计」这些重复任务，沉淀成可复用的 skill + 脚本，每个模块自带验证环。

> 一句话：**LLM 写中间产物 → 脚本固化格式 → 跨模型验证环兜底**。

> 全貌索引（模块→skill→脚本→验证方式）：见 [skeleton.md](skeleton.md)。

<p align="center">
  <img src="assets/verification-loop.png" width="600" alt="Verification Loop"/>
</p>

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
agent-useful-skills/
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
| check_skills.py | 校验全部 SKILL.md 是否符合 DSH/AgentSkills 规则（name/description/单层发现/运行时耦合） | 标准库 |
| redeploy-skills.ps1 | DSH 技能链接部署/自愈/校验（Windows junction / POSIX symlink，`-Check` 只读模式） | pwsh 7 |

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
claude plugins install https://github.com/<your-org>/agent-useful-skills --path code-security-skills
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

### DeepSeek Harness（DSH）接入

本仓库 skills 兼容 DSH（Agent Skills 标准运行时，本机已验证全部技能可注册）。DSH 只识别**单层**技能目录 `<技能根>/<技能名>/SKILL.md`，插件内技能需**逐个**建 junction（不要把整个 `skills/` 目录链过去）：

```powershell
# 用户级技能根：~/.dsh/skills（所有会话）；项目级：<工作区>/.dsh/skills
New-Item -ItemType Junction -Path "$env:USERPROFILE\.dsh\skills\paper-reading" -Target "$pwd\plugins\superpowers\skills\paper-reading"
```

- 校验：`python bin/check_skills.py`（或 `pip install -e .` 后 `check-skills`），确保 SKILL.md 符合 DSH 解析规则
- 自动化部署/自愈（推荐替代手写 junction）：`pwsh bin/redeploy-skills.ps1`（创建缺失链接、清理失效链接）；`-Check` 为只读校验（链接完整性 + frontmatter）。支持 `DSH_HOME` / `DSH_SKILLS` 环境变量覆盖目标目录
- ⚠️ 链接部署下，在 DSH 技能管理界面（如 skill-explorer）中**只用启用/禁用，不要用删除**——删除可能级联到链接目标（即仓库真实文件）
- 注意：`subagent-driven-development/scripts/` 下 3 个无扩展名脚本是 bash，Windows 需在 Git Bash / WSL 下运行

## 密钥配置

脚本优先读环境变量，兜底 `~/.claude/settings.json`（Claude Code 本地设置）：

```bash
export LLM_API_URL="https://api.siliconflow.cn/v1/chat/completions"
export SILICONFLOW_API_KEY="sk-..."

# 识图后端一键切换（可选，默认 siliconflow）
export VISION_PROVIDER="sensenova"   # 自动带出 URL + 模型 + SENSENOVA_API_KEY
```

## 许可证

[MIT](LICENSE) · 第三方内容归属见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)
