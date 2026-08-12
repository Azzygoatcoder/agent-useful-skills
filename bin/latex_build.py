#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
latex_build.py — LaTeX 模板库管理（ARIS 模式：模板选择 + latexmk 编译 + 页数检查）
科研骨架写作模块（PDF 侧） | 依赖: latexmk + xelatex/pdflatex, fitz(页数检查)

用法:
  python latex_build.py list
  python latex_build.py new --template sjtureport --dir my_report
  python latex_build.py new --template sjtuthesis --dir 我的论文 --src <SJTUThesis-path>
  python latex_build.py build --dir my_report [--engine xelatex|pdflatex|lualatex] [--pages] [--main-body]
  python latex_build.py pages --dir my_report [--main-body]

页数规则: ML 会议(icml/neurips)=正文页数只算 Intro→Conclusion(References 前);
          IEEE = 全算(含参考文献)。--main-body 输出正文页数。
模板目录: latex-templates/（与 bin/ 同级）。
"""

import argparse, os, re, shutil, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "latex-templates")

TEMPLATES = {
    "sjtureport": "sjtureport",      # 实习/课程/PRP 报告（xelatex）
    "sjtuthesis": "sjtuthesis",      # 学位论文（源在独立 clone，需 --src）
    "ieee-conf":  "ieee-conf",       # IEEE 会议（DAC/ICCAD）
    "icml":       "icml",            # ICML（需下载官方 .sty）
    "neurips":    "neurips",         # NeurIPS（需下载官方 .sty）
}

MAIN_FILE = "main.tex"


def cmd_list(_):
    print("LaTeX 模板库: latex-templates/")
    for name in TEMPLATES:
        print(f"  {name:12s} {TEMPLATES[name]}")
    print("\n映射见 latex-templates/README.md")


def cmd_new(args):
    if args.template not in TEMPLATES:
        sys.exit(f"未知模板 {args.template}，可用: {', '.join(TEMPLATES)}")
    if os.path.exists(args.dir):
        sys.exit(f"目标目录已存在: {args.dir}")
    if args.template == "sjtuthesis" and not args.src:
        sys.exit("sjtuthesis 需要 --src 指向 SJTUThesis clone（如 <SJTUThesis-path>）")
    src = args.src or os.path.join(TEMPLATE_DIR, TEMPLATES[args.template])
    if not os.path.isdir(src):
        sys.exit(f"模板源不存在: {src}")
    shutil.copytree(src, args.dir,
                    ignore=shutil.ignore_patterns("*.aux", "*.log", "*.out", "*.fls",
                                                  "*.fdb_latexmk", "*.pdf", ".git"))
    print(f"已从 {TEMPLATES[args.template]} 创建项目 → {args.dir}")
    print(f"  下一步: python bin/latex_build.py build --dir {args.dir}")


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, text=True, encoding="utf-8",
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"命令失败: {' '.join(cmd)}\n{r.stderr[-1500:] or r.stdout[-1500:]}")
    return r


def cmd_build(args):
    if not os.path.exists(os.path.join(args.dir, MAIN_FILE)):
        sys.exit(f"{args.dir} 下没有 {MAIN_FILE}")
    engine = {"xelatex": "-xelatex", "pdflatex": "-pdf", "lualatex": "-lualatex"}[args.engine]
    print(f"=== latexmk 编译 {args.dir}（{args.engine}）===")
    run(["latexmk", engine, "-interaction=nonstopmode", "-halt-on-error", MAIN_FILE], args.dir)
    pdf = os.path.join(args.dir, "main.pdf")
    if not os.path.exists(pdf):
        sys.exit("编译未产出 main.pdf")
    n = pdf_pages(pdf)
    print(f"✅ 编译成功: {pdf}（{n} 页）")
    if args.pages or args.main_body:
        print_pages(pdf, args.main_body)


def cmd_pages(args):
    pdf = os.path.join(args.dir, "main.pdf")
    if not os.path.exists(pdf):
        sys.exit(f"没有 main.pdf（先 build）: {pdf}")
    print_pages(pdf, args.main_body)


def pdf_pages(pdf):
    import fitz
    return fitz.open(pdf).page_count


def references_page(pdf):
    """找 References/参考文献 标题所在页（0 基）。找不到返回 None。"""
    import fitz
    doc = fitz.open(pdf)
    for i in range(min(doc.page_count, 60)):
        text = doc[i].get_text()
        if re.search(r"^\s*(References|REFERENCES|参考文献)\s*$", text, re.M):
            return i
    return None


def print_pages(pdf, main_body=False):
    n = pdf_pages(pdf)
    print(f"  总页数: {n}")
    if main_body:
        rp = references_page(pdf)
        if rp is not None:
            print(f"  正文页数(References 前): {rp}（ML 会议规则：正文≤8 页）")
        else:
            print("  未找到 References 标题，跳过正文页数")


def main():
    p = argparse.ArgumentParser(description="LaTeX 模板库管理")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="列出模板")
    n = sub.add_parser("new", help="从模板创建项目")
    n.add_argument("--template", required=True)
    n.add_argument("--dir", required=True)
    n.add_argument("--src", help="自定义源（sjtuthesis 需要）")
    b = sub.add_parser("build", help="latexmk 编译")
    b.add_argument("--dir", required=True)
    b.add_argument("--engine", default="xelatex", choices=["xelatex", "pdflatex", "lualatex"])
    b.add_argument("--pages", action="store_true", help="编译后报告页数")
    b.add_argument("--main-body", action="store_true", help="额外输出正文页数(References 前)")
    pg = sub.add_parser("pages", help="统计页数")
    pg.add_argument("--dir", required=True)
    pg.add_argument("--main-body", action="store_true")
    args = p.parse_args()
    {"list": cmd_list, "new": cmd_new, "build": cmd_build, "pages": cmd_pages}[args.cmd](args)


if __name__ == "__main__":
    main()
