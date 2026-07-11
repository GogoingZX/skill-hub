# Changelog — knowledge-wrapup

Format: [Keep a Changelog](https://keepachangelog.com/) spirit; versions follow
[SemVer](https://semver.org/) — MAJOR: breaks card/pipeline compatibility,
MINOR: adds behavior rules, PATCH: wording/fix only.

> Precision note: versions 1.0.0–1.4.0 predate this repo's git history and are
> reconstructed retroactively; timestamps are deliberately coarse
> ("date + period") because exact times were not recorded. From v1.4.0 on,
> git history is the precise source of truth.

## [1.8.1] — 2026-07-11

### Changed
- Example/Steps rule (card-spec): examples are written in best-practice form
  from the start; load-bearing practices are named explicitly with what they
  prevent. Trigger: the decorators note initially shipped its example without
  `@functools.wraps` — the canonical practice was missing precisely where a
  beginner would copy from (user proposal, approved 2026-07-11).

## [1.8.0] — 2026-07-11

### Changed
- Gate 2 (non-trivial) gains the **fundamentals exception**: well-documented
  textbook material passes when the conversation shows personal friction
  evidence (repeated questions / misunderstanding / learned-and-forgotten);
  such notes are tagged `fundamentals`, filed by subject domain (no generic
  "learning" folders), and written around the friction point. Rationale
  (user decision, 2026-07-11): one vault as SSOT beats a separate cheatsheet
  layer whose read-time routing cost compounds; the friction requirement
  keeps the signal-to-noise line versus official docs.

## [1.7.0] — 2026-07-07

### Added
- Spec-governance ground rule (user-mandated after a real deviation): the
  spec binds during execution; mid-run friction is flagged and proposed,
  never self-resolved; rule changes require prior user approval. Trigger
  incident: a diary section was written Chinese-only against the bilingual
  convention, then a post-hoc rule change was offered — rejected.

## [1.6.0] — 2026-07-07

### Added
- Code-presentation rule (layout rule 10): inline code only for short
  fragments inside a sentence; anything multi-line, commented, or
  copy-paste-ready gets a fenced code block — in the translation section too.
  Code is language-neutral: duplicate blocks verbatim (comments may be
  translated); never compress a block into inline code or replace it with a
  "see the English section above" reference.

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
