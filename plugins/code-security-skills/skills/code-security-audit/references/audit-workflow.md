## Audit Workflow

### Pre-Flight — REQUIRED BEFORE Step 0

BEFORE launching any agent or reading any code, complete these checks. This gate is **unconditional** — do not first decide whether the task "needs" it.

1. **Read `references/vulnerability-patterns.md`** — MUST finish before Phase 1. This is a required read, not a reference to skim later.
2. **Run `git rev-parse HEAD`** — store the audit commit hash for the report header.
3. **Identify the project language/framework** — run `ls *.py *.js *.ts *.go *.rs *.java 2>/dev/null` to probe. Customize agent grep patterns accordingly. If no code files found, ask the user what language the project uses.
4. **Check for prior report** — if `docs/SECURITY_AUDIT.md` exists, read the `**Audit commit:**` field. This feeds Step 0.

Any check skipped = audit validity compromised. If you must skip a check, state which one and why BEFORE proceeding.

### Step 0 — Scope Discovery

Before launching Phase 1, determine the review scope:

1. **Check for a previous audit report** at `docs/SECURITY_AUDIT.md`. If it exists, read the `**Audit commit:** <hash>` field.

2. **If a previous audit exists**, run:
   ```bash
   git diff --name-only <last-audit-commit>..HEAD
   ```
   These are the **changed files** since the last audit. Inject them into each Phase 1 agent prompt as:
   ```
   **Priority files (changed since last audit):** <list of paths>
   Focus 70% of attention on these files; cover the rest at normal depth.
   ```

3. **If this is the first audit** (no previous report), skip this step. All files get equal attention.

### Phase 1 — Parallel Exploration

Launch **3 Explore agents simultaneously** (single message, parallel tool calls). Each agent covers one security domain.

**Agent A: Secrets & Credentials**
Prompt template:
```
Explore the codebase at <path> for security issues related to secrets, credentials, and sensitive data handling:
1. Hardcoded API keys, tokens, passwords in source files
2. .env files, config files that might contain secrets
3. How credentials are stored, accessed, and written
4. Any logging or error messages that might leak sensitive data
5. Check .gitignore — are sensitive file patterns properly excluded?
6. Check git history for accidentally committed secrets
For each finding, assign a stable category prefix:
  SECRET (leaked keys/tokens), DEP (file permissions/temp files)
Report findings with specific file paths, line numbers, and code snippets.

**Confidence annotation — REQUIRED on every finding:**
- CONFIDENCE=high: exploit confirmed by code trace to user input
- CONFIDENCE=medium: pattern matches but reachability unclear from grep alone
- CONFIDENCE=low: suspicious pattern, likely requires context to confirm

CONFIDENCE=low findings MUST still be reported — never suppress them. That filtering decision belongs to Phase 2, not Phase 1.
```

**Agent B: Input Validation & Injection**
Prompt template:
```
Explore the codebase at <path> for security issues related to input validation, injection, and unsafe data handling:
1. Command injection: shell=True, os.system, subprocess with user input in command strings
2. SQL injection if database queries exist
3. Path traversal: user input used in file paths without validation
4. Insecure deserialization: pickle, yaml.load, marshal
5. XSS: innerHTML, document.write, unsanitized user data in HTML context
6. SSRF: user-controlled URLs in HTTP clients without allowlist validation
7. Unsafe eval/exec usage
8. Template injection (SSTI)
For each finding, assign a stable category prefix:
  SSRF (SSRF), PATH (path traversal), CMD (command injection),
  XSS (cross-site scripting), CODE (eval/exec)
Report findings with specific file paths, line numbers, and code snippets.

**Confidence annotation — REQUIRED on every finding:**
- CONFIDENCE=high: exploit confirmed by code trace to user input
- CONFIDENCE=medium: pattern matches but reachability unclear from grep alone
- CONFIDENCE=low: suspicious pattern, likely requires context to confirm

CONFIDENCE=low findings MUST still be reported — never suppress them. That filtering decision belongs to Phase 2, not Phase 1.
```

