#!/usr/bin/env python3
"""fig2drawio.py — 论文图 → draw.io 可导入的 Mermaid
Usage: python fig2drawio.py <image_path> [--out out.mmd] [--format mermaid|drawio]
流程: Qwen3-VL 读图结构(JSON) → Qwen3.5-397B 转 Mermaid/draw.io XML → 保存
"""
import sys, json, os, base64, urllib.request, re

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.getenv("LLM_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
VISION_MODEL = os.getenv("VISION_MODEL", "Qwen/Qwen3-VL-32B-Instruct")
TEXT_MODEL = os.getenv("REVIEW_MODEL", "Qwen/Qwen3.5-397B-A17B")


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


def call(model, messages):
    body = {"model": model, "messages": messages, "temperature": 0.2}
    req = urllib.request.Request(
        BASE, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + get_key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"]


STRUCTURE_PROMPT = """这是一张论文图（架构/流程/示意图）。请提取结构化信息，严格只输出一个 JSON 对象，不要任何其他文字：
{
  "nodes": [{"id": "n1", "label": "节点文字(准确抄录图里的文字)"}, ...],
  "edges": [{"from": "n1", "to": "n2"}, ...],
  "direction": "LR 或 TB（依据图的主流向）",
  "title": "图的标题（如有）"
}
- 节点 = 图里的每个框/模块/椭圆，label 尽量精确
- edges = 箭头/连线关系（谁指向谁）
- 读不清的字符用 "?" 占位，不要编造"""


def extract_structure(img_b64):
    msg = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + img_b64}},
        {"type": "text", "text": STRUCTURE_PROMPT},
    ]}]
    return call(VISION_MODEL, msg)


def to_mermaid(structure):
    prompt = f"""下面是论文图的结构 JSON：
{structure}

请生成等价的 Mermaid flowchart 代码：
- 方向用结构里的 direction（LR 或 TB）
- 节点用方括号 `A[文字]`，关系用 `A --> B`
- 文字里的特殊字符（括号/引号）要转义或用引号 `A["文字"]`
- 只输出 ```mermaid 代码块，不要其他文字
"""
    return call(TEXT_MODEL, [{"role": "user", "content": prompt}])


def to_drawio(structure):
    prompt = f"""下面是论文图的结构 JSON：
{structure}

请生成等价的 draw.io (diagrams.net) 可导入的 mxGraphModel XML：
- 用 <mxGraphModel> 根节点，<root> 里每个 cell 一个 <mxCell>（vertex 用 value 属性写文字，edge 用 source/target）
- 坐标 (x,y) 从上到下/从左到右合理排布
- 只输出 XML，不要其他文字
"""
    return call(TEXT_MODEL, [{"role": "user", "content": prompt}])


def extract_mermaid(raw):
    m = re.search(r"```mermaid\s*\n(.*?)\n```", raw, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*\n(.*?)\n```", raw, re.S)
    return m.group(1).strip() if m else raw.strip()


def main():
    if len(sys.argv) < 2:
        print("usage: fig2drawio.py <image_path> [--out out] [--format mermaid|drawio]", file=sys.stderr)
        sys.exit(1)
    img_path = sys.argv[1]
    fmt = "mermaid"
    out = "figure.mmd"
    if "--format" in sys.argv:
        fmt = sys.argv[sys.argv.index("--format") + 1]
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]

    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()

    print(f"[1/3] vision 读图结构 ({VISION_MODEL})...")
    structure = extract_structure(img_b64)
    print("   结构 JSON:", structure[:200].replace('\n', ' '), "...")

    if fmt == "drawio":
        print(f"[2/3] LLM 转 draw.io XML ({TEXT_MODEL})...")
        result = to_drawio(structure)
        if not out.endswith('.drawio'):
            out = out.rsplit('.', 1)[0] + '.drawio'
    else:
        print(f"[2/3] LLM 转 Mermaid ({TEXT_MODEL})...")
        result = to_mermaid(structure)
        result = extract_mermaid(result)
        if not out.endswith(('.mmd', '.mermaid')):
            out = out.rsplit('.', 1)[0] + '.mmd'

    with open(out, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"[3/3] 已保存: {os.path.abspath(out)}")


if __name__ == "__main__":
    main()
