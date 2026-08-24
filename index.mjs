// agent-useful-skills — DSH bundle entry.
//
// Registers the whole repository's skill collection (the same set
// bin/redeploy-skills.ps1 deploys: <repo>/skills/* and <repo>/plugins/*/skills/*)
// as a single FileSystemSkillProvider on ctx.skills.
//
// Coexistence / idempotency contract:
//  1. The provider SKIPS every skill name already present in the standard
//     skill roots (user ~/.dsh/skills, ~/.agents/skills, and the cwd project's
//     .dsh/skills / .agents/skills) — so a machine that already deployed these
//     skills via junctions keeps its copies and nothing duplicates.
//  2. Remaining candidates carry rank 700, BELOW every standard root rank
//     (project 100/200, runtime 250, custom 300, user 400/500, bundled 600),
//     so any other registration of the same name wins by priority.
//     The plugin's copies only surface where nothing else provides the name.
//  3. apply() is safe to mount twice in one process: the provider name is
//     registered once; a second registration attempt only warns.
import { existsSync, readdirSync } from 'node:fs'
import { access, readdir, stat } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { homedir } from 'node:os'
import { FileSystemSkillProvider } from '@deepseek-ai/dsh-skill-filesystem'

export const name = 'agent-useful-skills'
export const inject = ['skills']

const PACKAGE_ROOT = fileURLToPath(new URL('.', import.meta.url))
/** Below every standard root rank — the plugin copy only wins when nothing else provides the skill. */
export const FALLBACK_RANK = 700
export const PROVIDER_SOURCE = 'plugin:agent-useful-skills'

/** Skill base roots inside the installed package: `skills/` plus every plugin's nested `skills/` folder. */
export function repoSkillBases(packageRoot = PACKAGE_ROOT) {
  const bases = []
  const top = join(packageRoot, 'skills')
  if (existsSync(top)) bases.push(top)
  const plugins = join(packageRoot, 'plugins')
  if (existsSync(plugins)) {
    for (const sub of readdirSync(plugins, { withFileTypes: true })) {
      if (!sub.isDirectory()) continue
      const nested = join(plugins, sub.name, 'skills')
      if (existsSync(nested)) bases.push(nested)
    }
  }
  return bases
}

/** Every single-level skill directory underneath the bases (the redeploy-skills.ps1 contract). */
export function repoSkillRoots(packageRoot = PACKAGE_ROOT) {
  const dirs = []
  for (const base of repoSkillBases(packageRoot)) {
    for (const entry of readdirSync(base, { withFileTypes: true })) {
      if (entry.isDirectory()) dirs.push(join(base, entry.name))
    }
  }
  return dirs
}

/** Nearest ancestor containing .git (same shape as the host provider's project-root discovery). */
export async function findProjectRoot(cwd) {
  let current = cwd
  for (;;) {
    try {
      await access(join(current, '.git'))
      return current
    } catch { /* keep walking */ }
    const parent = dirname(current)
    if (parent === current) return null
    current = parent
  }
}

async function collectNames(root, found) {
  let entries
  try {
    entries = await readdir(root, { withFileTypes: true })
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry.name === '.system') continue
    const full = join(root, entry.name)
    try {
      const info = await stat(full)
      if (info.isDirectory()) {
        if (existsSync(join(full, 'SKILL.md'))) found.add(entry.name)
      } else if (entry.name.endsWith('.md')) {
        found.add(entry.name.slice(0, -3))
      }
    } catch { /* unreadable entry — ignore */ }
  }
}

/**
 * Skill names already provided by the standard filesystem roots. These are
 * the names this plugin must NOT re-register (dedup against junction
 * deployments and any other local copy).
 */
export async function existingSkillNames(cwd) {
  const found = new Set()
  const roots = [
    join(process.env.DSH_HOME ?? join(homedir(), '.dsh'), 'skills'),
    join(process.env.DSH_AGENTS_HOME ?? join(homedir(), '.agents'), 'skills'),
  ]
  if (cwd !== undefined) {
    const project = await findProjectRoot(cwd)
    if (project !== null) {
      roots.push(join(project, '.dsh', 'skills'), join(project, '.agents', 'skills'))
    }
  }
  for (const root of roots) await collectNames(root, found)
  return found
}

/**
 * The host provider (rank 300 for custom dirs) would SHADOW user-root skills
 * (rank 400). We subclass: discovery/parsing stays official; list() first
 * drops names already present in standard roots, then demotes the survivors
 * to a fallback rank so any other same-name registration wins by priority.
 */
export class AgentUsefulSkillsProvider extends FileSystemSkillProvider {
  constructor(ctx, control) {
    super(ctx, control, {
      providerName: name,
      includeDefaultRoots: false,
      watch: false,
      customSkillDirs: repoSkillBases(),
    })
  }

  async list(options) {
    let output
    try {
      output = await super.list(options)
    } catch (error) {
      this.ctx.logger.warn(`agent-useful-skills provider list failed: ${String(error)}`)
      return { candidates: [], complete: true }
    }
    const candidates = Array.isArray(output) ? output : output.candidates
    const complete = Array.isArray(output) ? true : output.complete
    const existing = await existingSkillNames(options.cwd)
    const visible = candidates
      .filter((candidate) => !existing.has(candidate.name))
      .map((candidate) => ({
        ...candidate,
        rank: FALLBACK_RANK,
        provider: name,
        source: PROVIDER_SOURCE,
      }))
    return { candidates: visible, complete }
  }
}

let provider = null

export function apply(ctx) {
  if (provider !== null) return
  try {
    ctx.skills.registerProvider((control) => {
      provider = new AgentUsefulSkillsProvider(ctx, control)
      return provider
    })
    ctx.effect(() => () => {
      provider = null
    })
  } catch (error) {
    ctx.logger.warn(`agent-useful-skills: provider is already registered — duplicate mount ignored (${String(error)})`)
  }
}