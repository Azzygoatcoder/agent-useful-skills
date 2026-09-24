# Security Policy

## 这个仓库是什么

`agent-useful-skills` 是一个**技能（skill）monorepo**：面向编码 agent 的指令集（`skills/`、`plugins/`），
加上一组本地 Python 工具（`bin/`）与 LaTeX 模板。它**不是**一个对外提供服务的应用。

因此这里的"漏洞"通常不是经典的 RCE/注入，而是**让 agent 做错事**：

## 在范围内

| 类别 | 例子 |
|------|------|
| **bin 脚本** | `bin/*.py`、`bin/*.mjs` 的命令注入、路径穿越、越界读写、选项注入（把用户/报告数据当参数传给子进程） |
| **技能指令本身** | 某个 `SKILL.md` 的措辞会让 agent 执行危险动作（读任意路径、跑不受信命令、把仓库内容当指令） |
| **供应链** | 依赖解析、`.github/workflows/` 里的信任边界（不受信代码拿到写权限/密钥） |
| **工具给出的假保证** | 最隐蔽的一类：`bin/security_audit_tools.py validate` 之类的校验器**声称**拦住了某件事，实际没拦 —— 用户会因此信任一个不成立的结论 |

## 不在范围内

- **你用本仓库的技能审计出来的、位于别人项目里的漏洞** → 报给那个项目，不要报到这里
- **第三方技能**（`diagram-design` / `fireworks-tech-graph` / `wiretext` 等）→ 报给各自上游；
  它们不随本仓库分发，见 [`skills.external.json`](skills.external.json) 与 [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)
- **`plugins/superpowers/`** 里继承自上游的内容 → 见 [obra/superpowers](https://github.com/obra/superpowers)
- **技能质量**（判断不准、误报多、触发词不好用）→ 那是 issue，不是安全问题，走
  [Issues](https://github.com/Azzygoatcoder/agent-useful-skills/issues)

## 怎么报

**用 GitHub 的私密漏洞报告**（不会公开、不会惊动任何人）：

> 仓库页 → **Security** 标签 → **Report a vulnerability**

请附上：受影响的文件与版本/tag、触发条件、最小复现、以及你认为的影响。
**不要**先开公开 issue。

## 我能承诺什么（说实话）

**单人维护，尽力而为，没有 SLA。** 我会读、会回，但不要期待小时级的响应。

- **支持范围**：滚动维护 `master`；打了 tag 的 Release 是当时快照，修复进 `master`、
  随下一个 tag 发出（发布由 CI 负责，见 [`release-notes/`](release-notes/)）
- **修复策略**：偏保守。这个仓库的产物是**给 agent 读的指令**，改动一个措辞的影响面比改一行代码更难评估 ——
  所以修复可能包含"收窄措辞/加校验/加回归测试"而不是直接改行为
- **披露**：修好后我会在 Release notes 里说明（本仓库的 Release notes 一贯写明取舍，包括**没**做什么）

## 一个自我指涉的提醒

本仓库的旗舰技能是 `code-security-audit`——它自己就要求"报告必须声明覆盖率与未审计面"。
所以如果你报的问题我判断**不在范围**，我会说清是哪一条排除规则挡下的，而不是不吭声。
