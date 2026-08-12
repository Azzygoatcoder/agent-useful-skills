#!/usr/bin/env python3
"""llm.py — 科研骨架共享 LLM 客户端（OpenAI-compatible）。

review.py / vision.py / consistency_check.py / fig2drawio.py 共用的调用层：
统一 key 解析、端点覆盖、超时/重试，消除各脚本复制的样板。

脱敏约定：
- key 优先读环境变量，兜底 ~/.claude/settings.json（Claude Code 本地设置，不入库）
- 端点用 LLM_API_URL 覆盖；默认 SiliconFlow（公开供应商）
- 自定义供应商（私有端点）不写进本文件，仅通过环境变量本地注入
"""
import sys, json, os, base64, urllib.request, urllib.error, time, re

sys.stdout.reconfigure(encoding='utf-8')  # 根治 GBK 崩溃

DEFAULT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
VISION_MODEL = os.getenv("VISION_MODEL", "Qwen/Qwen3-VL-32B-Instruct")
TEXT_MODEL = os.getenv("REVIEW_MODEL", "Qwen/Qwen3.5-397B-A17B")
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "120000"))


def get_key():
    """优先环境变量；兜底 ~/.claude/settings.json（Claude Code 本地设置，不入库）。"""
    key = os.getenv("SILICONFLOW_API_KEY")
    if key:
        return key
    try:
        s = json.load(open(os.path.expanduser('~/.claude/settings.json'), encoding='utf-8'))
        return s['env'].get('SILICONFLOW_API_KEY', '')
    except Exception:
        return ''


def api_url():
    """端点：LLM_API_URL 覆盖，默认 SiliconFlow（公开供应商）。"""
    return os.getenv("LLM_API_URL", DEFAULT_API_URL)


def chat(model, messages, temperature=None, timeout=240, retries=2):
    """一次非流式对话，返回 message.content 字符串。

    messages: OpenAI 格式（文本或 image_url 多模态均可）。
    temperature: None 表示不传该字段（用模型默认值）。
    retries: 5xx / 超时 / 网络错误自动重试次数；4xx 直接抛。
    """
    body = {"model": model, "messages": messages}
    if temperature is not None:
        body["temperature"] = temperature
    key = get_key()
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                api_url(), data=json.dumps(body).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            return resp["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise


def chat_json(model, messages, temperature=0.2, timeout=240, retries=2):
    """chat() 的 JSON 变体：要求模型只输出 JSON，解析失败追加纠正再试。

    返回解析后的 dict；重试耗尽仍失败返回 None（由调用方处理）。
    """
    for attempt in range(retries + 1):
        raw = chat(model, messages, temperature=temperature, timeout=timeout, retries=1)
        m = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.S)
        if m:
            raw = m.group(1).strip()
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            raw = raw[s:e + 1]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            if attempt < retries:
                messages = messages + [{"role": "user", "content": "上一条回复不是合法 JSON，请严格只重新输出一个合法 JSON 对象。"}]
                continue
            return None
    return None


def truncate_text(text, limit=None):
    """超长文本截断，保留头尾、中间标记省略，返回 (截断后文本, 是否截断)。"""
    limit = limit if limit is not None else MAX_INPUT_CHARS
    if len(text) <= limit:
        return text, False
    head = int(limit * 0.7)
    tail = int(limit * 0.3)
    out = text[:head] + f"\n\n...［截断：原文 {len(text)} 字符，超 {limit} 上限，中间已省略］...\n\n" + text[-tail:]
    return out, True


def img_url(path_or_url):
    """图片路径 → data URL；已是 http(s):// 或 data: 则原样返回。超大图片告警。"""
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    size = os.path.getsize(path_or_url)
    if size > 15 * 1024 * 1024:  # 15MB，base64 后约 20MB，接近多数视觉 API 上限
        print(f"[warning] 图片 {os.path.basename(path_or_url)} 达 {size // 1024 // 1024}MB，可能超出视觉 API 限制，建议先压缩", file=sys.stderr)
    with open(path_or_url, 'rb') as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


if __name__ == "__main__":
    print(f"api_url = {api_url()}")
    print(f"VISION_MODEL = {VISION_MODEL}")
    print(f"TEXT_MODEL = {TEXT_MODEL}")
    print(f"key_configured = {bool(get_key())}")
