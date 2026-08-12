#!/usr/bin/env python3
"""Consistency check: feed original gpt-image-2 image + vector-replica PNG to Qwen3-VL,
ask for a strict element-by-element diff and a 1-10 consistency score."""
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
    img_a, img_b = sys.argv[1], sys.argv[2]
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": llm.img_url(img_a)}},
        {"type": "image_url", "image_url": {"url": llm.img_url(img_b)}},
        {"type": "text", "text": PROMPT},
    ]}]
    print(llm.chat(llm.VISION_MODEL, messages))


if __name__ == "__main__":
    main()
