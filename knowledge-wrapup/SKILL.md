---
name: knowledge-wrapup
description: >
  Extract reusable knowledge from the current conversation (or from a user-provided
  file) into knowledge cards, then integrate them into the user's Obsidian knowledge
  base: append a diary entry, dedupe and merge into curated notes, update the index
  and taxonomy. Trigger ONLY when the user explicitly invokes /knowledge-wrapup or
  explicitly asks to save/wrap up this conversation's knowledge into their knowledge
  base. Never trigger proactively — this skill writes files into the user's vault.
---

# knowledge-wrapup

Turn valuable conversation content into a growing, curated knowledge base.

Data flows one way. The diary is a write-only record, never an input; cards are the
only thing integration consumes:

```
conversation ──→ diary   (conversation-<agent>/)             [write-only record]
             └─→ cards   (cards/)  ──→  notes (notes/) + INDEX.md + TAXONOMY.md
```

`<agent>` names the executor: `conversation-claude/` when run under Claude,
`conversation-codex/` under Codex. Historical diary directories are never
renamed — provenance paths stay valid.

Two invocation forms — under Claude the explicit form is `/knowledge-wrapup`,
under Codex it is `$knowledge-wrapup` (implicit invocation is disabled via
`agents/openai.yaml`; a natural-language request counts as explicit only when
it literally asks to wrap/save knowledge into the vault):

- `/knowledge-wrapup` — wrap up the current conversation (diary + cards + integration)
- `/knowledge-wrapup <file-or-folder>` — extract from the user's own file(s): notes,
  a PDF, etc. Same pipeline, but no diary entry is written.

File-mode source rules (so the same input yields the same source set on any run):

- Supported inputs: Markdown / plain text (`.md`, `.txt`) and PDF. Every other
  file is listed in the report as unsupported — never guessed at.
- A folder is processed recursively in lexicographic path order; hidden files
  and symlinks are skipped.
- Unreadable or failed files are explicit warnings in the report, never silent
  skips.
- PDF provenance carries a page locator (`source_ref: "guide.pdf#p12"`);
  scanned (image-only) or encrypted PDFs are reported as unsupported rather
  than half-extracted.

## Step 0 — Configuration

Read `~/.config/knowledge-wrapup/config.json`:

```json
{ "vault_path": "~/Desktop/knowledge-base", "language": "zh-CN", "vault_name": "knowledge-base" }
```

`vault_name` (optional) is the vault's registered name in Obsidian, used by the
CLI search in Step 3; when absent, default to the last path component of
`vault_path`.

- **Config missing = first run.** Ask the user two questions: (1) where should the
  knowledge base live (absolute path), (2) localization language (`en` means
  English-only output; any other language code means English body + a translation
  section in that language). Then write the config file.
- **Ensure the vault skeleton exists** — create only what is missing, never modify
  what exists: `INDEX.md`, `TAXONOMY.md` (copy the starter from
  `assets/templates/TAXONOMY.md`), the executing agent's `conversation-<agent>/`
  directory, `cards/`, `notes/`.
- On first initialization only, suggest to the user (do not change settings
  yourself): enable Obsidian's File Recovery core plugin, and add `cards/` to
  Settings → Files & links → Excluded files, so the intermediate card layer does
  not pollute search results and the graph.

## Step 1 — Extract candidates

Input: the current conversation, or the file given as argument.

Sweep the whole input in order. Any segment that *explains a concept or term,
teaches a procedure, records a pitfall, or verifies a fact* becomes a candidate.
Be generous at this stage — filtering happens next, not here.

## Step 2 — Filter through the three gates

A candidate is extracted only if it passes **all three**:

1. **Reusable** — still useful in a different project six months from now.
2. **Non-trivial** — something the user could not have written down before the
   conversation. Common knowledge fails this gate — with one exception:
   **well-documented fundamentals** (textbook / official-doc material) pass
   when the conversation shows personal friction evidence — the user asked
   repeatedly, misunderstood, or had learned-and-forgotten it. "Looks core"
   is not evidence; "it stalled the user" is. Such notes are tagged
   `fundamentals`, filed by subject domain (e.g. technology/python — never a
   generic "learning" folder), and written around the friction point (what
   confused the user and why), never as tutorial re-narration.
