# knowledge-wrapup

A Claude Code skill that turns your conversations (and your own notes/PDFs) into
a curated, Obsidian-friendly knowledge base — via a strict "knowledge card"
middleware layer.

## What it does

```
conversation ──→ diary   (conversation-claude/)          chronological record
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

It then creates the missing skeleton (`INDEX.md`, `TAXONOMY.md`,
`conversation-claude/`, `cards/`, `notes/`) without touching existing files.

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
├── references/
│   ├── card-spec.md             # card schema + examples + counter-examples
│   └── integration-rules.md     # merge rules, formats, translation quality
├── scripts/validate_card.py     # hard validation gate for every card
├── assets/templates/            # card/note/diary/taxonomy templates
└── evals/                       # regression test conversations
```

## Maintenance

- `TAXONOMY.md` in your vault is the classification vocabulary — edit it freely;
  the skill announces any domain it adds.
- After modifying SKILL.md, re-run the conversations in `evals/` and compare
  outputs — that's the regression check against capability drift.
- Versioning: SemVer in SKILL.md frontmatter (`version:`) + CHANGELOG.md.
  Bump MINOR for new behavior rules, PATCH for wording fixes, MAJOR if card
  or pipeline compatibility breaks; tag releases in git.
