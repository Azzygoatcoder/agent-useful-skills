#!/usr/bin/env python3
"""Vision proxy: give text-only LLMs indirect image recognition via Qwen3-VL-32B (SiliconFlow).

Usage: python vision.py <image_path|URL> [prompt]
Key 优先读环境变量 SILICONFLOW_API_KEY，兜底 ~/.claude/settings.json（Claude Code 本地设置）。
URL 可用 LLM_API_URL 覆盖（默认 SiliconFlow）。Output is UTF-8 (safe on Chinese Windows).
"""
import sys, json, base64, urllib.request, os

sys.stdout.reconfigure(encoding='utf-8')  # 根治 GBK 编码崩溃

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


def main():
    if len(sys.argv) < 2:
        print("usage: vision.py <image_path|URL> [prompt]", file=sys.stderr)
        sys.exit(1)
    target = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片的内容，包括所有关键文字。"
    if target.startswith(('http://', 'https://')):
        url = target
    else:
        with open(target, 'rb') as f:
            url = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": url}},
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