**Agent C: Auth, Cryptography & Dependencies**
Prompt template:
```
Explore the codebase at <path> for security issues related to:
1. Authentication and authorization: missing auth checks, weak auth mechanisms
2. Cryptography: weak algorithms (MD5, SHA1, DES), hardcoded keys, improper TLS
3. Session management: insecure cookies, missing HttpOnly/Secure/SameSite
4. CSRF protections on state-changing endpoints
5. Dependency security — check ALL of the following:
   a. Unpinned versions, missing lockfile
   b. Run the appropriate command for the project's ecosystem:
      - Python: pip check (detects version conflicts), safety check (known CVEs)
      - Node: npm audit, npx check-for-known-vulnerabilities
      - Rust: cargo audit
      - Go: govulncheck ./...
      - Java: mvn dependency-check:check
   c. If a previous audit report exists, diff the dependency file:
      git diff <last-audit-commit>..HEAD -- requirements.txt package.json pyproject.toml Cargo.toml go.mod pom.xml
   d. Flag new dependencies added since last audit — these need extra scrutiny
6. File permissions: credential files with weak permissions
7. Temp file handling: predictable names, missing cleanup
For each finding, assign a stable category prefix:
  AUTH (missing/weak auth), CRYPTO (weak crypto/TLS),
  DEP (dependencies/file-perms/temp-files)
Report findings with specific file paths, line numbers, and code snippets.

**Confidence annotation — REQUIRED on every finding:**
- CONFIDENCE=high: exploit confirmed by code trace to user input
- CONFIDENCE=medium: pattern matches but reachability unclear from grep alone
- CONFIDENCE=low: suspicious pattern, likely requires context to confirm

CONFIDENCE=low findings MUST still be reported — never suppress them. That filtering decision belongs to Phase 2, not Phase 1.
```

**Category-Prefixed IDs are stable** — they don't shift when new findings are added across audits. Use the prefix table in the report template (Phase 3).

**Customize the prompts** based on the codebase language and framework. Add language-specific patterns (e.g., for Python add `os.popen`, for JS add `eval`, for Go add `text/template` without escaping).

**Fallback: if parallel agents fail.** After launching Phase 1 agents, check how many returned valid findings:
- **3 or 2 valid reports** → proceed normally to Phase 2.
- **1 or 0 valid reports** → parallel launch failed. Immediately launch a **single comprehensive Agent** covering all three domains:

```
Explore the codebase at <path> for ALL security issues across three domains:

Domain A — Secrets & Credentials:
  Hardcoded keys, .env files, credential storage, logging leaks, .gitignore gaps, git history

Domain B — Input Validation & Injection:
  Command injection, SQL injection, path traversal, deserialization, XSS, SSRF, eval/exec

Domain C — Auth, Cryptography & Dependencies:
  Auth checks, weak crypto, session management, CSRF, dependency security, file permissions

For each finding, assign a category prefix (SECRET/DEP, SSRF/PATH/CMD/XSS/CODE, AUTH/CRYPTO/DEP).
Report findings with specific file paths, line numbers, and code snippets.

**Confidence annotation — REQUIRED on every finding.**
Same scale: high/medium/low. Low-confidence findings must still be reported.
```

The comprehensive agent's report replaces the missing parallel reports. Proceed to Phase 2 with whatever results are available.

**Agent D: 设计层与遗漏层（仅 L2/L3 启用）**

前三个 agent 覆盖的是"已知类别的已知模式"。Agent D 覆盖**扫描器抓不到、且不属于任何固定域**的部分。
它独立于前三个 —— 掉线不影响主流程。

