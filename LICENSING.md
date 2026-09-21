# 许可证策略

本仓库（`agent-useful-skills` monorepo）的授权规则。与 [`VERSIONING.md`](VERSIONING.md)（版本策略）、
[`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)（第三方归属）配套。

## 一句话

**根 MIT 覆盖全仓库；只有「可能被单独拿走的单元」才自带一份 LICENSE；fork 来的上游内容永远保留上游许可。**

## 默认：根 LICENSE 覆盖一切

根 [`LICENSE`](LICENSE) 是 MIT（Copyright (c) 2026 Azzygoatcoder）。
**没有自带 LICENSE 的目录一律按根 MIT 授权**，不需要逐个补文件 —— 那只会制造二十份内容相同的副本，
改一次要改二十处，且迟早不一致。

因此以下**不需要**各自 LICENSE（它们不是独立分发单元）：

`bin/` · `tests/` · `assets/` · `archive/` · `latex-templates/` · `skills/*` · `.github/`

> **`latex-templates/` 单独说明**：里面是我们**自写的最小骨架**（`main.tex` 几百字节，
> 靠 `\usepackage{neurips_2025}` 之类的引用取官方样式；ICML / NeurIPS 的官方 `.sty`
> **刻意不 vendoring**，见其 README「避免过期」）。`sjtuthesis/` 只是一份指路 README，
> 真工程在独立 clone。所以这里**不涉及** IEEE / ICML / NeurIPS / SJTU 的模板许可，
> 也没有转载其条款的义务。

## 例外一：可独立分发的单元自带 LICENSE

**判据：接收方有没有可能只拿到这个目录？**

`plugins/*/` 符合 —— 它们能被单独安装：

```bash
claude plugins install <repo> --path plugins/code-security-skills
```

所以每个插件目录下放一份与根**完全一致**的 MIT LICENSE，让授权随代码一起走。

| 目录 | 自带 LICENSE | 说明 |
|---|---|---|
| `plugins/code-security-skills/` | ✅ MIT © 2026 Azzygoatcoder | 与根一致 |
| `plugins/dev-workflow/` | ✅ MIT © 2026 Azzygoatcoder | 与根一致 |
| `plugins/superpowers/` | ✅ MIT © 2025 Jesse Vincent | **fork，保留上游署名** —— 见例外二 |

**不要**把 `skills/*` 也铺一遍 LICENSE：`bin/redeploy-skills.ps1` 把它们软链进**本机** DSH 技能根，
那是同机部署、不是分发，不产生转载义务；真要分发时它们随仓库整体走，根 MIT 已经覆盖。

## 例外二：fork 的上游内容保留上游许可

`plugins/superpowers/` 是 [obra/superpowers](https://github.com/obra/superpowers) 的本地 fork
（永不更新上游，原版 MIT）。它的 `LICENSE` 是**上游的**（Copyright (c) 2025 Jesse Vincent）。

- **不要**覆盖成本仓库署名。MIT 要求保留版权声明，覆盖即违规。
- 我们对其中的 skill 做了大量修改（并新增 figure-drawing / paper-reading / paper-writing /
  office-tools）—— MIT 允许修改与再分发，但**署名不能抹**。新增内容同样按该 MIT 授权即可，
  没必要搞双许可。

## 例外三：第三方内容按各自许可

随仓库分发的第三方内容（如 `skills/storage-analyzer` 改自 `KKKKhazix/khazix-skills` 的 MIT）
统一在 [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md) 登记来源与许可，均遵循上游许可。

## 新增内容时怎么办

| 你加了什么 | 要做什么 |
|---|---|
| 新的 `plugins/<name>/` | 复制根 `LICENSE` 一份进去 |
| 新的 `skills/<name>/` | 什么都不用做（随仓库整体走） |
| 从别处 fork / 抄来的内容 | **保留其 `LICENSE` 原样**，并在 `THIRD-PARTY-NOTICES.md` 登记来源与许可 |
| 只改了文档 | 什么都不用做 |

## 机器可读字段一览

| 文件 | 字段 | 当前值 |
|---|---|---|
| `package.json` | `license` | `MIT` |
| `pyproject.toml` | `license` | `MIT` |
| `plugins/<name>/.claude-plugin/plugin.json` | `license` | `MIT` |

> `plugins/superpowers/` 另有 `.codex-plugin/` / `.cursor-plugin/` / `.kimi-plugin/` 三份 manifest，
> 其 `license` 亦为 `MIT`。

## 不用做的事

- 不必为每个 skill / 每个脚本文件加 SPDX 头 —— 根 LICENSE 已覆盖，加了只是噪音
- 不必给上游 fork「重新授权」成本仓库署名
- 不必在 README 里逐个复述许可证全文 —— 指到本文件与 `THIRD-PARTY-NOTICES.md` 即可
