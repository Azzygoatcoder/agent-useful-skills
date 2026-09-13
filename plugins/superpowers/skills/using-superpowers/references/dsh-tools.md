# DeepSeek Harness (DSH) Tool Mapping

Skills in this pack speak in **actions** ("dispatch a subagent", "search the web", "write a todo"). On DeepSeek Harness those resolve to the tools below. Load this file only when your harness is DSH.

| Action a skill requests | DSH equivalent |
|------------------------|----------------|
| Dispatch a subagent / "Subagent (general-purpose):" template | `subagent` tool (self-contained prompt) or `subagent_fork` (inherits this conversation) |
| Run several independent subagents in parallel | multiple `subagent` calls in ONE message (background by default) |
| Read a file | `read` |
| Read many files | several `read` calls in one message |
| Create / overwrite a file | `write` |
| Edit a file in place | `edit` |
| Run a shell command | `pwsh` (PowerShell 7; `bash` may be unavailable on Windows) |
| Search file contents | `grep` |
| Find files by name | `glob` |
| Fetch a URL | `web_fetch` |
| Search the web | `web_search` |
| Track a multi-step task | `todo_write` |
| Load a skill | `skill` tool with the exact skill name |
| Invoke an MCP tool | `mcp__<server>__<tool>` (e.g. `mcp__gen-image__generate_image`) |
| Long-running / background command | `pwsh` with `run_in_background: true`, then `job_output` |

## Path resolution — read this before running any helper script

DSH injects into every skill body:

> **Base directory for this skill: `<dir>`** — Resolve relative paths mentioned by this skill against the base directory before using them.

So a bare ``bin/vision.py`` inside a skill means `<skill-base>/bin/vision.py`, which **does not exist** — the helper scripts live in the *repository root* `bin/`, and each skill is loaded from its own directory (often via a junction under `~/.dsh/skills/<name>`).

Resolve helper scripts against the **repository root**, not the skill base:

- Installed via `pip install -e .` → use the console command: `review`, `vision`, `office-tools`, `latex-build`, `data-plot`, `consistency-check`, `fig2drawio`, `security-audit-tools`, `check-skills`, `style-reference-docx`.
- Otherwise → run `python <repo-root>/bin/<script>.py …`.

Never assume the current working directory is the repository root; if a path does not resolve, say so instead of guessing.

## Runtime differences worth knowing

- **`~/.dsh/skills/`** is the user skill root; **`~/.agents/skills/`** is the cross-runtime alias. Project-level roots are `<project>/.dsh/skills/`.
- **Do not delete** a deployed skill from a DSH skill-management UI when the repo uses junctions: deleting the link can cascade to the real repository files. Disable instead.
- Skills are discovered **single-level only**: `<root>/<skill-name>/SKILL.md`. Reference material must live in `references/` inside the skill, never as a nested `SKILL.md`.
- Frontmatter is strict: only `name`, `description`, `whenToUse`, `disable-model-invocation`, `user-invocable`, `metadata` are read. The legacy camelCase keys (`disableModelInvocation`, `modelInvocable`, `userInvocable`) cause the skill to be **dropped with a warning**.
- `description` is what the catalog shows — the runtime truncates it at **500 characters**.
