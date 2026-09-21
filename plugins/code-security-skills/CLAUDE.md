# Code Security Skills

Claude Code 插件，提供系统化的代码安全审计能力。

## 包含的技能

| 技能 | 触发方式 | 功能 |
|------|----------|------|
| `code-security-audit` | "audit this repo", "安全审计" 等 | 4 阶段系统安全审计（探索→验证→报告→重审计） |
| `security-fix-skill` | "/security-fix", "修安全漏洞" | 按优先级批量修复审计发现（只处理 `VERDICT=confirmed`） |

`audit` / `reaudit` / `review-skill` 已于 2026-09-12 合并归档（见仓库根 `archive/`）：
`audit` 与 `reaudit` 是 `code-security-audit` 的 Phase 1-3 与 Phase 4，拆成同级技能只会让触发词互相抢命中；
`review-skill` 合并进 `dev-workflow`。**不要再引用这三个名字。**

## 技能依赖

```
code-security-audit
  ├── Phase 1-3  探索 → 验证 → 报告      （/audit 入口）
  └── Phase 4    增量重审与状态追踪      （/reaudit 入口）
security-fix-skill → 修完后回 code-security-audit Phase 4 的 mark-fixed
```

## 认识态与修复态（两条正交轴）

每条 finding 的注解带 `VERDICT`（认识态）与 `STATUS`（修复态）：

- `VERDICT=confirmed`（缺省）/ `needs-validation` / `rejected`
- **只有 `confirmed` 允许带 `SEVERITY`** —— 不确定就不许定级
- `STATUS` = `open` / `fixed` / `deferred` / `not-fixed` / `partial`

契约规范见 `skills/code-security-audit/references/vulnerability-patterns.md` §18；
执行者是仓库根的 `bin/security_audit_tools.py validate`（已接入 CI）。

## 迭代指南

- 新增漏洞模式：编辑 `skills/code-security-audit/references/vulnerability-patterns.md`，
  **并同时在「不算 Finding 判别表」补一行排除条件** —— 没有排除条件的模式是误报来源
- 新增攻击面（AI/供应链/桌面 IPC/资源耗尽/数据隔离）：编辑
  `skills/code-security-audit/references/attack-surfaces.md`（懒加载，不要并入主流程三域）
- 修改审计流程：编辑 `skills/code-security-audit/SKILL.md` 与其 `references/`
- 改注解字段或校验规则：`bin/security_audit_tools.py` + `tests/test_bin_contracts.py`
  必须同步（契约测试是这套注解的唯一回归保护）
- 所有技能通过 `name` 字段互相引用，不需要文件路径；引用已归档技能会被
  `bin/check_skills.py --strict` 拦下
