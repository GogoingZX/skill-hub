# Knowledge Card Specification (spec_version: 1)

The card is the middleware of the whole system: every source (conversation, note,
PDF) is normalized into this one format, and integration consumes nothing else.
Cards are for machine consumption — English-only, no translation section.

## File naming

`cards/{topic}--{yyyyMMdd}.md` — e.g. `prompt-caching--20260705.md`

- `topic` is the knowledge's unique identifier: lowercase kebab-case English,
  matching the curated note's filename. It is the dedupe anchor.
- `topic` names the concept by ITS NAME, readable at a glance — never how it's
  computed or implemented:
  - Use the term people use for the concept: a plain phrase, or an established
    named term (`bessel-correction`, `capm`, `oauth`). Never lead with — or
    fall back to — an implementation detail: an API parameter, a formula
    fragment, a symbol, or a spec number.
    - ✗ `bessel-correction-and-ddof` (ddof = API parameter)
    - ✗ `sample-variance-n-minus-1` (n-minus-1 = formula fragment)
    - ✓ `bessel-correction-sample-variance` (named concept + subject)
    - ✗ `pep-723-inline-script-metadata` (number leads)
    - ✓ `python-inline-script-deps--pep723` (concept leads; number → `--<id>` suffix)
  - The line: name = "what it's CALLED", not "how it's DONE".
  - Test: scanning `notes/`, you know what the file is about from the name alone.
  - Spec/standard numbers (PEP/RFC/CVE/ISO/W3C…) go as a `--<id>` suffix anchor,
    never the head; most topics have no number → no suffix.
  - Specific over vague: `choosing-a-package-installer`, not `packages`.
- The date suffix allows the same topic to produce cards on different days
  (new sources, new information); integration merges them into the same note.
- One card per topic per day. If a card for the same topic already exists with
  today's date, extend that card (flip it back to `status: raw`, re-validate,
  re-integrate) instead of inventing a second filename. Re-integration applies
  only the card's NEW material to the note — the previously merged content is
  already there, and re-appending it is a defect.
- **Merged cards are frozen.** Once `status: merged`, a card is a provenance
  snapshot: never edit it retroactively — presentation/style fixes go to the
  NOTE only; new information about the topic gets a new dated card (or the
  same-day flip-to-raw above). This keeps cards honest as "what was extracted
  that day" and kills card/note drift maintenance. **The one exception is a
  privacy scrub**: removing a real identifier or private datum that must not
  persist anywhere (see synthetic-data rule) may edit a frozen card in place.

## Frontmatter — enums are closed; fields required unless marked optional

```yaml
---
spec_version: 1                    # bump only when this spec changes
topic: prompt-caching              # kebab-case; must match filename
type: concept                      # concept | term | howto | gotcha | tutorial
                                   # term vs concept: would it belong in a
                                   # glossary? unit = a NAME people use (the
                                   # card explains the word) -> term; unit = a
                                   # mechanism (explains how the thing works)
                                   # -> concept; unsure -> concept.
domain: technology/ai-engineering  # from TAXONOMY.md; <level1>[/<level2>]
tags: [claude-api, performance]    # 2–4 target (1–5 hard limit), from TAXONOMY '## Tags' registry
source: conversation               # conversation | note | pdf
source_ref: "conversation-claude/conversation-20260705.md"  # path; for PDFs add page, e.g. "guide.pdf#p12"
confidence: verified               # verified (actually run/tested in session) | discussed
date: 2026-07-05
status: raw                        # raw | merged | dropped
scope: versioned                   # (optional) universal | versioned | observed | policy
last_verified: 2026-07-05          # (optional) required when scope is versioned/observed
---
```

### Claim scope (optional, but set it on version-sensitive material)

`scope` records what KIND of claim the card makes, so an absolute-sounding title
is not mistaken for a universal law. It is optional — a judgment field: the
validator checks it when present and warns on absolute titles, but does not
require it (Level-2 enforcement, not a hard gate):

- `universal` — holds regardless of tool version or environment; only for
  genuinely general facts.
- `versioned` — depends on a tool/product version; requires `last_verified`
  (yyyy-MM-dd) and an in-body note of what it applies to.
- `observed` — a single-environment or local reproduction; requires
  `last_verified` and a minimal repro + environment; never titled as a universal
  limit.
