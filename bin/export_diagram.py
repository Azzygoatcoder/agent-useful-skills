#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_diagram.py — 把配图的单文件 HTML 图源导出为独立 .svg（可选 .png）

用法:
  python export_diagram.py <diagram.html> [...]        # 导出同目录同名 .svg
  python export_diagram.py --png <diagram.html> [...]  # 顺便导出 .png（需 rsvg-convert）
  python export_diagram.py --check [<html> ...]        # 只校验，不写文件（退出码 1 = 有漂移）

为什么需要它：仓库里的配图是「HTML 唯一图源，SVG/PNG 由它派生」。此前这个派生靠手工，
于是漂移过两次——旧 audit-workflow-v14 的 HTML/SVG 两件成了孤儿，且导出的 .svg 缺
`xmlns`，作为 <img> 嵌入时根本不渲染。本脚本把导出固化成可复现的一条命令。

导出步骤（对齐 diagram-design/references/export.md）：
  1. 取 HTML 里**第一个** <svg> 块
  2. 补 xmlns（缺了就不是合法 standalone SVG，<img> 不渲染）
  3. 要求有 viewBox（没有就报错，不猜）
  4. 注入 webfont @import（合并进既有 <defs>，不新增第二个）
  5. 前置 XML 声明后写出
纯标准库；PNG 走外部 rsvg-convert（缺失则跳过并提示）。
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)
FONT_IMPORT = (
    "<style>@import url('https://fonts.googleapis.com/css2?"
    "family=Instrument+Serif:ital@0;1&amp;family=Geist:wght@400;500;600&amp;"
    "family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>"
)
XML_PROLOG = '<?xml version="1.0" encoding="UTF-8"?>\n'


def build_svg(html_text: str) -> str:
    """从 HTML 取出首个 <svg> 并补全为独立可用的 SVG。缺关键属性时抛 ValueError。"""
    m = SVG_RE.search(html_text)
    if not m:
        raise ValueError("HTML 里找不到 <svg> 块")
    svg = m.group(0)
    head = svg.split(">", 1)[0]

    if "xmlns=" not in head:
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        head = svg.split(">", 1)[0]
    if "viewBox" not in head:
        raise ValueError("<svg> 根节点缺 viewBox —— 拒绝猜测尺寸")

    if "<defs>" in svg:
        svg = svg.replace("<defs>", "<defs>" + FONT_IMPORT, 1)
    else:
        svg = svg.replace(">", "><defs>" + FONT_IMPORT + "</defs>", 1)
    return XML_PROLOG + svg + "\n"


def export_one(html_path: str, want_png: bool = False) -> tuple[bool, str]:
    """返回 (是否变更, 说明)。"""
    if not os.path.isfile(html_path):
        return False, f"图源不存在：{html_path}"
    base = os.path.splitext(html_path)[0]
    svg_path = base + ".svg"
    try:
        text = build_svg(open(html_path, encoding="utf-8").read())
    except ValueError as exc:
        return False, f"{os.path.basename(html_path)}: {exc}"

    old = open(svg_path, encoding="utf-8").read() if os.path.isfile(svg_path) else None
    changed = old != text
    if changed:
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(text)

    note = "已更新" if changed else "无变化"
    if want_png:
        conv = shutil.which("rsvg-convert") or shutil.which("magick")
        if conv is None:
            note += "；跳过 PNG（未找到 rsvg-convert / magick）"
        else:
            png_path = base + ".png"
            cmd = ([conv, "-w", "1360", svg_path, "-o", png_path]
                   if conv.endswith("rsvg-convert")
                   else [conv, svg_path, png_path])
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            note += "；PNG " + ("已导出" if r.returncode == 0 else f"失败({r.returncode})")
    return changed, f"{os.path.relpath(svg_path)}: {note}"


def main() -> int:
    ap = argparse.ArgumentParser(description="配图 HTML 图源 → 独立 SVG（可选 PNG）")
    ap.add_argument("html", nargs="+", help="图源 HTML 路径")
    ap.add_argument("--png", action="store_true", help="同时导出 PNG（需 rsvg-convert）")
    ap.add_argument("--check", action="store_true", help="只校验 .svg 是否与 HTML 同步，不写文件")
    args = ap.parse_args()

    if args.check:
        drift = []
        for h in args.html:
            base = os.path.splitext(h)[0]
            svg_path = base + ".svg"
            if not os.path.isfile(h):
                drift.append(f"图源不存在：{h}")
                continue
            if not os.path.isfile(svg_path):
                drift.append(f"缺派生 SVG：{os.path.relpath(svg_path)}")
                continue
            try:
                want = build_svg(open(h, encoding="utf-8").read())
            except ValueError as exc:
                drift.append(f"{os.path.relpath(h)}: {exc}")
                continue
            if open(svg_path, encoding="utf-8").read() != want:
                drift.append(f"{os.path.relpath(svg_path)} 已与图源漂移（重跑 export_diagram.py）")
        if drift:
            for d in drift:
                print(f"✗ {d}")
            print(f"校验失败：{len(drift)} 处需要重新导出")
            return 1
        print(f"✓ 全部通过：{len(args.html)} 个图源的派生 SVG 均同步")
        return 0

    n_changed = 0
    for h in args.html:
        changed, note = export_one(h, want_png=args.png)
        print(("● " if changed else "· ") + note)
        n_changed += int(changed)
    print(f"\n{'已更新' if n_changed else '无变化'}：{n_changed}/{len(args.html)} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
