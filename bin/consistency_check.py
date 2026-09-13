#!/usr/bin/env python3
"""Consistency check: feed original image + vector-replica PNG to an INDEPENDENT model,
ask for a strict element-by-element diff and a 1-10 consistency score.

定位：这是「验证环」的独立模型复核，不是"代眼"——被复核的矢量图通常由作者模型产出，
同模型自评会继承同一套盲点，所以这里刻意走另一个模型（Qwen3-VL）。
"""
import os
import sys

import llm

PROMPT = (
    "Image A is the ORIGINAL gpt-image-2 generated concept diagram. "
    "Image B is a vector replica redrawn in draw.io. "
    "Strictly compare the two and list, item by item, every English element that Image B "
    "LOST, SIMPLIFIED, or CHANGED relative to Image A. Pay special attention to: omitted or "
    "renamed text labels, missing boxes/nodes, missing or extra arrows, changed arrow "
    "directions, lost terminology, and any annotation that disappeared. Do NOT ignore "
    "differences just because Image B looks cleaner or more organized. "
    "Finally, output a consistency score from 1 to 10 (10 = perfect verbatim match) and a "
    "one-line verdict."
)


def main():
    import argparse
    p = argparse.ArgumentParser(
        description="矢量图一致性复核：原图 + 复刻图 → 独立模型逐元素 diff + 1-10 分")
    p.add_argument("original", help="原始图（如 gpt-image-2 产物）")
    p.add_argument("replica", help="复刻图（如 draw.io 导出 PNG）")
    args = p.parse_args()
    img_a, img_b = args.original, args.replica
    # 路径先校验：此前缺参直接 IndexError，路径写错则把远端报错当结论打印
    for label, path in (("原始图", img_a), ("复刻图", img_b)):
        if not os.path.isfile(path):
            print(f"{label}不存在：{path}", file=sys.stderr)
            sys.exit(2)
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": llm.img_url(img_a)}},
        {"type": "image_url", "image_url": {"url": llm.img_url(img_b)}},
        {"type": "text", "text": PROMPT},
    ]}]
    out = llm.chat_vision(messages)
    if not out or not str(out).strip():
        print("复核失败：独立模型未返回内容", file=sys.stderr)
        sys.exit(3)
    print(out)


if __name__ == "__main__":
    main()
