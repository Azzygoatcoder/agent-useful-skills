---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, checking whether a skill applies before acting, with fast paths for small tasks
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

## The Rule

Check whether a skill clearly applies before acting on a task. When one does, invoke it — and say so.

**Before entering plan mode:** only use the optional brainstorming/planning flow when the task is genuinely ambiguous or large. Small, well-specified tasks skip it.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

**Proportion matters.** Skill ceremony is a tool, not a tax. Small, unambiguous tasks don't need the full process — use subagent-driven-development's lightweight path or just do the fix. Don't force a heavyweight skill onto something that's clearly a quick fix.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → if large/ambiguous, use the optional planning flow first; otherwise implement directly.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Worth a Second Look

These thoughts are signals to check whether a skill genuinely applies — not automatic triggers:

| Thought | Check |
|---------|-------|
| "I need more context first" | A skill might tell you HOW to gather it. |
| "Let me explore the codebase first" | Skills can guide the exploration. |
| "This doesn't need a formal skill" | Ask: would the skill's discipline prevent a real mistake here? |
| "I remember this skill" | Skills evolve — read the current version if you invoke it. |

If the check comes back no, proceed without it. The point is noticing, not guilt.

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
