#!/usr/bin/env node
// gen-image-mcp.js — 零依赖 MCP 服务器，通用 OpenAI 兼容生图（/v1/images/generations）
// 端点配置全部来自环境变量，不硬编码任何供应商。
//
//   单端点（命名为 default）:
//     GEN_IMAGE_URL=https://.../v1
//     GEN_IMAGE_API_KEY=sk-...
//   多端点（JSON 对象，支持 openai/anthropic 等任意 OpenAI 兼容服务）:
//     GEN_IMAGE_PROVIDERS='{"name":{"url":"https://.../v1","key":"sk-..."}}'
//   其它:
//     GEN_IMAGE_MODEL=...（默认 gpt-image-2）
//     GEN_IMAGE_DIR=...（输出目录，默认 ~/Pictures/generated）
const fs = require('fs');
const path = require('path');
const https = require('https');
const os = require('os');

function loadProviders() {
  const map = {};
  // 主端点 → 命名 default
  if (process.env.GEN_IMAGE_URL) {
    map.default = { url: process.env.GEN_IMAGE_URL, key: process.env.GEN_IMAGE_API_KEY || '' };
  }
  // 额外端点（JSON）
  try {
    const extra = JSON.parse(process.env.GEN_IMAGE_PROVIDERS || '{}');
    for (const [name, cfg] of Object.entries(extra)) {
      if (cfg && cfg.url) map[name] = { url: cfg.url, key: cfg.key || '' };
    }
  } catch (e) { /* 配置解析失败则忽略 */ }
  return map;
}

const PROVIDERS = loadProviders();
const OUT_DIR = process.env.GEN_IMAGE_DIR || path.join(os.homedir(), 'Pictures', 'generated');
const MODEL = process.env.GEN_IMAGE_MODEL || 'gpt-image-2';

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

function generateImage(provider, model, prompt, size, n) {
  const p = PROVIDERS[provider];
  if (!p) return Promise.reject(new Error('未知 provider: ' + provider + '（可用: ' + Object.keys(PROVIDERS).join(', ') + '）'));
  if (!p.key) return Promise.reject(new Error(provider + ' 的 API key 未配置'));
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ model, prompt, n: n || 1, size: size || '1024x1024' });
    const req = https.request(p.url.replace(/\/+$/, '') + '/images/generations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + p.key,
        'Content-Length': Buffer.byteLength(body),
      },
    }, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error('响应解析失败: ' + data.slice(0, 200))); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function handle(msg) {
  if (msg.method === 'initialize') {
    return send({ jsonrpc: '2.0', id: msg.id, result: {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'gen-image-mcp', version: '2.0.0' },
    }});
  }
  if (msg.method === 'notifications/initialized' || msg.method === 'notifications/cancelled') return;
  if (msg.method === 'ping') return send({ jsonrpc: '2.0', id: msg.id, result: {} });

  if (msg.method === 'tools/list') {
    return send({ jsonrpc: '2.0', id: msg.id, result: { tools: [
      {
        name: 'generate_image',
        description: '通过 OpenAI 兼容接口生成图片，保存到本地并返回文件路径。provider 由环境变量 GEN_IMAGE_PROVIDERS / GEN_IMAGE_URL 配置。',
        inputSchema: {
          type: 'object',
          properties: {
            prompt: { type: 'string', description: '图片描述提示词（建议写清主体/风格/细节）' },
            provider: { type: 'string', description: 'provider 名（env 配置的端点），默认 default' },
            size: { type: 'string', enum: ['1024x1024', '1024x1792', '1792x1024'], description: '图片尺寸，默认 1024x1024' },
            n: { type: 'number', description: '生成数量，默认 1' },
          },
          required: ['prompt'],
        },
      },
      {
        name: 'get_server_info',
        description: '返回服务配置（各 provider 端点、key 是否配置、输出目录）',
        inputSchema: { type: 'object', properties: {} },
      },
    ]}});
  }

  if (msg.method === 'tools/call') {
    const { name, arguments: args } = msg.params;
    if (name === 'get_server_info') {
      const info = {};
      for (const [k, p] of Object.entries(PROVIDERS)) {
        info[k] = { url: p.url, keyConfigured: !!p.key };
      }
      info.outDir = OUT_DIR;
      return send({ jsonrpc: '2.0', id: msg.id, result: {
        content: [{ type: 'text', text: JSON.stringify(info, null, 2) }],
      }});
    }
    if (name === 'generate_image') {
      const provider = args.provider || 'default';
      const resp = await generateImage(provider, MODEL, args.prompt, args.size, args.n);
      if (resp.error) throw new Error(provider + ' 返回错误: ' + JSON.stringify(resp.error));
      const results = [];
      fs.mkdirSync(OUT_DIR, { recursive: true });
      for (let i = 0; i < (resp.data || []).length; i++) {
        const b64 = resp.data[i].b64_json;
        if (!b64) { results.push('第 ' + (i + 1) + ' 张无 b64_json'); continue; }
        const fname = 'gen-' + provider + '-' + Date.now() + '-' + i + '.png';
        const fpath = path.join(OUT_DIR, fname);
        fs.writeFileSync(fpath, Buffer.from(b64, 'base64'));
        results.push(fpath);
      }
      return send({ jsonrpc: '2.0', id: msg.id, result: {
        content: [{ type: 'text', text: '[' + provider + '] 已生成 ' + results.length + ' 张图:\n' + results.join('\n') }],
      }});
    }
    return send({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: '未知工具: ' + name } });
  }

  if (msg.id !== undefined) {
    return send({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: 'Method not found: ' + msg.method } });
  }
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  buffer += chunk;
  let idx;
  while ((idx = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, idx);
    buffer = buffer.slice(idx + 1);
    if (!line.trim()) continue;
    let msg;
    try { msg = JSON.parse(line); } catch (e) { continue; }
    handle(msg).catch((err) => {
      if (msg.id !== undefined) {
        send({ jsonrpc: '2.0', id: msg.id, error: { code: -32603, message: String(err.message || err) } });
      }
    });
  }
});