```
你不在前三个域里工作。目标是标准清单之外的东西。

**业务逻辑**（扫描器找不到，收益最高）
- 状态机违规：能跳步？能倒退？能重放已完成的流程？第 2 步失败时第 1 步回滚了吗？
- 有业务影响的竞态：双花/双批准/丢失更新 —— 重点是 check-then-act 非原子的操作
- 数值操纵：负数、零、溢出、精度丢失、字符串↔数字隐式转换
- 访问边界：不是"有没有鉴权"，而是"这条业务规则检查对了吗" —— 能否从另一个操作绕过同一效果？
- 隐式信任假设：来自存储/配置/其他组件/插件的值被当作"进来时验过了"。换了条路径写入呢？
- 时间逻辑：过期、调度、速率窗口、时钟偏移；边界时刻与跨组件时区
- 默认与降级：配置缺失、开关关闭、依赖不可用时的安全姿态是什么？

**功能滥用与数据外泄**（合法功能被用于非预期目的 —— 找设计缺陷，不只找代码 bug）
- 导出/备份当外泄：低权用户能否导出超出其权限的数据？含已删除/草稿/历史版本？
- 导入/恢复当注入：能否覆盖既有数据、绕过正常校验、写进无权写入的集合？
- 搜索/过滤/排序当 oracle：能否探测无权访问内容的存在性？按隐藏字段排序能否泄露其值？
- 副作用枚举：错误信息/响应时间/大小/状态码在"不存在"与"无权限"之间有差异吗？
- 预览/草稿/暂存泄漏：预览 token 是否只作用于单个对象？草稿能否被搜索/RSS/sitemap 发现？
- 通知/webhook 当 SSRF：用户能设置服务端去取的 URL 吗？跟随重定向之后呢？

**链式漏洞与信任边界**（单看都合规，串起来就越权）
- 多步边界失败：先画出低权主体能读/写/调用/留存什么，再只把**具体输出**接到后续信任决策上；
  逐个确认前提，不假设下游效果
- 跨组件信任落差：对比 A 保证的与 B 假设的是否一致（截断、类型转换、归一化、租户范围、插件权限）
- 二阶使用：字段名→JSON path、slug→文件路径、已转义文本→原始渲染、存储字符串→URL/正则/模板/策略表达式
- 范围与能力增长：token/key/插件/OAuth/MCP/AI 能力在委派、刷新、缓存、角色变更、组合后变宽 ——
  指出结果主体本不该有的那个**具体操作**
- 回滚与恢复：取消删除、恢复、版本回滚，是否重新施加了**当前**的属主/校验/授权？

**Wildcard —— 没有类别，去找清单之外的东西**
- 这个代码库里**最奇怪的代码**是什么？为什么存在？被滥用会怎样？
- 哪些功能是半成品/实验性/硬加上去的？它们评审最少、安全性最弱
- 界面永远不会发、但 API 允许的调用有哪些？
- 有没有隐藏/未文档化的端点、参数、头、功能？（看路由注册、中间件、配置；含 debug/dev 模式能否在生产被打开）
- 把不打算一起用的功能混起来会怎样？（本地化+预览+缓存；导入+插件+webhook；OAuth+模拟+API key）
- **测试里没有测什么？** 对比开发者想过的边界（有测试）与他们没想到的（没测试）
- 代码对环境做了什么假设？（数据库在本地、时钟准确、DNS 可信、文件系统区分大小写）

**每个 finding 都要走完整路径，不能只报表面现象。** 一个 flag 不是 finding —— 先追影响：
cookie 缺 HttpOnly，先确认它是否承载安全敏感数据、JS 是否按设计需要读它。
```

### Phase 2 — Deep-Dive Verification

After receiving all three agent reports:

1. **Read the flagged files** yourself. Agents provide summaries but you must verify each finding is real.
2. **Filter false positives**. Not everything an agent flags is exploitable. Check context: is user input actually reachable? Is the vulnerable function guarded?
3. **Deduplicate overlapping findings**. Agents A, B, and C may flag the same issue independently. Merge findings that:
   - Share the same file AND lines are within 15 of each other → same root cause
   - Share the same vulnerability category AND same file → likely the same issue
   - Keep the most detailed description; note both agent sources in the merged entry
