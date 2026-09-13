#!/usr/bin/env python3
"""review.py — 跨模型对抗评审（结构化 JSON 输出）

Usage: python review.py <file_path|text> [focus] [--json]
评审 prompt 改编自 ARIS kill-argument 范式：commit 到单一最强拒绝理由，逼承诺。
评审者与执行者（deepseek）不同模型 → 跨模型独立性。
默认人类可读排版；--json 仅输出纯 JSON 供程序消费（自动 gate 用）。

--json 输出形状（gate 可据此判可信度）：
  {
    "truncated": false,          # true = 输入超长被截断，结论只覆盖头尾
    "original_chars": 12345,     # 原始输入字符数
    "reviewed_chars": 12345,     # 实际送审字符数
    "max_input_chars": 120000,   # 当前上限
    "verdict": {...}             # 模型返回的评审结果
  }
**自动 gate 必须检查 truncated**：为 true 时评审只看到头 70% + 尾 30%，
中间被省略，不能当作完整评审结论。
"""
import sys, os, json
import llm

REVIEW_PROMPT = """你是一名顶级会议/期刊的资深评审。假设这份工作一定有严重问题，你的任务是用尽一切理由拒绝它。请直接阅读内容本身，不要轻信任何转述。

核心要求：不要列一长串弱点。请 commit 到单一最强的一个拒绝理由——如果只能用一个理由拒掉这份工作，你会选哪个？为什么它致命？

严格只输出一个 JSON 对象，不要任何其他文字：
{
  "score": 1到10的整数,
  "verdict": "READY" 或 "ALMOST" 或 "NOT_READY",
  "strongest_objection": "单一最强的拒绝理由，一句话说清为什么致命",
  "minimal_fix": "针对该理由的最小可执行修复",
  "other_weaknesses": ["次要弱点，最多3条，每条一句话"]
}

规则：
- strongest_objection 只能写一个理由，禁止用"还有/其次/另外"再列别的
- 如果内容真的经得起你的攻击，verdict 用 "READY"，strongest_objection 写 "未找到致命缺陷"
- 残酷诚实，不迁就"""


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv[1:]
    if not args:
        print("usage: review.py <file_path|text> [focus] [--json]", file=sys.stderr)
        sys.exit(1)
    target = args[0]
    focus = args[1] if len(args) > 1 else ""
    if os.path.exists(target):
        with open(target, encoding='utf-8') as f:
            content = f.read()
        src = f"文件: {target}"
    else:
        content = target
        src = "直接文本输入"
    if focus:
        content += f"\n\n[重点审查方向] {focus}"
    original_chars = len(content)
    content, truncated = llm.truncate_text(content)
    if truncated:
        print(f"[warning] 输入超长，已截断到 {llm.MAX_INPUT_CHARS} 字符（保留头尾）", file=sys.stderr)

    messages = [
        {"role": "system", "content": REVIEW_PROMPT},
        {"role": "user", "content": f"待评审内容（{src}）:\n\n{content}"},
    ]
    result = llm.chat_json(llm.TEXT_MODEL, messages, temperature=0.3)
    if result is None:
        print("评审失败：模型未返回合法 JSON", file=sys.stderr)
        sys.exit(2)
    if as_json:
        # 显式带出截断状态：gate 消费 JSON 时必须能区分「完整评审」与「头尾评审」
        print(json.dumps({
            "truncated": truncated,
            "original_chars": original_chars,
            "reviewed_chars": len(content),
            "max_input_chars": llm.MAX_INPUT_CHARS,
            "verdict": result,
        }, ensure_ascii=False, indent=2))
        if truncated:
            # 非零退出：让自动 gate 无法把截断评审误当通过
            sys.exit(3)
    else:
        if truncated:
            print(f"⚠️ 输入被截断（{original_chars} → {len(content)} 字符），"
                  f"结论只覆盖头尾，中间内容未被评审", file=sys.stderr)
        _pretty(result)


def _pretty(r):
    print(f"===== 评审结果（{llm.TEXT_MODEL}）=====")
    print(f"评分 {r.get('score')} / 10    判定 {r.get('verdict')}")
    print(f"\n[最强拒绝理由] {r.get('strongest_objection')}")
    print(f"[最小修复] {r.get('minimal_fix')}")
    others = r.get('other_weaknesses') or []
    if others:
        print("\n[次要弱点]")
        for w in others:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
