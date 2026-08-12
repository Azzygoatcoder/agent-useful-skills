#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
style_reference_docx.py — 给 pandoc reference.docx 预设中文论文样式
科研骨架写作模块 | 用法: python style_reference_docx.py [模板路径]（默认 bin/templates/reference.docx）

设置:
  Normal           宋体/Times New Roman 12pt（小四）
  Body Text/首段   首行缩进 2 字符(firstLineChars=200) + 1.5 倍行距
  Heading 1/2/3    黑体 16/14/12pt（三号/四号/小四）
  Title            黑体

重新生成默认模板: pandoc -o reference.docx --print-default-data-file reference.docx
然后跑本脚本预设中文样式；也可在 WPS/Word 里打开模板手动微调（改完保存即生效）。
"""

import argparse, sys
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

LATIN = "Times New Roman"
EAST = "宋体"
HEI = "黑体"


def set_fonts(style, latin=LATIN, east=EAST, size=None, bold=None, line=None, indent_chars=None):
    style.font.name = latin  # 建 rPr/rFonts（ascii/hAnsi）
    style.font.element.rPr.rFonts.set(qn("w:eastAsia"), east)
    if size:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if line:
        style.paragraph_format.line_spacing = line
    if indent_chars:
        pPr = style.element.get_or_add_pPr()
        ind = pPr.get_or_add_ind()
        ind.set(qn("w:firstLineChars"), str(indent_chars * 100))  # 2 字符 = 200


def main():
    p = argparse.ArgumentParser(description="预设 reference.docx 中文样式")
    p.add_argument("path", nargs="?", default=r"bin\templates\reference.docx")
    args = p.parse_args()
    doc = Document(args.path)
    st = {s.name: s for s in doc.styles}
    set_fonts(st["Normal"], size=12)                                        # 宋体小四
    for name in ("Body Text", "First Paragraph"):
        set_fonts(st[name], size=12, line=1.5, indent_chars=2)              # 首行缩进2字符
    for i, sz in enumerate((16, 14, 12), start=1):
        set_fonts(st[f"Heading {i}"], east=HEI, latin=LATIN, size=sz)       # 黑体标题
    set_fonts(st["Title"], east=HEI, latin=LATIN, size=28)
    doc.save(args.path)
    print(f"已预设中文样式 → {args.path}")


if __name__ == "__main__":
    main()