4. **Run the Finding Self-Check** on every finding BEFORE it enters the report. A finding that fails ANY of these checks is NOT a finding — it is a note or a false positive:

   | # | Check | Fail Action |
   |---|-------|-------------|
   | 1 | Can I trace user input to this code without auth? | No → downgrade severity by 1 level |
   | 2 | Is there a compensating guard within 20 lines? | Yes → document the guard; this is NOT a finding |
   | 3 | Was this confirmed by a DIFFERENT grep/search than the one that found it? | No → mark UNCONFIRMED; do NOT assign above Low |
   | 4 | Can this code path execute in production? | No → informational only; NOT a finding |
   | 5 | Is this a code-quality opinion disguised as a security finding? ("use const", "extract function") | Yes → discard; NOT a finding |

   **Self-Check examples — concrete cases:**

   ```
   CORRECT kill (check 2): Agent flags "subprocess.run(cmd, shell=True)" at line 42.
   Guard at line 38: cmd = shlex.quote(user_input). Check 2 finds the guard → NOT a finding.

   CORRECT downgrade (check 3): Agent flags "pickle.load(open(f))" in a test file.
   Grep found it; no second method confirmed. Check 3 fails → UNCONFIRMED, ceiling = Low.

   CORRECT discard (check 5): "var should be const" → NOT a security finding. Discard.

   WRONG kill: Agent flags "open(user_file)" as path traversal. The agent didn't
   read the allowlist validation 5 lines above. Check 2 SHOULD have caught this.
   ```

4.5 **独立性复核（Critical/High 必做；Low/Medium 推荐）** — 单模型自审会漏掉"过度自信"。

   **规则：找出这条 finding 的 agent，不能是复核它的 agent。** 自己写的自己点头不算验证。

   1. **换 agent 回读源码** —— Critical/High 必须由一个**没参与该条发现**的新 agent 复核。
      它要回读注解 `FILE` / `LINES` 指向的**当前源码**（不是读草稿），逐条判断：trace 的第一个点
      是否真的是低信任入口、最后一个点是否真的是声称的 sink、路径上有没有被忽略的 guard。
      要求它**试着推翻**，而不是确认。
   2. **跨模型对抗** —— 把 finding **连同它引用的源码**交给 `review.py`（不同模型，ARIS 对抗范式）：

      ```bash
      review <finding + 被引用的源码> "这条 finding 成立吗？入口→sink 的 trace 断在哪？漏了哪个 guard？"
      ```

      它的 `strongest_objection`（单一最强拒绝理由）+ `other_weaknesses` 当复核清单逐条回查：
      被批倒且无反驳依据的重新验证；它无法推翻的才保留。
      **注意喂什么**：给 finding + 源码，不是整篇散文草稿 —— 对着文档挑刺的收益远低于对着源码反驳。
   3. **记录复核者** —— 在 finding 正文里写一行 `- **Verified by:** <agent 标识 / review.py 模型名>`。
      没有这一行，Critical/High 不算验证完成。

   **这是 30-40% 误报瓶颈的自动化解法**（替代"全靠人工读代码判断"）。

5. **Assign severity** to each confirmed (and deduplicated) finding:

| Severity | Criteria | MANDATORY ACTION |
|----------|----------|------------------|
| **Critical** | Remote + unauthenticated → secret access OR arbitrary code execution | **BLOCKER**: Must be confirmed by 2 independent methods. Do not proceed to next finding until a verified exploit path is documented. |
| **High** | Authenticated privilege escalation, injection with confirmed data impact | Must include reproduction steps. Single-method detection → downgrade to Medium. |
| **Medium** | Information disclosure, missing hardening, defense-in-depth gaps | Must note whether compensating controls exist within the codebase. |
| **Low** | Best-practice violations with minimal direct risk | Aggregate into one section. Do NOT spend more than 2 minutes verifying per finding. |

