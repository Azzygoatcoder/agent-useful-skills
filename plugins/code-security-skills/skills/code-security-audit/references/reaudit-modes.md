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
5. **未变更文件的 finding** — 不重读，但**"文件没变"不等于"结论仍然成立"**：
   - 修复可能落在**别的文件**（共享工具里加了 guard，或换了调用方）→ 本条 `FILE` 没变，
     结论却已过时，`fixed` 会永远认不出来。因此对 `open` / `not-fixed` / `partial` 的
     finding，额外扫一遍 `git diff <audit-commit>..HEAD` 的**新增行**，找 remediation
     里描述的那个 guard —— 而不是只看 `FILE` 是否落在变更集里。
   - 其余保持原 STATUS，但**必须在重审段的「未重验，沿用旧结论」表里逐条列出**
     （见 `references/audit-report-template.md`）—— 静默沿用旧结论是漏报来源。
6. **查回归** — 扫 diff 新增行里是否引入新的漏洞模式。
7. **写重审段** — 结构见 `references/audit-report-template.md`，**含「未重验」表**。

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

1. 扫所有 `AUDIT:` 注解
2. **先按认识态（VERDICT）计数，再按修复态（STATUS）计数**，输出：

```
=== 认识态 (7 findings) ===
  confirmed        6
  needs-validation 1

=== 修复进度 (分母 6，已排除 rejected) ===
  fixed       5
  open        1
  ────────────
  合计        6     (83% fixed)
```

3. 修复进度的**分母不含 `rejected`** —— 已推翻的候选不是工作项，不该拉低百分比。

有 `not-fixed` / `partial` 时逐条列出 ID 与严重度（**不要只输出三种状态** —— 那样
`partial`/`not-fixed` 会被静默吞掉）。

---

## Prior-run 纪律（多轮审计之间）

多轮审计最典型的失败模式，是把上一轮的结论当成这一轮的证据。规则：

| 上一轮状态 | 本轮怎么处理 |
|-----------|-------------|
| `confirmed` + 相关源码/条件**未变** | 可沿用同一 ID 与结论，但**仍须过一遍本轮 Phase 2 验证**（换 agent 复核引用行）。不重复进修复队列 |
| `confirmed` + 相关源码**已变** | **当作新工作重建**，不要在 diff-filter 里跳过 —— 旧结论只说明当时成立 |
| `needs-validation` | 仍缺那个仓库外事实 → 保留 `BLOCKER` 并在本轮再试；**不因为"上轮记过"就跳过** |
| `rejected` | 只抑制**那一条具体断言**（同文件同行同根因）。证据一变就是新工作 |
| `deferred` / `out_of_scope` | 是优先级输入，**不是抑制键** |

**「上一轮记过了」永远不是本轮不覆盖的理由。** `FILE` / `LINES` 指向同一位置，也不代表那条路径仍然成立 —— 必须有本轮的复核记录。

---

## 状态注解格式

```markdown
### SSRF-1 — tool_fetch_url navigates to unvalidated URL
<!-- AUDIT:VERDICT=confirmed STATUS=open SEVERITY=high FILE=src/module.py LINES=100-120 -->

### PROMPT-1 — 检索内容可覆盖系统指令
<!-- AUDIT:VERDICT=needs-validation STATUS=open FILE=src/rag.py LINES=88-104 BLOCKER="线上是否启用工具调用未知" -->
```

字段：`VERDICT`（缺省 `confirmed`）/ `STATUS` / `SEVERITY`（仅 confirmed）/ `FILE` / `LINES` / `COMMIT`（可选）/ `REASON`（可选）/ `BLOCKER`（needs-validation 必填）。
**`VERDICT` 是认识态、`STATUS` 是修复态，两条正交轴** —— `deferred` 是"暂不修"，不是"测不出来"。
完整字段规范见 `references/vulnerability-patterns.md` §18；`bin/security_audit_tools.py validate` 是这套契约的执行者。

## 用脚本做状态管理（推荐，替代手动 grep/Edit）

```bash
security-audit-tools list [--status open] [--severity high] [--verdict needs-validation] [--json]
security-audit-tools status
security-audit-tools validate        # 契约校验：VERDICT/SEVERITY 互斥、FILE 存在、
                                     # LINES 合法、fixed 的 COMMIT 是 HEAD 祖先、报告含 ## Coverage
security-audit-tools diff-filter --commit <上次审计hash>
security-audit-tools mark-fixed SSRF-1 PATH-1
security-audit-tools mark-deferred SSRF-1 --reason "等上游库修 TLS 默认值"
```

- 脚本在**仓库根** `bin/security_audit_tools.py`，需先 `pip install -e .`（或从仓库根
  `python bin/security_audit_tools.py <子命令>`）
- 报告路径缺省自动探测：cwd 的 `docs/SECURITY_AUDIT.md` → cwd 根 → 本插件 `docs/`
- 找不到报告时退出码 2 并给出提示（不抛 traceback）
- 脚本不可用时，退回手动 grep/Edit 注解——**契约不变**，仍是那几个字段
