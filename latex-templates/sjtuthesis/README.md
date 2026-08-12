# SJTUThesis — 学位论文

毕设/硕博学位论文用 **sjtug/SJTUThesis**（学位办官方认可）。

- 已 clone 到 `<SJTUThesis-path>`（完整工程，非本目录副本）
- 本地编译验证：`latexmk -xelatex main.tex`（已验证通过）
- 学位类型：`\documentclass[type=bachelor|master|doctor]{sjtuthesis}`
- 盲审版：`\documentclass[review=true]{sjtuthesis}`（自动去作者/导师/致谢）

结构：`main.tex`（主入口）+ `setup.tex`（配置）+ `contents/`（分章）+ `figures/` + `refs.bib`。

用 bin/latex_build.py 新开项目：
```
python bin/latex_build.py new --template sjtuthesis --dir 我的论文 --src <SJTUThesis-path>
```