NON-NEGOTIABLE: If a finding cannot meet its severity tier's mandatory action, it MUST be downgraded to the next tier where the action is achievable.

6. **Assign a stable category-prefixed ID** to each finding using this table:

| Prefix | Category | Typical patterns |
|--------|----------|------------------|
| `SSRF` | SSRF / URL injection | Unsanitized URL in HTTP client, Playwright navigation |
| `PATH` | Path traversal | `../` in file paths, missing `is_relative_to` |
| `AUTH` | Missing/weak authentication | Unguarded endpoint, missing auth check |
| `CMD` | Command injection | `shell=True`, `os.system`, MATLAB -batch |
| `XSS` | Cross-site scripting | `innerHTML`, unsanitized HTML output |
| `CODE` | Unsafe eval/exec | `eval`, `exec`, `Function()`, dynamic import |
| `SECRET` | Secrets/credentials leak | Hardcoded keys, tokens in logs/URL |
| `CRYPTO` | Weak cryptography | MD5/SHA1, `verify=False`, hardcoded keys |
| `DEP` | Dependencies / files / config | Unpinned deps, missing lockfile, temp files, file perms |
| `STATE` | Shared mutable state | Global state without isolation |
| `META` | 技能/流程自身的元问题 | 报告字段、注解契约、清单与实际不符 |
| `PROMPT` | AI/LLM 上下文与工具授权 | 间接 prompt 注入、记忆投毒、工具参数越权、MCP 标识混淆 |
| `SUPPLY` | 供应链 / CI / 发布 | 依赖解析源混淆、CI 跑不受信代码、构建到发布的标识替换 |
| `IPC` | 桌面 / 移动 / 本地 IPC | 深链歧义、webview origin 漂移、native bridge 越权、本地对端鉴权 |
| `RES` | 资源耗尽 / 可用性 | 超线性解析、解压放大、无界缓冲、取消后仍在跑、配额记账缺口 |
| `TENANT` | 数据隔离 / 生命周期 | 缺租户约束、缓存索引 ACL 漂移、导出范围扩张、软删绕过 |

Number sequentially within each prefix: `SSRF-1`, `SSRF-2`, `PATH-1`, etc.
**新增前缀必须同时加进这张表和 `bin/security_audit_tools.py` 的 `ID_PREFIXES`** —— `validate` 会对表外前缀报错。

7. **判定认识态 `VERDICT`**（每条都要定，缺省 `confirmed`）：
   - `confirmed` —— 源码证据 + 有界本地验证齐全，边界与结果都成立。**只有它能带 `SEVERITY`。**
   - `needs-validation` —— 源码路径成立，但卡在一个**仓库外的事实**上。写 `BLOCKER="缺的那个事实"`，
     **不得给严重度**。
   - `rejected` —— 已被推翻的候选。写 `REASON="理由"` 并**保留在报告里**，以免下轮重打同一枪。

   **不确定就不许定级。** 把"证据不足的严重问题"改写成"证据充分的轻微问题"，是审计里最贵的错误。

### Meta-Cognition Trap — watch for these internal signals

During Phase 2 verification, if you find yourself thinking any of the following, STOP. These are rationalization signals, not valid verification:

- **"This is probably fine in practice"** → That IS the signal to escalate, not dismiss. Probabilities are not verification. Trace the dataflow before closing.
- **"User input will never reach this code"** → Assumption-based dismissal is the #1 source of false negatives. Verify with a concrete code path, not intuition.
- **"The fix is obvious, no need to document it"** → Every finding MUST include concrete remediation code. No exceptions. An undocumented fix is not a fix.
- **"This is just how the framework works"** → Frameworks have CVEs too. Flag it; let the report reader decide.

These are NOT valid reasons to close a finding. When you catch yourself using them, reopen the finding for deeper review.

### Phase 3 — Report Compilation

Write the audit report to an agreed location. Use the exact report template in `references/audit-report-template.md` (report section).

