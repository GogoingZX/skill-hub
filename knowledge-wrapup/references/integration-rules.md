# Integration Rules

How cards become curated notes, and how the diary, taxonomy, and index are
maintained. Integration consumes cards only — never raw sources.

## Curated note format

One concept = one note file: `notes/<domain>/<topic>.md`. The filename equals the
card `topic` — that equality is what makes dedupe work.

```markdown
---
topic: git-commit-messages
domain: technology/tools
tags: [git, best-practice]
status: active            # active | disputed
spec_version: 1
---

# Writing Good Git Commit Messages

[Body sections mirror the card type's structure — see card-spec.md]

## References
- [Conventional Commits](https://www.conventionalcommits.org/) — the convention
  and its rationale.

## Sources
- conversation-claude/conversation-20260705.md (discussed)

## ⚠️ Pending verification
[Only present when there are unresolved conflicts]

---

## 中文翻译
[Translation section — heading in the target language; omit entirely when
language is "en"]
```

## Merge procedure, by relation

**new** — instantiate `assets/templates/note.md`, fill body from the card, list
the card's source in `## Sources`, place in `notes/<domain>/`, add an INDEX line.

**corroborates** — add one line to `## Sources` (nothing else changes). If the
note now has 2+ independent agreeing sources, you may note "(corroborated)" on
the source lines. Do not duplicate content.

**supplements** — append the new information to the appropriate existing section
(or add a section), with an inline source marker like
`*(source: guide.pdf#p12)*` on the added material. Re-do the translation section
as a whole afterwards so it matches the updated English body.

**conflicts** — never silently overwrite, never adjudicate:

```markdown
## ⚠️ Pending verification
- Cache TTL: conversation-20260705 says 5 minutes; guide.pdf#p12 says
  configurable. → verify which applies to the current version.
```

Set frontmatter `status: disputed`, keep the previously recorded claim in place,
and flag the conflict prominently in the run report. Evidence ordering when the
user asks for a recommendation: verified-by-running > official docs/PDF >
conversation discussion > unverified personal notes. The user is the final judge;
when they resolve a conflict, they (or a later run at their request) clear the
section and restore `status: active`.

**References merging** — union of the note's and card's links, deduped by URL,
kept as an **ordered list** (renumber after merging).

## User edits are first-class

The user may freely edit any note. When merging into an edited note, locate the
target sections tolerantly (heading text match, case-insensitive). If the note
has been restructured so far that the standard sections cannot be found, append
nothing, and report: "note X was restructured by the user; card Y left unmerged
(status stays raw)". Never reformat or "correct" user content.

## TAXONOMY.md

Machine-readable controlled vocabulary. Format contract:

- Level-1 domain: `## <slug>` heading (lowercase kebab-case)
- Level-2 subdomain: `- <slug>` list item under its domain
- Anything not matching those patterns (e.g. the `## Rules` section) is prose.

Rules:

1. Always classify into an existing domain if one fits. Create a new domain only
   when nothing fits; update TAXONOMY.md in the same run and announce it in the
   report.
2. Two levels maximum. Finer distinctions are expressed with tags, never deeper
   folders.
3. Split a level-2 subdomain out only when a subtopic has accumulated roughly
   8–10 notes; when splitting, move the affected notes and update INDEX.md paths.

## INDEX.md

One line per note, grouped by level-1 domain, alphabetical within a group:

```markdown
## technology
- [Writing Good Git Commit Messages](notes/technology/tools/git-commit-messages.md) — subject in imperative ≤50 chars; body explains why
```

The hook after the dash is a one-line reminder of the note's core point, not a
category label. Update the line when a note is significantly enriched.

## Diary entry format

`conversation-claude/conversation-{yyyyMMdd}.md` — one file per day, one appended
section per run. The section is **topic-structured**: one `### Topic:` block per
topic discussed, so the diary reads as a browsable digest, not a blob.
Instantiate `assets/templates/diary-section.md`:

```markdown
## 14:30 — one-line session headline

### Topic: Obsidian CLI (verified)

**Summary:** Official CLI since 1.12; ~100 commands; verified locally.

**Details:** Best where vault awareness matters — search for dedupe,
unresolved/orphans for graph maintenance. Example:
`obsidian vault="kb" search query="prompt caching"`.

**Open items:** [omit line if none]
**References:** https://obsidian.md/cli
**Card:** [[obsidian-cli]]

**中文:** [natural translation of Summary + Details]
```

