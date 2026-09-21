---
name: md-format-fixer
description: >
  Check and fix common markdown formatting issues after writing or editing any .md file.
  MUST be invoked whenever you have just written or edited a markdown file (via Write or
  Edit tools). Checks table formatting, code-block fences, blank lines, ambiguous headers,
  and other rendering hazards; fixes what it can and flags what needs judgment. Also invoke
  on "check markdown", "fix formatting", "markdown格式", "表格格式", or a .md rendering wrong.
---

# Markdown Format Fixer

After every Write or Edit to a `.md` file, run through the checks below on the file
you just touched. Fix issues in place unless flagged for manual review.

## Check 1: Tables — blank lines

**Problem**: A markdown table immediately after a text line (without a blank line between)
can be misparsed by some renderers (Obsidian, GitHub, strict CommonMark).

**Detection**: Any line matching `^|.*|$` that is preceded by a non-empty, non-table,
non-blank line.

**Fix**: Insert a blank line before the table header row.

## Check 2: Code blocks — closing fence

**Problem**: Content that should be outside a code block is trapped inside because the
closing ``` is missing or placed after that content.

**Detection**: Looking for lines of plain text between the last content line and the
closing ``` of a fenced code block.

**Fix**: Move the closing ``` to before the escaped content, so the content renders
as normal markdown.

**Manual flag**: If no closing ``` exists at all, add one at the end — but warn the
user to verify the intended scope.

## Check 3: Table column counts

**Problem**: A data row has fewer or more `|`-separated cells than the header row or
separator row, causing rendering breakage.

**Detection**: Count the number of `|` in the header row, separator row, and each
data row. Any mismatch is an error.

**Fix**:
- **Missing cell**: Insert an empty cell ` ` at the position.
- **Extra cell**: Merge or remove — flag for manual review if ambiguous.

## Check 4: Code blocks — empty fences

**Problem**: ` ``` ` on a line by itself with no matching close creates an unterminated
code block that swallows all subsequent content.

**Detection**: Any ` ``` ` that opens a code block but has no matching close before EOF
or before another code block opens.

**Fix**: Add a closing ` ``` ` at the end of the intended block. If the intended scope
is unclear, flag for manual review.

## Check 5: Ambiguous table headers

**Problem**: Column headers that don't convey what the column represents (e.g., just
"差距" without specifying "A − B 差距", or single-word labels that are meaningless
without context).

**Detection**: Look for table headers that are single generic words without units or
comparison direction.

**Fix**: Expand the header to be self-describing. Flag for manual review — the writer
knows best what the column contains.

## Check 6: Unicode hazards in tables

**Problem**: Fullwidth characters (： U+FF1A, ， U+FF0C) or special Unicode symbols
in or near table markup can cause rendering issues in some parsers.

**Detection**: Fullwidth colon `：` immediately before a table (on the introducing line),
or unusual Unicode in `|` separators.

**Fix**: Replace `：` with `:` before tables where it serves as a colon introducing
the table. Other fullwidth characters in cell content are usually fine.

## 自进化日志（The Fix Log）

After every fix session, append a brief entry to `references/fix-log.md`:

```markdown
### {date} — {filename}
- **Found**: {brief description of issue}
- **Fixed**: {what you did}
- **Root cause**: {why it happened — e.g., "wrote table directly after bold text without blank line"}
```

Before running checks, quickly scan the fix log for recurring patterns. If the same
issue has occurred 3+ times, mention it to the user as a systematic habit to watch
for (this is the "self-evolution" — the skill gets better at catching your specific
patterns).

## When Not to Fix

- **Intentional formatting**: If a table-without-blank-line is clearly inside a list
  item or blockquote where it's structurally correct, leave it.
- **Inline code blocks**: Single-backtick inline code is fine; don't touch it.
- **Already-correct files**: If no issues found, just confirm "no issues" — don't
  make unnecessary edits.
