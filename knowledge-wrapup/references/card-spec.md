# Knowledge Card Specification (spec_version: 1)

The card is the middleware of the whole system: every source (conversation, note,
PDF) is normalized into this one format, and integration consumes nothing else.
Cards are for machine consumption — English-only, no translation section.

## File naming

`cards/{topic}--{yyyyMMdd}.md` — e.g. `prompt-caching--20260705.md`

- `topic` is the knowledge's unique identifier: lowercase kebab-case English,
  matching the curated note's filename. It is the dedupe anchor.
- The date suffix allows the same topic to produce cards on different days
  (new sources, new information); integration merges them into the same note.
- One card per topic per day. If a card for the same topic already exists with
  today's date, extend that card (flip it back to `status: raw`, re-validate,
  re-integrate) instead of inventing a second filename.

## Frontmatter — all fields required, enums are closed

```yaml
---
spec_version: 1                    # bump only when this spec changes
topic: prompt-caching              # kebab-case; must match filename
type: concept                      # concept | term | howto | gotcha | tutorial
domain: technology/ai-engineering  # from TAXONOMY.md; <level1>[/<level2>]
tags: [claude-api, performance]    # 2–4 target (1–5 hard limit), from TAXONOMY '## Tags' registry
source: conversation               # conversation | note | pdf
source_ref: "conversation-claude/conversation-20260705.md"  # path; for PDFs add page, e.g. "guide.pdf#p12"
confidence: verified               # verified (actually run/tested in session) | discussed
date: 2026-07-05
status: raw                        # raw | merged | dropped
---
```

## Body — required sections by type

Fixed English `##` headings. `## References` is optional; all others required.

| type | required sections, in order |
|---|---|
| `concept`, `term` | Definition → Usage scenarios → Example → Related |
| `howto` | Goal → Prerequisites → Steps → Verification → Related |
| `gotcha` | Symptom → Cause → Fix → How to avoid → Related |
| `tutorial` | Goal → Steps → Result → Related |

Section rules:

- **Example / Steps**: prefer the actual example from the source conversation —
  concrete beats generic. Examples are written in **best-practice form from
  the start** (never a naive version the reader must later unlearn); when a
  practice is load-bearing — omitting it causes real failures — name it
  explicitly and state what it prevents (e.g. `@functools.wraps` on a
  decorator's wrapper).
- **Related**: `[[wikilinks]]` to associated topics. Linking to notes that do
  not exist yet is deliberate — `obsidian unresolved` turns them into a
  to-learn list. But **links follow content, never the other way around**: a
  dangling link is a promise that a note passing the three gates could exist
  there. Do not link out of habit to project-specific machinery, to
  tool-overview placeholders ("[[obsidian]]" from an Obsidian-related note),
  or to hub pages nobody asked for. Dispositions for an existing dangling
  link: fill it when real content arrives; leave it as a signpost; delete it
  once it turns out the "content" would be project docs or trivia — never
  write a thin note just to clear the list.
- **References** (optional, 0–3 links): official docs and high-quality
  tutorials, formatted as an **ordered list** (`1.`, `2.`, …), each with a
  one-line note on what it covers. **Never invent a URL.** Only include links
  that actually appeared in the conversation or canonical official domains you
  are certain of (e.g. git-scm.com, developer.mozilla.org). If uncertain, write
  the resource name with "(search for this)" and no URL.

## Completeness standard

A card must be able to **re-teach its topic months later without the
conversation**. Capture every distinct point the source actually covered —
all steps, the concrete examples, the command lines, the pitfalls, the
comparisons. Compressing a rich discussion into a thin digest is a defect:
brevity belongs to the diary's Summary field, not to cards or notes. When the
source compared or enumerated things, keep the table; when it walked a
process, keep every step.

## Worked example — a good card

```markdown
---
spec_version: 1
topic: git-commit-messages
type: howto
domain: technology/tools
tags: [git, best-practice]
source: conversation
source_ref: "conversation-claude/conversation-20260705.md"
confidence: discussed
date: 2026-07-05
status: raw
---

# Writing Good Git Commit Messages

## Goal
Commit messages that let a reader understand *why* a change was made without
opening the diff.

## Prerequisites
Basic git workflow (add/commit).

## Steps
1. Subject line: imperative mood, ≤ 50 chars, no trailing period —
   "Fix race in session cleanup", not "Fixed some bugs".
2. Blank line, then a body explaining *why* (the diff already shows *what*).
3. Optionally adopt Conventional Commits: `type(scope): subject`, e.g.
   `feat(auth): add token refresh`.

## Verification
`git log --oneline` reads like a changelog a teammate can follow.

## References
- [Conventional Commits](https://www.conventionalcommits.org/) — the
  `type(scope): subject` convention and its rationale.

## Related
[[git-workflow]], [[code-review]]
```

## Counter-examples — do NOT extract these

1. **"We renamed `utils.py` to `helpers.py` in the user's repo."**
   Fails gate 1 (reusable): project-specific action, meaningless elsewhere.
2. **"Canvas means a surface you draw on."**
   Fails gate 2 (non-trivial) *if* that is all that was said. It passes only when
   the conversation added real substance (e.g. `<canvas>` vs SVG trade-offs) —
   or via the fundamentals exception (SKILL.md Step 2): personal friction
   evidence in the conversation (repeated questions, a misunderstanding,
   learned-and-forgotten) admits a textbook topic, tagged `fundamentals` and
   written around the friction point.
3. **"The user prefers concise answers."**
   Excluded category: preference — belongs to memory, not the knowledge base.
4. **"As discussed above, combine that approach with the second option."**
   Fails gate 3 (self-contained): meaningless without conversation context.
   Rewrite it into a self-contained statement or drop it.

## Tag rules

Tags express **cross-cutting facets**; the domain expresses the single home.
They answer different questions, so they must not overlap:

1. Tags come from the `## Tags` registry in the vault's TAXONOMY.md.
   **Reuse first** — check the registry (and `obsidian tags`) before inventing;
   a genuinely new tag is registered there in the same run and announced in the
   report. Unregistered tags fail validation.
2. Never tag what the domain already says: no `git` tag on a note in
   `technology/git` (validator enforces this).
3. Target 2–4 tags; 1–5 is the hard limit. One is lonely, five is a ceiling,
   not a goal.

## Validation

Every card must pass before integration:

```bash
python3 scripts/validate_card.py <card>... --vault <vault_path>
```

Checks: filename pattern, frontmatter completeness, enum values, topic/filename
consistency, domain present in TAXONOMY.md, tag format, required body sections
for the card's type. Fix and re-run until exit code 0.