Per-topic fields: Summary (1–2 sentences) → Details → Open items (omit if
none) → References (omit if none; **ordered list**, one-line annotation each)
→ Card wikilink (omit if none) → translation block. Even project-specific
topics that produce no card belong in the diary — it is the chronological
record; the gates apply to cards, not to the diary.

**Details must be complete, not compressed**: cover every distinct point the
topic's discussion actually made — the reasoning, the concrete examples (1–2),
the commands, the caveats. The reader should not need the original
conversation to reconstruct what was learned. Brevity lives in Summary;
Details is the record.

Append-only. Never modify existing sections, even to fix formatting. If today's
file is missing, create it fresh and mention that in the report.

## Presentation rules (notes and diary)

Optimize for scan-ability — the reader should get the structure at a glance.
Full typography rules live in `markdown-style.md` (binding); highlights:

0. **Enumerations and steps are markdown lists** (U1) — never substitute
   characters (①②③, •); soft-wrap constrains paragraphs, never list
   structure (U2): one list item = one line, never fold a list into a
   paragraph. **Translations mirror the source structure one-to-one**
   (U7): list for list, table for table; headings rewritten idiomatically,
   never word-stacked transliterations. Session war stories stay out of
   notes (U6) — one evidence line max.

1. **Comparisons and enumerations go in tables**, not prose lists: model/option
   comparisons, type vocabularies, decision shortcuts, do-vs-don't.
2. **Processes, decision trees, DAGs, and architectures go in Mermaid diagrams**
   (Obsidian renders ` ```mermaid ` natively): `flowchart` for decisions and
   pipelines, `sequenceDiagram` for interactions. Keep diagrams small (≤10
   nodes); label edges.
3. Prose remains for definitions, reasoning, and anything that needs nuance —
   don't force a diagram where two sentences are clearer.
4. In the translation section, translate table content; for diagrams, reference
   the English diagram instead of duplicating it (labels stay in English).

## Layout rules (reading experience)

5. **No walls of text.** Keep paragraphs short (a few sentences); multi-point
   content becomes bullets with blank lines between blocks. The diary's Details
   field is a bullet list, never one mega-paragraph. "Short" means few
   sentences, not few physical lines — see rule 7 on soft-wrapping.
6. **Callouts for emphasis** (Obsidian renders them natively):
   `> [!summary]` — one-liner at the top of every note and every diary topic;
   `> [!warning]` — pitfalls and gotchas. Use sparingly; two per document is
   usually plenty.
7. **Soft-wrap all prose — one paragraph/bullet = one physical line, for BOTH
   English and CJK.** Do not hard-wrap prose at a fixed column. Two reasons:
   (a) for CJK, a mid-sentence newline renders as a stray space and corrupts
   the text; (b) even for English, hard breaks do NOT reflow to the window
   width in Obsidian's Live Preview / Source view, so the text can't adapt to
   the reader's pane. Let the editor soft-wrap. This applies to paragraphs,
   list-item bodies, and callout content alike. (Code blocks, tables, and
   headings are unaffected — they keep their own line structure.)
8. **No duplicate H1s.** The translation section's title is a bold line, its
   section headings are H3 — the document outline stays clean.
9. **Separate diary topics with `---` rules** so each topic reads as a card.
10. **Code blocks vs inline code**: inline code is only for short fragments
    referenced inside a sentence (a command name, a flag, a path). Anything
    multi-line, anything with explanatory comments, and any command meant to
    be copy-pasted gets a fenced code block — **in the translation section
    too**. Code is language-neutral: duplicate the block verbatim in the
    translated section (comments may be translated); never compress a code
    block into inline code or replace it with "see the English section
    above" — both force the reader to jump or retype.

## Translation quality rules (when language ≠ "en")

Applied to notes and diary sections only — never cards.

1. Write the complete English content first; translate afterwards as a whole.
2. The translation must read as if originally written by a native speaker —
   idiomatic, natural register. Literal word-by-word translation is a defect.
3. Keep technical terms in English on first mention with the translation
   alongside, e.g. 提示词缓存(prompt caching); after that, use whichever reads
   naturally.
4. Code blocks, commands, URLs, and wikilinks are never translated.
5. The translation section lives at the bottom of the note under a `---` rule,
   heading in the target language (e.g. `## 中文翻译` for zh-CN). For diary
   entries, each topic block carries its own translation block (a
   bottom-of-file section would break append-only).
6. **The translation mirrors the English structure field for field** — same
   headings/labels in the target language, same field order, no merging
   structured fields into one paragraph. If the English format ever changes,
   the translation format changes with it in the same edit; a structure
   mismatch between the two is a defect. Language-neutral content (URLs,
   wikilinks, code) is not duplicated into the translation.
