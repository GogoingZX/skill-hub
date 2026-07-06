# Changelog — knowledge-wrapup

Format: [Keep a Changelog](https://keepachangelog.com/) spirit; versions follow
[SemVer](https://semver.org/) — MAJOR: breaks card/pipeline compatibility,
MINOR: adds behavior rules, PATCH: wording/fix only.

> Precision note: versions 1.0.0–1.4.0 predate this repo's git history and are
> reconstructed retroactively; timestamps are deliberately coarse
> ("date + period") because exact times were not recorded. From v1.4.0 on,
> git history is the precise source of truth.

## [1.5.0] — 2026-07-07

### Added
- "Links follow content" rule for Related wikilinks: a dangling link must
  promise a three-gate-passing note. No habitual links to project machinery,
  tool-overview placeholders, or unrequested hub pages. Dangling-link
  dispositions codified: fill / leave as signpost / delete — never write a
  thin note just to clear the unresolved list. (Distilled from three real
  cleanups: knowledge-base-automation, the obsidian MOC proposal, [[obsidian]].)

## [1.4.0] — 2026-07-05 (late evening) / 2026-07-06 (early)

### Added
- Layout rules for reading experience: `> [!summary]` callout per note/diary
  topic, `> [!warning]` for gotchas, no walls of text, `---` between diary
  topics, translation sections demote headings (no duplicate H1).
- **CJK no-hard-wrap rule**: one Chinese paragraph = one physical line
  (renderers turn newlines into spaces, corrupting CJK text).
- Decision-table format pinned in Step 6: fixed column structure
  (`# | Candidate | Reusable | Non-trivial | Self-contained | Relation |
  Outcome`), fixed cell conventions, no ad-hoc symbols — closing a drift
  observed across three real runs.

## [1.3.0] — 2026-07-05 (evening)

### Added
- Completeness standard: cards/notes must re-teach the topic without the
  conversation; brevity belongs to the diary Summary field only.
- References switched to ordered lists everywhere (cards, notes, diary),
  renumbered after merging.

## [1.2.0] — 2026-07-05 (afternoon)

### Added
- Tag governance: `## Tags` controlled registry in TAXONOMY.md; validator
  rejects unregistered tags and tags duplicating the note's domain;
  target 2–4 tags per card (hard limit 1–5); reuse-first, register-and-announce
  for new tags.

## [1.1.0] — 2026-07-05 (afternoon)

### Added
- Diary restructured to topic blocks: `### Topic:` × (Summary / Details /
  Open items / References / Card), project-only topics included.
- Presentation rules: tables for comparisons/enumerations, Mermaid for
  flows/DAGs/architecture.
- Translation mirroring rule: translations mirror the English structure field
  for field; structure mismatch is a defect; language-neutral content (URLs,
  wikilinks, code) not duplicated.

### Changed
- Taxonomy: `technology/git` and `technology/obsidian` split out by user
  direction; rule 3 amended to allow user-directed splits.

## [1.0.0] — 2026-07-05 (morning)

### Added
- Initial release: four-layer pipeline (sources → diary → cards → notes),
  three extraction gates, four merge relations with conflict surfacing,
  `validate_card.py` hard gate, five card templates, bilingual output,
  config-driven first-run setup, regression evals.
- Same-day same-topic rule codified from testing: extend the existing card
  (raw → re-validate → re-integrate) instead of inventing a second filename.
