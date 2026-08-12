#!/usr/bin/env python3
"""Consistency check: feed original gpt-image-2 image + vector-replica PNG to Qwen3-VL,
ask for a strict element-by-element diff and a 1-10 consistency score."""
import sys, json, base64, urllib.request, os

sys.stdout.reconfigure(encoding='utf-8')

API_URL = os.getenv("LLM_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
MODEL = os.getenv("VISION_MODEL", "Qwen/Qwen3-VL-32B-Instruct")


def get_key():
    """优先环境变量；兜底 ~/.claude/settings.json（Claude Code 本地设置）。"""
    key = os.getenv("SILICONFLOW_API_KEY")
    if key:
        return key
    try:
        s = json.load(open(os.path.expanduser('~/.claude/settings.json'), encoding='utf-8'))
        return s['env'].get('SILICONFLOW_API_KEY', '')
    except Exception:
        return ''


def as_data_url(path):
    with open(path, 'rb') as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def main():
    img_a, img_b = sys.argv[1], sys.argv[2]
    prompt = (
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
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": as_data_url(img_a)}},
            {"type": "image_url", "image_url": {"url": as_data_url(img_b)}},
            {"type": "text", "text": prompt}
        ]}]
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + get_key(), "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read())
    print(resp["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
