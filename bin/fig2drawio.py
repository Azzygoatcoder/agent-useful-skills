#!/usr/bin/env python3
"""fig2drawio.py — 论文图 → draw.io 可导入的 Mermaid
Usage: python fig2drawio.py <image_path> [--out out.mmd] [--format mermaid|drawio]
流程: Qwen3-VL 读图结构(JSON) → Qwen3.5-397B 转 Mermaid/draw.io XML → 保存
"""
import sys, os, re
import llm


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


def extract_structure(img_data_url):
    msg = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": img_data_url}},
        {"type": "text", "text": STRUCTURE_PROMPT},
    ]}]
    return llm.chat_vision(msg, temperature=0.2)


def to_mermaid(structure):
    prompt = f"""下面是论文图的结构 JSON：
{structure}

请生成等价的 Mermaid flowchart 代码：
- 方向用结构里的 direction（LR 或 TB）
- 节点用方括号 `A[文字]`，关系用 `A --> B`
- 文字里的特殊字符（括号/引号）要转义或用引号 `A["文字"]`
- 只输出 ```mermaid 代码块，不要其他文字
"""
    return llm.chat(llm.TEXT_MODEL, [{"role": "user", "content": prompt}], temperature=0.2)


def to_drawio(structure):
    prompt = f"""下面是论文图的结构 JSON：
{structure}

请生成等价的 draw.io (diagrams.net) 可导入的 mxGraphModel XML：
- 用 <mxGraphModel> 根节点，<root> 里每个 cell 一个 <mxCell>（vertex 用 value 属性写文字，edge 用 source/target）
- 坐标 (x,y) 从上到下/从左到右合理排布
- 只输出 XML，不要其他文字
"""
    return llm.chat(llm.TEXT_MODEL, [{"role": "user", "content": prompt}], temperature=0.2)


def extract_mermaid(raw):
    m = re.search(r"```mermaid\s*\n(.*?)\n```", raw, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*\n(.*?)\n```", raw, re.S)
    return m.group(1).strip() if m else raw.strip()


def main():
    import argparse
    p = argparse.ArgumentParser(
        description="论文图 → draw.io / Mermaid（独立模型读图结构 → 文本模型转型）")
    p.add_argument("image", help="输入图片路径")
    p.add_argument("--out", help="输出文件（缺省按格式取 figure.mmd / figure.drawio）")
    p.add_argument("--format", choices=["mermaid", "drawio"], default="mermaid",
                   help="输出格式（此前未知值会静默落到 mermaid）")
    p.add_argument("--structure-out", help="把读出的结构 JSON 另存一份，便于人工核对（强烈建议）")
    args = p.parse_args()

    img_path = args.image
    fmt = args.format
    out = args.out or ("figure.drawio" if fmt == "drawio" else "figure.mmd")

    if not os.path.isfile(img_path):
        sys.exit(f"图片不存在：{img_path}")

    print(f"[1/3] 独立模型读图结构 ({llm.VISION_MODEL})...")
    structure = extract_structure(llm.img_url(img_path))
    if not structure or not structure.strip():
        sys.exit("读图失败：独立模型未返回结构")
    # 结构 JSON 是"黑盒转可检查规格"的关键产物：默认存盘，供人工核对后再转型
    struct_out = args.structure_out or (out.rsplit(".", 1)[0] + ".structure.json")
    with open(struct_out, "w", encoding="utf-8") as f:
        f.write(structure)
    print(f"   结构 JSON 已存: {os.path.abspath(struct_out)}（先核对再信任下面的转换）")

    if fmt == "drawio":
        print(f"[2/3] 文本模型转 draw.io XML ({llm.TEXT_MODEL})...")
        result = to_drawio(structure)
        if not out.endswith('.drawio'):
            out = out.rsplit('.', 1)[0] + '.drawio'
    else:
        print(f"[2/3] 文本模型转 Mermaid ({llm.TEXT_MODEL})...")
        result = to_mermaid(structure)
        result = extract_mermaid(result)
        if not out.endswith(('.mmd', '.mermaid')):
            out = out.rsplit('.', 1)[0] + '.mmd'

    if not result or not result.strip():
        sys.exit("转换失败：文本模型未返回内容")
    with open(out, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"[3/3] 已保存: {os.path.abspath(out)}")


if __name__ == "__main__":
    main()
