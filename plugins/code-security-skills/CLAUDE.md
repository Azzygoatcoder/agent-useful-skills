# Code Security Skills

Claude Code 插件，提供系统化的代码安全审计能力。

## 包含的技能

| 技能 | 触发方式 | 功能 |
|------|----------|------|
| `code-security-audit` | "audit this repo", "安全审计" 等 | 4 阶段系统安全审计（探索→验证→报告→重审计） |
| `audit` | `/audit` | 快捷入口，委托到 code-security-audit Phase 1-3 |
| `reaudit` | `/reaudit`, "再审计" | 快捷入口，委托到 code-security-audit Phase 4 |
| `security-fix-skill` | "/security-fix", "修安全漏洞" | 按优先级批量修复审计发现 |

## 技能依赖

```
code-security-audit (父技能)
  ├── audit (→ Phase 1-3)
  ├── reaudit (→ Phase 4)
  └── security-fix-skill → reaudit → code-security-audit Phase 4
```

## 迭代指南

- 新增漏洞模式：编辑 `skills/code-security-audit/references/vulnerability-patterns.md`
- 修改审计流程：编辑 `skills/code-security-audit/SKILL.md`
- 所有技能通过 `name` 字段互相引用，不需要文件路径