3. **Self-contained** — understandable without the conversation's context.

Explicitly excluded, regardless of gates: project-specific decisions and paths,
code fixes tied to one repository, the user's preferences and opinions (that is
what memory is for), anything already fully covered by an existing note, and
process chatter.

Record every candidate's gate results in a decision table (shown in the final
report — see Step 6). **Zero surviving candidates is a valid outcome**; report
"nothing worth extracting" honestly instead of manufacturing filler. A typical
conversation yields 0–5 cards.

## Step 3 — Dedupe against the vault

First list today's already-written cards (`ls <vault_path>/cards/*--{yyyyMMdd}.md`)
so a same-day sibling session's extractions are visible upfront instead of being
discovered as collisions card-by-card.

Then, for each surviving candidate, search existing notes (scope: `notes/` only —
never match against `cards/`):

```bash
obsidian vault="<vault_name>" search query="<topic keywords>"
# If the command FAILS or is missing (e.g. Obsidian isn't running),
# fall back to filesystem search — prefer rg, then grep:
rg -il "<topic keywords>" <vault_path>/notes/
grep -ril "<topic keywords>" <vault_path>/notes/
```

An existing executable is not proof the CLI works — it needs a running Obsidian.
Pick the search backend once per run and name it in the final report.

Classify the candidate's relation to the vault — exactly one of four:

| Relation | Meaning | What integration will do |
|---|---|---|
| **new** | no existing note covers it | create a note |
| **corroborates** | same content already recorded | add a source line only; no new content |
| **supplements** | new information, no contradiction | append to the existing note, cite source |
| **conflicts** | contradicts the existing note | record both claims, never silently overwrite |

Running the skill twice on the same conversation is safe by construction — but
a replayed source is a **duplicate, not corroboration**: if the note's Sources
already list the same `source_ref`, skip the candidate entirely (no source line,
no diary append) and say so in the report. `corroborates` is reserved for an
*independent* source that agrees (details in `references/integration-rules.md`).

## Step 4 — Write cards

One card per surviving candidate, instantiated from the matching template in
`assets/templates/` (card-concept, card-term, card-howto, card-gotcha,
card-tutorial). Full schema, naming rules, and worked examples (including
counter-examples of what NOT to extract): read `references/card-spec.md`.
All output typography (lists, characters, Mermaid labels, math, bilingual
structure) follows `references/markdown-style.md` — its machine-checkable
subset is enforced by the validator below.

Cards are English-only. External links go in the card's `## References` section —
official docs and high-quality tutorials, 0–3 per card. **Never invent a URL**:
include only links that actually appeared in the conversation or canonical
official domains you are certain of; otherwise give the resource name with a
"(search for this)" note and no URL.

Then validate every card — this is a hard gate, not a formality:

```bash
python3 scripts/validate_card.py <card-file>... --vault <vault_path>
```

Fix and re-validate until clean. A card that fails validation must not proceed
to integration.

## Step 4b — Work card-by-card, not in batches

For each surviving candidate, complete the full unit before starting the
next: write the card → validate it → integrate its note (Step 5) → lint the
note. Do NOT write all cards first and all notes afterwards — on large runs
quality decays at the tail of each batch (observed 2026-07-16: translation
defects concentrated in the later notes of a 14-card batched run). After a
run of more than ~8 cards, additionally re-read the LAST THIRD of the
translation sections against markdown-style U7 before reporting.

## Step 5 — Integrate

Follow `references/integration-rules.md` (and `references/markdown-style.md`
for typography) for the exact note format, merge
procedure per relation, conflict handling, translation quality rules, and
TAXONOMY/INDEX maintenance. In brief:

1. Apply each card to `notes/<domain>/` per its Step-3 relation. One concept =
   one note file; the note's filename is the card's `topic`.
2. Classify into an existing TAXONOMY.md domain whenever possible. Creating a
   new domain is allowed but must update TAXONOMY.md and be announced in the
   report. Two folder levels maximum.
3. Conflicts go into the note's `## ⚠️ Pending verification` section with both
   claims and sources, and the note's frontmatter gets `status: disputed`.