- `policy` — this vault's own preference, not a claim about tool capability;
  state the goal and the cost.

The curated note carries the same `scope`/`last_verified` — it is the living
version-anchor, since a merged card is frozen and cannot be re-verified.

### Synthetic identifiers and private data (privacy red line)

Cards and notes are treated as publishable: never carry a real local username,
personal name, email, absolute home path (`/Users/<name>/…`), or real private
specifics (trip destinations, dates, amounts) from the session. Replace them
with synthetic, non-reversible stand-ins (`dev-a`, `try-new-parser`, seeded
fixtures, `/Users/<user>/…`). When a topic needs concrete data, use a fixed-seed
synthetic set and say so. The validator scans for home paths carrying a real
username, non-example emails, and a configured denylist of your own identifiers
(`--privacy-denylist`).

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
  concrete beats generic — but SELF-STANDING (markdown-style U6): numbers
  chosen for teaching clarity, session/project outcomes at most one line
  framed as evidence, never narrative ("we then…", "in the original
  incident…"). Examples are written in **best-practice form from
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
  the resource name with "(search for this)" and no URL. An **empty**
  `## References` heading is a defect — omit the section entirely, or write
  `none — <why>` (a bare heading reads as an unfinished placeholder; the
  validator warns on it).
- **Tail-section order**: when present, the closing sections appear in the fixed
  order **References → Related → Sources** (References is omitted when empty).
  The validator warns on any other order.

## Completeness standard

A card must be able to **re-teach its topic months later without the
conversation**. Capture every distinct point the source actually covered —
all steps, the concrete examples, the command lines, the pitfalls, the
comparisons. Compressing a rich discussion into a thin digest is a defect:
brevity belongs to the diary's Summary field, not to cards or notes. When the
source compared or enumerated things, keep the table; when it walked a
process, keep every step.

### Depth: teach, don't digest

Where the source supports it, a `concept` / `term` / `howto` / `gotcha`
**teaches** the topic — it does not just name conclusions:

- the mechanism or *why*, not only the *what*;
- a breakdown of the load-bearing terms, parameters, or flags — name each token
  and say what it does;
- a self-standing worked example with concrete, teaching-chosen values.

Listing conclusions the reader must already understand in order to follow them is
the shallow-digest failure — it fails the re-teach test above.

**Destructive operations** take the strongest form of this. A command that can
irreversibly lose data (`reset --hard`, `rm -rf`, `branch -D`, `gc --prune`,
`push --force`, `DROP`, removing an inner `.git`, …) must never ship as a bare
command — vault content is trusted and copy-pasted. Teach it in five parts:

1. **Command breakdown** — the full command with every flag and argument
   explained, naming the mode/variant it belongs to (`--hard` vs `--soft` /
   `--mixed`).
2. **When it applies** — the exact right situations, and the wrong ones, each with
   the safer alternative.
3. **Consequences** — precisely what is lost versus preserved.
4. **Recovery** — written as if the command has ALREADY run and done its damage:
   ordered, followable steps for each recoverable case, and an explicit list of
   what is NOT recoverable.
5. **Cautions** — the read-only preflight to run first, how to confirm the precise
   target, and the traps.

### Enrichment versus provenance

A note can be no deeper than its source **unless** knowledge is added beyond the
conversation. That is allowed — but never silently, and never disguised as
session-verified fact:

- **Faithful first.** Capture everything the source actually reached, at full
  depth. Most thin notes fail here, not at enrichment: the source was rich and the
  extraction digested it. Fix that before adding anything.
- **Marked enrichment.** Knowledge added from the model to teach the topic fully
  sets the card to `confidence: discussed` (a card carrying any claim not verified
  in-session is never `verified`) and must carry a real `## References` entry
  backing the added claims. Never inject unsourced material under
  `source: conversation` + `confidence: verified`.
- **Thin-source stub.** When even enrichment would be guesswork — no session basis
  and no citable source — do not emit a confident shallow note. Write what is
  actually known and mark the gap with a `> [!todo] thin source — deepen in a
  future pass` callout, and flag it in the run report. Depth becomes a deliberate
  follow-up, not a silent gap.

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
1. [Conventional Commits](https://www.conventionalcommits.org/) — the `type(scope): subject` convention and its rationale.

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
