#!/usr/bin/env node
// verify-plugin.mjs — 白盒验证 agent-useful-skills 的 DSH 插件入口（无需启动 DSH）。
//
// 覆盖：
//  1. apply() 幂等：同进程二次挂载不重复注册；注册表抛错时不崩溃（只告警）。
//  2. 去重契约：本机（~/.dsh/skills 已有 junction 部署）list() 返回 0 个候选，
//     全新机器（空 DSH_HOME）返回 skills.manifest.json 中的默认技能。
//  3. 候选形状：rank=FALLBACK_RANK(700)、provider/source 正确、description/invocation 齐全。
//  4. get() 能读出 SKILL.md 正文（与官方解析规则一致）。
//
// 运行：node bin/verify-plugin.mjs
// 依赖：仓库根 node_modules/@deepseek-ai/dsh-skill-filesystem —— 用 `npm install` 解析
//   （package.json 声明 ^0.1.1-rc.1）。不要手工建 junction 指向 DSH 运行时的
//   node_modules：pnpm 的内容寻址 store 目录名带哈希，运行时每次更新哈希就变，
//   junction 会悬空并让本脚本以 ERR_MODULE_NOT_FOUND 崩掉（2026-09 实际踩过）。
//   注意：`npm install` 解析到的版本可能低于 DSH 实际运行时版本（例如装到
//   0.1.1-rc.2 而运行时是 0.1.5-rc.1）。本脚本只验证插件自身的注册/去重契约，
//   两者 API 兼容即可；若上游改了 Config/list() 形状，需同步核对运行时版本。
import { mkdtemp, rm } from 'node:fs/promises'
import { readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  apply,
  AgentUsefulSkillsProvider,
  existingSkillNames,
  repoSkillRoots,
  archivedSkillRoots,
  DEFAULT_SKILL_NAMES,
  FALLBACK_RANK,
  PROVIDER_SOURCE,
  name,
} from '../index.mjs'

let failures = 0
function check(label, ok, detail = '') {
  console.log(`${ok ? '✓' : '✗'} ${label}${detail ? ` — ${detail}` : ''}`)
  if (!ok) failures += 1
}

const control = () => ({ signal: new AbortController().signal, invalidate() {} })
const logger = { warn: (...args) => console.warn('  [warn]', ...args) }
const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..')

// --- 1. apply() 幂等 ---
{
  let registerCalls = 0
  const ctx = {
    logger,
    get: () => undefined,
    on: () => () => {},
    effect: () => () => {},
    skills: { registerProvider: (create) => { registerCalls += 1; create(control()); return () => {} } },
  }
  apply(ctx)
  apply(ctx)
  apply(ctx)
  check('apply() 幂等：二次/三次挂载不重复注册', registerCalls === 1, `registerProvider 调用 ${registerCalls} 次`)

  const throwing = {
    logger,
    get: () => undefined,
    on: () => () => {},
    effect: () => () => {},
    skills: { registerProvider: () => { throw new Error('already registered') } },
  }
  let threw = false
  try { apply(throwing) } catch { threw = true }
  check('apply() 遇注册表抛错不崩溃（只告警）', !threw)
}

// --- 2/3. 去重契约 + 候选形状 ---
const dirs = repoSkillRoots().map((d) => d.replace(/\\/g, '/').split('/').at(-1)).sort()
check('默认技能目录发现 ⊇ 仓库默认清单', dirs.length >= DEFAULT_SKILL_NAMES.length, `${dirs.length} 个: ${dirs.join(', ')}`)

const missingDefault = DEFAULT_SKILL_NAMES.filter((d) => !dirs.includes(d))
check('默认清单中的技能都存在于默认目录', missingDefault.length === 0, missingDefault.join(', '))

// 刻意不参与模型自动调用的技能：仍需可加载/可手动调用，但设 disable-model-invocation
// 把它们从 catalog 摘掉，避免每轮误命中。断言该字段确实存在——否则摘除会静默失效。
const CATALOG_EXCLUDED = ['using-superpowers']
const extraDirs = dirs.filter((d) => !DEFAULT_SKILL_NAMES.includes(d) && !CATALOG_EXCLUDED.includes(d))
check('默认目录无多余技能（CATALOG_EXCLUDED 除外）', extraDirs.length === 0, extraDirs.join(', '))

