# Re-audit 模式与状态追踪（Phase 4）

本文件是 `code-security-audit` 的 Phase 4 展开。原先 `/reaudit` 是独立技能，2026-09-12 合并回本技能
（审计与重审是同一工作流的两段，拆成两个同级技能只会让"再审计/检查修复"误命中完整四阶段审计）。

## 四种模式

| 命令 | 动作 | 读文件？ |
|------|------|---------|
| `/reaudit` | 完整增量重审（Phase 4） | 仅变更文件 |
| `/reaudit mark-fixed <ID>` | 轻量：标记 finding 已修复 | 否 |
| `/reaudit mark-deferred <ID> [--reason "文本"]` | 轻量：标记结构性延期 | 否 |
| `/reaudit status` | 修复进度汇总 | 否（只扫注解） |

---

## Mode 1: 完整重审（`/reaudit`）

1. **解析状态注解** — 扫报告里的 `<!-- AUDIT:STATUS=... -->` 行，取每条 finding 的
   `FILE` / `LINES` / `STATUS`。
2. **先做祖先性检查（必做）** — 注解里的 audit commit 可能已被 rebase/squash 掉：
   ```bash
   git merge-base --is-ancestor <audit-commit> HEAD && echo OK || echo REWRITTEN
   ```
   不是祖先 → **历史被重写过**：`git diff <audit-commit>..HEAD` 会返回一堆无关文件
   （本仓库实测过：返回 151 个路径，全是噪音）。此时**跳过 diff-filter**，声明历史已重写，
   直接全量重验并重新建立基线（写入新的 audit commit）。
3. **Diff-filter** — 只有 `FILE` 出现在 `git diff --name-only <audit-commit>..HEAD` 里的
   finding 需要重验。
   > ⚠️ `FILE` 必须与 `git diff` 输出**同一基准**。规范是**仓库根相对 POSIX 路径**
   （正斜杠、无 `./` 前缀）。若审计目标只是某个子目录，报告里每个 `FILE` 都要带该子目录前缀，
   否则匹配不上（会静默判为「未变更」而跳过——安全工具里这是漏报来源）。
   > 另：`FILE` 在 HEAD 处不存在时，按**已变更**处理并标记为 stale 路径。
4. **重验变更文件的 finding** — 读回源码核对：
   - 修复到位 → `STATUS=fixed COMMIT=<hash>`
   - 仍可利用 → `STATUS=not-fixed`
   - 部分解决 → `STATUS=partial`
5. **未变更文件的 finding 保持原状** — 不重读、不改 STATUS。
6. **查回归** — 扫 diff 新增行里是否引入新的漏洞模式。
7. **写重审段** — 结构见 `references/audit-report-template.md`。

---

## Mode 2: mark-fixed（`/reaudit mark-fixed <ID>`）

轻量状态更新，不读文件。提交修复后用。

1. 在报告里定位含该 ID 的 `<!-- AUDIT:STATUS=... -->` 行
2. 若 `STATUS=open` / `not-fixed` → 改为 `STATUS=fixed COMMIT=<当前 HEAD>`
3. 若已是 `fixed` → 提示但允许更新 commit
4. 若 `STATUS=deferred` → 提示用户确认延期理由已不成立

支持多个 ID：`/reaudit mark-fixed SSRF-1 PATH-1 AUTH-1`

---

## Mode 3: mark-deferred（`/reaudit mark-deferred <ID> --reason "文本"`）

用于短期不会修的结构性 finding（TLS、keychain、架构调整）。

1. 更新注解为 `STATUS=deferred`，并把 `--reason` 写进注解的 `REASON="..."` 字段
   （原因里的双引号会被换成单引号以保持注解可解析）
2. finding 留在报告里，延期状态与原因可见

---

## Mode 4: status（`/reaudit status`）

不读文件的进度概览：

1. 扫所有 `AUDIT:STATUS=` 注解
2. 按状态与严重度计数，输出：

```
  Status      Count
  ─────────   ─────
  fixed       5
  open        1
  deferred    1
  ─────────   ─────
  Total       7     (71% fixed)
```

有 `not-fixed` / `partial` 时逐条列出 ID 与严重度（**不要只输出三种状态**——那样
`partial`/`not-fixed` 会被静默吞掉）。

---

## 状态注解格式

```markdown
### SSRF-1 — tool_fetch_url navigates to unvalidated URL
<!-- AUDIT:STATUS=open SEVERITY=high FILE=src/module.py LINES=100-120 -->
```

字段：`STATUS` / `SEVERITY` / `FILE` / `LINES` / `COMMIT`（可选）/ `REASON`（可选）。
完整字段规范见 `references/vulnerability-patterns.md` §18。

## 用脚本做状态管理（推荐，替代手动 grep/Edit）

```bash
security-audit-tools list [--status open] [--severity high] [--json]
security-audit-tools status
security-audit-tools diff-filter --commit <上次审计hash>
security-audit-tools mark-fixed SSRF-1 PATH-1
security-audit-tools mark-deferred SSRF-1 --reason "等上游库修 TLS 默认值"
```

- 脚本在**仓库根** `bin/security_audit_tools.py`，需先 `pip install -e .`（或从仓库根
  `python bin/security_audit_tools.py <子命令>`）
- 报告路径缺省自动探测：cwd 的 `docs/SECURITY_AUDIT.md` → cwd 根 → 本插件 `docs/`
- 找不到报告时退出码 2 并给出提示（不抛 traceback）
- 脚本不可用时，退回手动 grep/Edit 注解——**契约不变**，仍是那几个字段
