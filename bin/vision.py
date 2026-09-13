#!/usr/bin/env python3
"""vision.py — 跨模型识图（独立第二意见）

Usage: python vision.py <image_path|URL> [prompt]

定位（2026-09-12 起）：宿主模型（DeepSeek V4.1+）自带原生视觉，**直接读图即可**。
本脚本不再是"给盲模型代眼"，而是提供**与作者模型不同的独立判断**——用于验证场景：
渲染有没有错、这张图值不值得留、结构与文字对不对得上。同模型自评会继承同一套盲点，
独立模型才有信息量，所以它服务的是本仓库的"验证环"，而不是"看懂一张图"。

  - 只是想看懂一张图       → 用原生读图，别调本脚本
  - 需要独立模型复核一张图 → 用本脚本（Qwen3-VL-32B by default）
"""
import sys
import llm


def main():
    if len(sys.argv) < 2:
        print("usage: vision.py <image_path|URL> [prompt]", file=sys.stderr)
        sys.exit(1)
    target = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片的内容，包括所有关键文字。"
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": llm.img_url(target)}},
        {"type": "text", "text": prompt},
    ]}]
    print(llm.chat_vision(messages))


if __name__ == "__main__":
    main()
