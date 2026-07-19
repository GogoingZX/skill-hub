# knowledge-wrapup

An agent skill (Claude Code and Codex) that turns your conversations (and your
own notes/PDFs) into a curated, Obsidian-friendly knowledge base — via a strict
"knowledge card" middleware layer.

## What it does

```
conversation ──→ diary   (conversation-<agent>/)         chronological record
             └─→ cards   (cards/)                        normalized middleware
                          └──→ notes (notes/)            curated knowledge base
                               + INDEX.md + TAXONOMY.md
```

One command runs the whole pipeline: extract knowledge from the current
conversation, filter it through strict boundaries, dedupe against your existing
notes, merge (verify / supplement / flag conflicts), write a diary entry, and
update the index.

## Usage

| Command | Effect |
|---|---|
| `/knowledge-wrapup` | Wrap up the current conversation: diary + cards + integration |
| `/knowledge-wrapup <file-or-folder>` | Extract from your own notes or a PDF (no diary entry) |

Under Codex the explicit form is `$knowledge-wrapup`; implicit invocation is
disabled (`agents/openai.yaml`), so the skill never fires from a prompt match.

Run it whenever a valuable discussion wraps up — running twice on the same
conversation is safe (duplicates are recognized and skipped). Zero cards is a
normal outcome for casual conversations.

## First run

The skill asks two questions and remembers the answers in
`~/.config/knowledge-wrapup/config.json`:

1. **Vault path** — where the knowledge base lives (an Obsidian vault or any folder).
2. **Language** — `en` for English-only output; any other language code (e.g.
   `zh-CN`) keeps English as the writing language and appends a natural,
   native-quality translation to notes and diary entries.

A third, optional key — `vault_name`, the vault's registered name in Obsidian —
defaults to the last component of the vault path.

It then creates the missing skeleton (`INDEX.md`, `TAXONOMY.md`, the agent's
`conversation-<agent>/` directory, `cards/`, `notes/`) without touching
existing files.

Recommended one-time Obsidian settings (the skill suggests, never changes them):

- Enable the **File Recovery** core plugin — protects against accidental deletions.
- Add `cards/` to **Settings → Files & links → Excluded files** — keeps the
  middleware layer out of search results and the graph.

## What gets extracted (and what doesn't)

Extracted only if **all three** hold: reusable in other projects, non-trivial
(you couldn't have written it before the conversation), and self-contained.
Never extracted: project-specific decisions, single-repo code fixes, personal
preferences, things your notes already cover, small talk.

Every run ends with a decision table showing each candidate and why it was
kept or dropped — quality stays auditable.

## Your files, your rules

- The diary is **append-only**; the skill never rewrites what's there. Edit it freely.
- Notes are yours to edit; the skill merges into them and never "corrects" you.
  If a note is restructured beyond recognition, the skill reports instead of guessing.
- Deleted a diary file? Nothing breaks — knowledge lives in cards and notes; only
  the provenance trail is affected, and the run report will tell you. Recovery:
  `obsidian history:restore` (File Recovery) or Obsidian Sync.
- Conflicting information from different sources is never silently resolved: both
  claims are recorded under **⚠️ Pending verification** and flagged to you.

## Layout

```
knowledge-wrapup/
├── SKILL.md                     # pipeline the model follows
├── agents/openai.yaml           # Codex metadata (explicit invocation only)
├── references/
│   ├── card-spec.md             # card schema + examples + counter-examples
│   ├── integration-rules.md     # merge rules, formats, translation quality
│   └── markdown-style.md        # universal typography rules (U1–U7)
├── scripts/
│   ├── validate_card.py         # hard gate for every card
│   ├── validate_note.py         # hard gate for every touched note
│   ├── validate_diary.py        # hard gate for the staged diary section
│   ├── update_index.py          # sorted, bounded INDEX.md maintenance
│   └── check_provenance.py      # report-only source_ref integrity check
├── assets/templates/            # card/note/diary/taxonomy templates
├── evals/                       # regression protocol + fixture vault + assertions
└── tests/                       # unit tests for the scripts (python3 -m unittest)
```

## Maintenance

- `TAXONOMY.md` in your vault is the classification vocabulary — edit it freely;
  the skill announces any domain it adds.
- **One canonical home per rule.** Every rule lives in exactly one file
  (typography → markdown-style.md, card schema → card-spec.md, merge/formats →
  integration-rules.md, pipeline flow → SKILL.md). Any other file may restate
  it only as a one-line summary plus a pointer — never a reworded full copy,
  and examples must demonstrate the canonical form. When a restatement and its
  canonical home disagree, the restatement is the defect (the ordered-References
  example drift fixed in 1.9.0 was this class).
- After modifying scripts, run `python3 -m unittest discover -s tests`. After
  modifying SKILL.md or references, run the regression protocol in
  `evals/README.md` against a scratch vault — never the real one.
- Versioning: CHANGELOG.md is the single version source (SemVer — MINOR for
  new behavior rules, PATCH for wording fixes, MAJOR if card or pipeline
  compatibility breaks); tag releases in git. SKILL.md carries no version field.
