---
name: knowledge-wrapup
version: 1.4.0
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
conversation ──→ diary   (conversation-claude/)              [write-only record]
             └─→ cards   (cards/)  ──→  notes (notes/) + INDEX.md + TAXONOMY.md
```

Two invocation forms:

- `/knowledge-wrapup` — wrap up the current conversation (diary + cards + integration)
- `/knowledge-wrapup <file-or-folder>` — extract from the user's own file(s): notes,
  a PDF, etc. Same pipeline, but no diary entry is written.

## Step 0 — Configuration

Read `~/.config/knowledge-wrapup/config.json`:

```json
{ "vault_path": "~/Desktop/knowledge-base", "language": "zh-CN" }
```

- **Config missing = first run.** Ask the user two questions: (1) where should the
  knowledge base live (absolute path), (2) localization language (`en` means
  English-only output; any other language code means English body + a translation
  section in that language). Then write the config file.
- **Ensure the vault skeleton exists** — create only what is missing, never modify
  what exists: `INDEX.md`, `TAXONOMY.md` (copy the starter from
  `assets/templates/TAXONOMY.md`), `conversation-claude/`, `cards/`, `notes/`.
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
   conversation. Common knowledge fails this gate.
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

For each surviving candidate, search existing notes (scope: `notes/` only —
never match against `cards/`):

```bash
obsidian vault="<vault-name>" search query="<topic keywords>"
# If the Obsidian CLI is unavailable, fall back to:
grep -ril "<topic keywords>" <vault_path>/notes/
```

Classify the candidate's relation to the vault — exactly one of four:

| Relation | Meaning | What integration will do |
|---|---|---|
| **new** | no existing note covers it | create a note |
| **corroborates** | same content already recorded | add a source line only; no new content |
| **supplements** | new information, no contradiction | append to the existing note, cite source |
| **conflicts** | contradicts the existing note | record both claims, never silently overwrite |

Running the skill twice on the same conversation is safe by construction: the
second run's candidates land on **corroborates** and are skipped.

## Step 4 — Write cards

One card per surviving candidate, instantiated from the matching template in
`assets/templates/` (card-concept, card-term, card-howto, card-gotcha,
card-tutorial). Full schema, naming rules, and worked examples (including
counter-examples of what NOT to extract): read `references/card-spec.md`.

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

## Step 5 — Integrate

Follow `references/integration-rules.md` for the exact note format, merge
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
5. Update `INDEX.md` (one line per note) and flip integrated cards to
   `status: merged`.
6. Notes and diary get a translation section when `language` is not `en`;
   cards never do.
7. **The user's manual edits are first-class.** Merge into their structure as
   best you can; if a note has been restructured beyond recognition, say so in
   the report instead of "fixing" it.

## Step 5b — Diary (conversation mode only)

Append one section to
`<vault_path>/conversation-claude/conversation-{yyyyMMdd}.md`, instantiated from
`assets/templates/diary-section.md` — topic-structured: one `### Topic:` block
per topic (Summary / Details with 1–2 examples / Open items / References /
Card), exact format and presentation rules (tables, Mermaid diagrams) in
`references/integration-rules.md`. Rules:

- **Append-only.** Never parse, rewrite, or reformat existing content — the user
  may have edited it, and their edits stay untouched.
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
5. Provenance integrity: check that all `source_ref` targets in the vault still
   exist; list broken links as a warning (knowledge is unaffected; only
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