for (const name of CATALOG_EXCLUDED) {
  const skillPath = join(repoRoot, 'plugins/superpowers/skills', name, 'SKILL.md')
  let hasFlag = false
  try {
    const head = readFileSync(skillPath, 'utf8').split('---')[1] ?? ''
    hasFlag = /^\s*disable-model-invocation:\s*true\s*$/m.test(head)
  } catch { /* 文件缺失 → hasFlag 保持 false */ }
  check(`${name} 设了 disable-model-invocation: true（不占 catalog）`, hasFlag, hasFlag ? '' : `检查 ${skillPath}`)
}

const archivedDirs = archivedSkillRoots().map((d) => d.replace(/\\/g, '/').split('/').at(-1)).sort()
// 与清单一样按实测数目断言，不用魔法数字（archive/ 会随每次合并增长）
check('归档技能非空且与默认清单无重叠', archivedDirs.length > 0, `${archivedDirs.length} 个: ${archivedDirs.join(', ')}`)
const archiveConflict = archivedDirs.filter((d) => DEFAULT_SKILL_NAMES.includes(d))
check('归档与默认清单无重叠', archiveConflict.length === 0, archiveConflict.join(', '))

const existing = await existingSkillNames(repoRoot)
const overlap = existing.size > 0 ? dirs.filter((d) => existing.has(d)) : []
console.log(`  本机标准技能根已存在 ${existing.size} 个技能名，与本仓库重叠: ${overlap.length} 个（${overlap.join(', ') || '无'}）`)

{
  const provider = new AgentUsefulSkillsProvider({ logger, get: () => undefined }, control())
  const out = await provider.list({ cwd: repoRoot })
  const visible = out.candidates.map((c) => c.name).sort()
  const expectedVisible = DEFAULT_SKILL_NAMES.filter((d) => !existing.has(d)).sort()
  check(
    `本机 list() 让位给 junction 部署（候选 = ${expectedVisible.length} 个）`,
    JSON.stringify(visible) === JSON.stringify(expectedVisible),
    `实际 ${visible.length} 个`,
  )
}

// --- 全新机器模拟：空 DSH_HOME ---
{
  const temp = await mkdtemp(join(tmpdir(), 'aus-verify-'))
  const savedHome = process.env.DSH_HOME
  const savedAgents = process.env.DSH_AGENTS_HOME
  process.env.DSH_HOME = temp
  process.env.DSH_AGENTS_HOME = join(temp, 'agents')
  try {
    const ctx = { logger, get: () => undefined }
    const provider = new AgentUsefulSkillsProvider({ logger, get: () => undefined }, control())
    const out = await provider.list({ cwd: repoRoot })
    const candidates = out.candidates
    const names = candidates.map((c) => c.name).sort()
    const expectedFresh = [...DEFAULT_SKILL_NAMES].sort()
    check('全新机器 list() 返回默认技能清单', names.length === expectedFresh.length && JSON.stringify(names) === JSON.stringify(expectedFresh), `${names.length}/${expectedFresh.length}`)
    const leak = names.filter((d) => !DEFAULT_SKILL_NAMES.includes(d))
    check('归档技能不会进入默认候选', leak.length === 0, leak.join(', '))
    const bad = candidates.filter((c) => c.rank !== FALLBACK_RANK || c.provider !== name || c.source !== PROVIDER_SOURCE || !c.description || !c.invocation)
    check('候选形状：rank/provider/source/description/invocation 合规', bad.length === 0, bad.length > 0 ? bad.map((b) => b.name).join(',') : '')
    const target = candidates.find((c) => c.name === 'storage-analyzer')
    check('storage-analyzer 候选存在', target !== undefined)
    if (target !== undefined) {
      const def = await provider.get(target, { signal: new AbortController().signal })
      check(
        'get() 读回 SKILL.md 正文',
        def !== undefined && def.content.includes('# Storage Analyzer') && def.provider === name,
        def === undefined ? 'get 返回空' : `${def.content.length} chars`,
      )
    }
  } finally {
    if (savedHome === undefined) delete process.env.DSH_HOME
    else process.env.DSH_HOME = savedHome
    if (savedAgents === undefined) delete process.env.DSH_AGENTS_HOME
    else process.env.DSH_AGENTS_HOME = savedAgents
    await rm(temp, { recursive: true, force: true })
  }
}

console.log(failures === 0 ? '\n✓ 全部通过' : `\n✗ ${failures} 项失败`)
process.exit(failures === 0 ? 0 : 1)