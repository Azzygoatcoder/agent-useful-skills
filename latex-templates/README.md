# LaTeX 模板库 — 科研骨架写作模块（PDF 侧）

文档类型 → 模板 → 引擎 映射。编译统一走 `bin/latex_build.py`（ARIS 模式：模板选择 + latexmk + 页数检查）。

## 映射表

| 文档类型 | 模板 | 引擎 | 状态 |
|---------|------|------|------|
| 实习/课程/PRP 报告 | `sjtureport/` | xelatex | ✅ 已验证编译 |
| 学位论文（毕设/硕博） | `sjtuthesis/`（指向 `<SJTUThesis-path>`） | xelatex | ✅ 已验证编译 |
| 会议论文（EDA：DAC/ICCAD） | `ieee-conf/` | pdflatex | ✅ IEEEtran 已装 |
| 会议论文（ML：ICML） | `icml/` | pdflatex | ⏳ 需下载当年官方 .sty |
| 会议论文（ML：NeurIPS） | `neurips/` | pdflatex | ⏳ 需下载当年官方 .sty |

## 用法

```bash
# 新开项目（从模板复制）
python bin/latex_build.py new --template sjtureport --dir my_report

# 编译
python bin/latex_build.py build --dir my_report            # 默认 latexmk
python bin/latex_build.py build --dir my_report --engine pdflatex
python bin/latex_build.py build --dir my_report --pages    # 编译+页数检查
```

## 关键点

- **sjtutex 三类（sjtuthesis/sjtuarticle/sjtureport）随 MiKTeX 自带**，`\documentclass` 直接可用，无需装
- 参考文献：中文用 **biblatex + biber + gb7714-2015**（UTF-8 中文无痛，与 SJTUThesis 同栈）；IEEE 用 `IEEEtran.bst`；ML 用官方 `.bst`
- **页数规则**：ML 会议（ICML/NeurIPS）= 8 页正文（Intro→Conclusion），参考文献/附录不限；IEEE = 全算（含参考文献）
- ICML/NeurIPS 官方 `.sty` 每年更新——投稿前从官方站点下载当年版放模板目录，不 vendoring（避免过期）
- SJTUThesis 维护在独立 clone（`<SJTUThesis-path>`），模板库只做指针

## 新模板接入

1. 在 `latex-templates/` 下建目录放 main.tex + 资源
2. README 映射表加一行（文档类型/模板/引擎）
3. `bin/latex_build.py` 的 `TEMPLATES` 表加 entry
