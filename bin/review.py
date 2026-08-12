#!/usr/bin/env python3
"""review.py — 跨模型对抗评审（默认 Qwen3.5-397B-A17B / SiliconFlow）

Usage: python review.py <file_path|text> [focus]
评审 prompt 改编自 ARIS auto-review-loop 的对抗评审范式。
评审者与执行者（deepseek）不同模型 → 跨模型独立性。
"""
import sys, os
import llm

REVIEW_PROMPT = """你是一名资深评审（顶级会议/期刊级别）。假设这份工作一定有严重问题，你的任务就是找到它。请直接阅读内容本身，不要轻信任何转述。

请输出：
1. 总体评分（1-10）
2. 关键弱点列表（按严重程度排序，每项说明为什么致命）
3. 每个弱点的最小修复建议（具体可执行）
4. 明确结论：READY / NOT READY / ALMOST

要求：残酷诚实。如果你真的努力想找出问题但内容经得住考验，就明确说出来。"""


def main():
    if len(sys.argv) < 2:
        print("usage: review.py <file_path|text> [focus]", file=sys.stderr)
        sys.exit(1)
    target = sys.argv[1]
    focus = sys.argv[2] if len(sys.argv) > 2 else ""
    if os.path.exists(target):
        with open(target, encoding='utf-8') as f:
            content = f.read()
        src = f"文件: {target}"
    else:
        content = target
        src = "直接文本输入"
    if focus:
        content += f"\n\n[重点审查方向] {focus}"

    messages = [
        {"role": "system", "content": REVIEW_PROMPT},
        {"role": "user", "content": f"待评审内容（{src}）:\n\n{content}"},
    ]
    result = llm.chat(llm.TEXT_MODEL, messages, temperature=0.3)
    print(f"===== 评审结果（{llm.TEXT_MODEL}）=====")
    print(result)


if __name__ == "__main__":
    main()
