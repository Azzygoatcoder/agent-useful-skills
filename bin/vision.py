#!/usr/bin/env python3
"""Vision proxy: give text-only LLMs indirect image recognition via Qwen3-VL-32B (SiliconFlow).

Usage: python vision.py <image_path|URL> [prompt]
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