4. Merge card References into the note (dedupe by URL).
5. Update `INDEX.md` — one line per note, via
   `scripts/update_index.py --vault … --note … --title … --summary …`
   (idempotent: refreshes an existing line instead of duplicating) — and
   flip integrated cards to `status: merged`.
5b. Lint every note you created or touched:
   `python3 scripts/validate_note.py <note>... --language <config language>
   --vault <vault_path>` — a failing note blocks completion (fix and
   re-lint), same hard-gate status as card validation.
6. Notes and diary get a translation section when `language` is not `en`;
   cards never do.
7. **The user's manual edits are first-class.** Merge into their structure as
   best you can; if a note has been restructured beyond recognition, say so in
   the report instead of "fixing" it.

## Step 5b — Diary (conversation mode only)

Append one section to
`<vault_path>/conversation-<agent>/conversation-{yyyyMMdd}.md`, instantiated from
`assets/templates/diary-section.md` — topic-structured: one `### Topic:` block
per topic (Summary / Details with 1–2 examples / Open items / References /
Card), exact format and presentation rules (tables, Mermaid diagrams) in
`references/integration-rules.md`. Rules:

- **Append-only.** Never parse, rewrite, or reformat existing content — the user
  may have edited it, and their edits stay untouched. Because appended text is
  immutable afterwards, **validate the staged section BEFORE appending** — write
  it to a temp file and run
  `python3 scripts/validate_diary.py <staged-file> --language <config language>`
  (hard gate: fix and re-validate until clean) — a defect that lands in the
  diary stays there.
- **Rerun guard.** If today's diary already contains a section for this same
  session (same topics from the same conversation — e.g. the skill was rerun),
  skip the append and say so in the report instead of recording the session twice.
- File missing (even if it existed earlier today)? Create it fresh with just this
  section and mention that in the report. Do not attempt recovery.

## Step 6 — Report

End with a summary in the chat, containing:

1. The decision table, in EXACTLY this column structure (headers may be
   localized to the chat language, but order and semantics are fixed —
   never merge the three gate columns into one):

   | # | Candidate | Reusable | Non-trivial | Self-contained | Relation | Outcome |

   Cell conventions: gates use ✅ / ❌ (with a ≤4-word reason on the failing
   gate); hard-excluded categories mark ❌ in Reusable with the category
   (e.g. "❌ project-specific"), remaining gates "—"; gates not evaluated
   because an earlier one failed use "—"; Relation is one of
   new/corroborates/supplements/conflicts or "—" for dropped candidates.
   No ad-hoc symbols beyond these.
2. Counts: cards written, notes created, notes enriched, corroborations, conflicts.
3. Conflicts, if any — flagged prominently for the user to resolve.
4. New taxonomy domains, if any.
5. Provenance integrity: run `scripts/check_provenance.py --vault …` —
   it checks that all `source_ref` targets in the vault still exist and
   lists broken links as a warning (knowledge is unaffected; only
   traceability is lost). Report only — never repair or delete.
6. Knowledge gaps: output of `obsidian unresolved` (or note it if CLI unavailable).

## Ground rules (apply everywhere)

- Write only inside the vault (plus the config file). Never modify Obsidian
  settings, never touch the user's source files.
- The skill owns: new cards, card `status` flips, its own appends to notes/INDEX/
  TAXONOMY/diary. Everything else in the vault belongs to the user.
- Conflicting knowledge is surfaced, never adjudicated silently. When ordering
  evidence, prefer: verified-by-running > official docs/PDF > conversation
  discussion > unverified notes — but the user is the final judge.
- All generated English is written first and completely; translation (if enabled)
  is done afterwards as a whole, natural and idiomatic, never literal. Details in
  `references/integration-rules.md`.
- **The spec is binding during execution — no self-authorized deviations.**
  If a rule feels wrong mid-run, follow it anyway, flag the friction in the
  report, and propose a change; the change happens only after the user
  approves, never before. Deviating first and legitimizing afterwards is the
  exact degradation pattern this skill's defenses exist to prevent — and the
  executor itself is a degradation vector those defenses cannot script away.