**Annotation format** (the `<!-- AUDIT:... -->` line right after each finding title):

```
<!-- AUDIT:VERDICT=<verdict> STATUS=<status> [SEVERITY=<severity>] FILE=<path> LINES=<span>[,<span>] [COMMIT=<hash>] [REASON="..."] [BLOCKER="..."] -->
```

| Field | Required | Values |
|-------|----------|--------|
| `VERDICT` | 可选，缺省 `confirmed` | `confirmed` / `needs-validation` / `rejected` —— **认识态** |
| `STATUS` | Yes | `open` → `fixed` → `deferred` → `not-fixed` → `partial` —— **修复态** |
| `SEVERITY` | `confirmed` 必填 | `critical` / `high` / `medium` / `low`。**非 confirmed 禁止携带** |
| `FILE` | Yes | 仓库根相对 POSIX 路径（正斜杠、无 `..`、无绝对路径） |
| `LINES` | Yes | `123-145`、单行 `123`，或逗号分隔多段 `475,510` |
| `COMMIT` | On fix | Hash of the commit that resolved this finding |
| `REASON` | `rejected` 必填 | 判定理由 |
| `BLOCKER` | `needs-validation` 必填 | 缺失的那个仓库外事实 |

这条注解支撑轻量 `mark-fixed`（只改这一行）与基于 diff 的增量重审（比对 `FILE` 与 `git diff`）。
**`VERDICT` 与 `STATUS` 是两条正交轴**：`deferred` 是"暂不修"，不是"测不出来"——后者属于 `VERDICT`。
报告还**必须**有非空的 `## Coverage` 段（交代哪些面未审计及原因）。

收工前跑契约校验：`python bin/security_audit_tools.py validate`（VERDICT/SEVERITY 互斥、`FILE` 存在、
`LINES` 不越界、`fixed` 的 `COMMIT` 是 HEAD 祖先、`## Coverage` 存在）。

### Phase 4 — Re-Audit (When Fixes Are Applied)

完整操作见 `references/reaudit-modes.md`（四种模式 + prior-run 纪律），此处只留要点：

1. **先做祖先性检查**（必做）—— `git merge-base --is-ancestor <audit-commit> HEAD`。
   不是祖先 ⇒ 历史被重写，`git diff` 会返回一堆无关文件：**跳过 diff-filter**，全量重验并重新建立基线，
   并在报告里加 `**Provenance:** baseline-rewritten`（见模板；这是 `validate` 豁免 COMMIT 祖先校验的唯一方式）。
2. **Diff-filter** —— 只重验 `FILE` 落在 `git diff --name-only <audit-commit>..HEAD` 里的 finding。
   `FILE` 基准必须是**仓库根相对 POSIX 路径**；按子目录基准写会让所有 `FILE` 匹配不上，
   被静默判为"未变更"而跳过 —— 安全工具里这是漏报来源。
3. **重验变更文件的 finding** —— 读回源码核对：`fixed`（+`COMMIT=`）/ `not-fixed` / `partial` / `deferred`。
4. **未变更文件的 finding** —— 不重读，但**"文件没变"不等于"结论仍然成立"**：修复可能落在**别的文件**
   （共享工具里加了 guard）。所以对 `open` / `not-fixed` / `partial` 的 finding，还要扫 diff 的**新增行**
   找 remediation 里描述的 guard。其余保持原 `STATUS`，但**必须在重审段的「未重验」表里逐条列出**。
5. **查回归** —— 扫 diff 新增行是否引入新的漏洞模式（`shell=True`、`innerHTML`、用户可控 URL 等）。
6. **写重审段 + 改注解** —— 用 `references/audit-report-template.md` 的 Re-Audit 模板（含「未重验」表）；
   用 `security-audit-tools mark-fixed` 改注解（`VERDICT` 会被自动保留）。
7. **跑契约校验** —— `python bin/security_audit_tools.py validate`，有问题先修再收工。

