---
title: knowledge-wrapup Codex Compatibility and Reliability Review
status: implemented
implemented_in: "1.9.0 (2026-07-19) — KW-01…KW-10 all addressed; KW-03/KW-04/KW-07/KW-08 landed lighter than proposed (rule-level idempotency instead of run manifests; selective validator depth; source rules in SKILL.md instead of an adapter spec; assertion checklists + script unit tests instead of a full harness). See CHANGELOG 1.9.0."
reviewed_at: "2026-07-19"
review_scope: read-only review of skill instructions, references, scripts, templates, evaluations, and Codex compatibility
implementation_changes: none
---

# knowledge-wrapup Codex Compatibility and Reliability Review

## Purpose

This document records issues and optimization proposals identified during a read-only review of `knowledge-wrapup`. It is decision material, not an implementation specification. No skill implementation, configuration, knowledge-vault, or Claude memory file was changed during the review.

## Executive summary

The skill has a strong core architecture: a one-way diary/card/note pipeline, explicit extraction gates, four integration relationships, card-by-card execution, conflict preservation, user-edit protection, and deterministic validation scripts. The most valuable next step is a narrow Codex compatibility layer that preserves the existing knowledge pipeline. Reliability changes involving idempotency, provenance, or schema evolution should be reviewed separately because they can affect existing cards and notes.

Recommended order:

1. Add Codex discovery and invocation metadata without changing pipeline semantics.
2. Align the declared specification with validators and helper scripts.
3. Make repeated and interrupted runs genuinely idempotent.
4. Define cross-agent provenance and deterministic source adapters.
5. Turn evaluation inputs into executable regression tests.

## Verified current state

- The source skill is installed for Claude through `~/.claude/skills/knowledge-wrapup`, which points to this directory.
- No corresponding user skill exists under Codex's current discovery path, `$HOME/.agents/skills/knowledge-wrapup`.
- The existing configuration file contains `vault_path` and `language`; the configured language is `zh-CN`.
- The knowledge vault, `INDEX.md`, `TAXONOMY.md`, `cards/`, `notes/`, and `conversation-claude/` exist.
- All four Python scripts pass Python abstract-syntax-tree parsing and expose working command-line help.
- The Obsidian CLI executable exists, but it could not connect during the review because Obsidian was not running. The filesystem-search fallback therefore remains operationally important.
- Codex's bundled quick validator could not run because the local Python environment lacks PyYAML. A direct audit of the validator rules nevertheless established that the current `version` frontmatter key is outside its accepted property set.

## Strengths to preserve

- The diary is a chronological record, cards are normalized middleware, and curated notes are the knowledge product.
- The reusable, non-trivial, and self-contained gates create a strong signal-to-noise boundary.
- Zero surviving candidates is explicitly acceptable, preventing manufactured filler.
- Project decisions, repository-specific fixes, user preferences, and already-covered material are excluded from the knowledge layer.
- New, corroborating, supplementary, and conflicting information receive different integration behavior.
- Conflicts remain visible instead of being silently adjudicated.
- User edits are first-class and are not reformatted or overwritten when the expected structure cannot be found safely.
- Processing one card through validation and integration before starting the next reduces tail-quality degradation.
- Validators and helper scripts are dependency-light and suitable for deterministic enforcement.
- `SKILL.md` is below the recommended size threshold, while detailed rules live in directly referenced files.

## Finding KW-01: Codex discovery and invocation are not configured

Priority: P0

### Current state

- The skill is discoverable by Claude but not by Codex.
- The documented invocation forms are `/knowledge-wrapup` and `/knowledge-wrapup <file-or-folder>`.
- Codex uses `$knowledge-wrapup` or a skill picker for explicit invocation and may also invoke a skill implicitly when its description matches.
- The skill intentionally requires explicit invocation because it writes to the private knowledge vault.

### Problem and evidence

Future Codex sessions cannot discover the skill from its current Claude-only symlink. If it is installed without an invocation policy, Codex's default implicit-invocation behavior would rely only on the natural-language warning in `description`, which is weaker than a machine-readable prohibition.

Evidence:

- [`SKILL.md`](../SKILL.md) describes only the Claude-style slash invocation.
- Codex's user-level discovery location is `$HOME/.agents/skills`, and Codex supports symlinked skill folders.
- `agents/openai.yaml` is currently absent.

### Why change

The desired behavior is native Codex discovery without accidental vault writes. Discovery and invocation safety should be enforced by the Codex skill interface rather than left entirely to model interpretation.

### Concrete change

1. Add a user-level symlink at `$HOME/.agents/skills/knowledge-wrapup` pointing to this source directory.
2. Add `agents/openai.yaml` with user-facing metadata and `policy.allow_implicit_invocation: false`.
3. Document `$knowledge-wrapup` as the Codex explicit form while retaining `/knowledge-wrapup` for Claude.
4. Keep natural-language requests valid only when they explicitly ask to write or wrap knowledge into the vault.

### Expected outcome

- Codex lists the skill in selectors and can load it through progressive disclosure.
- Ordinary requests to summarize a conversation do not trigger vault writes.
- Claude and Codex use one source directory rather than maintaining diverging copies.

### Before and after

| Aspect | Before | After |
|---|---|---|
| Claude discovery | Available through a symlink | Unchanged |
| Codex discovery | Not available | Available through a user-level symlink |
| Codex explicit invocation | Not documented | `$knowledge-wrapup` is documented |
| Implicit invocation | Controlled only by prose | Disabled by machine-readable policy |

### Costs and risks

- Codex may need to restart if the new skill does not appear immediately.
- Both Claude and Codex should be tested after any shared `SKILL.md` change.
- Filesystem writes to the vault and config paths may still require explicit Codex sandbox approval.

## Finding KW-02: Version metadata has drifted and is not Codex-portable

Priority: P0

### Current state

- [`SKILL.md`](../SKILL.md) declares `version: 1.7.0`.
- [`CHANGELOG.md`](../CHANGELOG.md) records versions 1.8.0 and 1.8.1.
- The local Codex skill validator accepts a constrained frontmatter property set that does not include a top-level `version` key.

### Problem and evidence

The declared version is stale and prevents a clean Codex validation result under the current validator rules. Two locations currently claim to be part of the versioning system but disagree.

### Why change

A single canonical version prevents ambiguous releases and makes cross-client compatibility checks reproducible.

### Concrete change

Choose one of the following approaches:

1. Recommended for a locally authored skill: remove the top-level `version` field from `SKILL.md` and treat release tags or `CHANGELOG.md` as the canonical version source.
2. If runtime metadata is still needed, place the version in a field accepted by both target clients and generate it from one canonical source.
3. Add a validation check that fails when the canonical release version and documented latest changelog entry disagree.

### Expected outcome

- Codex validation is no longer blocked by an unexpected frontmatter key.
- The skill has one authoritative version rather than two competing values.

### Before and after

| Aspect | Before | After |
|---|---|---|
| `SKILL.md` version | 1.7.0 | Removed or generated from the canonical source |
| Latest changelog version | 1.8.1 | Remains canonical or is generated consistently |
| Codex frontmatter compatibility | Fails the property-set rule | Passes the property-set rule |

### Costs and risks

- Claude compatibility should be checked before changing the frontmatter contract.
- Moving version metadata may require adjusting existing release documentation.

## Finding KW-03: Repeated runs are not fully idempotent

Priority: P0

### Current state

- The skill states that running it twice on the same conversation is safe.
- The diary is append-only and writes one section per run.
- A candidate matching existing content is classified as `corroborates`, which adds a source line.
- Same-day cards can be reopened and reintegrated.

### Problem and evidence

Card creation may avoid duplicate filenames, but the complete run is not guaranteed to be a no-op:

- The same conversation can append a duplicate diary section.
- The same source can be added again to a note's Sources section.
- Reprocessing the same source as `corroborates` can incorrectly make one source look like independent corroboration.
- A failure halfway through the card-by-card pipeline can leave a partially integrated run with no explicit resume record.

### Why change

Idempotency should apply to all externally visible vault changes, not only card filenames. Without a stable source identity, repeated runs can inflate evidence and complicate recovery.

### Concrete change

1. Compute a stable source fingerprint for each invocation, based on the normalized input plus the source identity.
2. Record a `run_id` and source fingerprint in a small run manifest or equivalent ledger.
3. Treat the same source and same content as `duplicate`, which produces no note or provenance mutation.
4. Reserve `corroborates` for an independent source that agrees with an existing claim.
5. Deduplicate Sources entries using normalized source identity rather than visible text alone.
6. Record per-card completion so an interrupted run can resume without replaying completed mutations.
7. Prevent a second diary append for an already-recorded source fingerprint.

### Expected outcome

- Running the same input twice produces zero additional vault changes.
- Corroboration counts represent independent evidence.
- Interrupted runs can continue safely from the last completed unit.

### Before and after

| Scenario | Before | After |
|---|---|---|
| Same conversation rerun | Cards may dedupe, but diary and Sources may repeat | Entire run is a no-op |
| Independent agreeing source | Uses `corroborates` | Still uses `corroborates` |
| Identical source replay | May look like corroboration | Classified as `duplicate` |
| Mid-run failure | Partial state with manual reasoning required | Explicit resumable checkpoint |

### Costs and risks

- A run manifest and source fingerprint introduce additional state.
- Adding `duplicate`, `run_id`, or source identity fields may require card schema version 2.
- Existing cards should not be rewritten silently; migration should be additive or performed through a reviewed one-time tool.

## Finding KW-04: The validators do not enforce the complete written contract

Priority: P0

### Current state

- `validate_card.py` checks required frontmatter fields, enums, basic slugs, filename consistency, domain and tag membership, required section presence, and selected Markdown rules.
- `validate_note.py` checks a smaller note contract, summary presence, translation presence, selected Markdown rules, and limited translation-structure counts.
- Diary text has no dedicated command-line validator even though appended text is immutable by policy.

### Problem and evidence

Several written requirements remain unenforced:

- Card section order is required by the specification, but the validator only checks whether each heading appears somewhere.
- Date strings are pattern-checked but not validated as real calendar dates.
- Card H1 presence, duplicate headings, unknown frontmatter fields, source locator format, and References list style are not fully checked.
- Note `spec_version`, domain, and tag values are not validated to the same depth as cards.
- The translation-heading regular expression recognizes Chinese or English translation words, while configuration claims to support any non-`en` language code.
- Translation mirroring checks ordered lists and some tables, but not unordered lists, headings, callouts, code blocks, field order, or missing translated tables.
- The diary's pre-append instruction relies on calling an internal Python function or human inspection rather than a stable CLI hard gate.

### Why change

Rules described as hard gates should be machine-enforced wherever deterministic validation is possible. Otherwise the written specification and actual acceptance boundary diverge.

### Concrete change

1. Parse and compare ordered section sequences rather than testing membership only.
2. Validate dates with a calendar-aware parser.
3. Validate H1 count, duplicate headings, known frontmatter keys, source-locator rules, and ordered References.
4. Reuse a shared schema layer for card and note frontmatter instead of duplicating partial checks.
5. Make the configured translation heading explicit or derive it from a supported-language map.
6. Compare bilingual headings, ordered and unordered lists, tables, callouts, fenced code blocks, and field order.
7. Add `validate_diary.py` or a general `validate_generated_markdown.py` command that can validate a staged diary section before append.
8. Start stronger checks in report-only mode against the existing vault, then promote stable checks to errors.

### Expected outcome

- The executable acceptance boundary matches the written specification more closely.
- Append-only diary defects are blocked before they become immutable.
- Cross-language behavior is explicit rather than inferred.

### Before and after

| Contract area | Before | After |
|---|---|---|
| Card sections | Presence only | Presence, uniqueness, and order |
| Dates | Shape only | Real calendar date |
| Translation | Primarily zh-CN and English assumptions | Explicit configured-language contract |
| Diary | Internal function or visual inspection | Dedicated CLI hard gate |
| Existing vault adoption | New checks could fail immediately | Report-only audit before enforcement |

### Costs and risks

- Stronger validation may surface pre-existing defects in valid-looking notes.
- A shared schema parser adds code, but it removes duplicated validation logic.
- Translation equivalence can only be partially automated; idiomatic quality remains a human or model judgment.

## Finding KW-05: INDEX ordering in the specification and implementation differs

Priority: P1

### Current state

- [`references/integration-rules.md`](../references/integration-rules.md) requires entries to be alphabetical within their level-1 group.
- [`scripts/update_index.py`](../scripts/update_index.py) appends a new entry to the end of the selected section's bullet block.
- The script searches for a level-2 heading by visible heading text.

### Problem and evidence

Appending does not guarantee alphabetical order. A level-2 slug reused under different level-1 domains could also cause an unbounded heading lookup to select the wrong subsection.

### Why change

The helper script should be the deterministic implementation of the index contract. A mismatch forces the model or user to repair ordering manually.

### Concrete change

1. Parse INDEX into bounded level-1 and level-2 sections.
2. Locate a level-2 section only inside its intended level-1 section.
3. Normalize, deduplicate, and alphabetically sort note entries in the target section.
4. Preserve unrelated prose, spacing, headings, and user-edited sections byte-for-byte when possible.
5. Add fixtures covering level-1 notes, level-2 notes, repeated subdomain names, updates, duplicates, and unchanged dry runs.

### Expected outcome

- INDEX ordering consistently matches the specification.
- Identically named subdomains cannot receive entries intended for another domain.

### Before and after

| Behavior | Before | After |
|---|---|---|
| New line placement | Appended to the section | Inserted into sorted position |
| Repeated subdomain slug | May match globally | Resolved within the intended parent domain |
| User formatting | Preserved incidentally | Explicitly protected by bounded edits |

### Costs and risks

- Sorting can create larger diffs in an existing manually ordered INDEX.
- The first implementation should run on a copy or in `--dry-run` mode and show the exact proposed section change.

## Finding KW-06: Cross-agent provenance is Claude-specific

Priority: P1

### Current state

- Conversation diaries live under `conversation-claude/`.
- Conversation cards use paths under that directory as `source_ref`.
- The schema records a source type but not the agent that produced the diary or card.

### Problem and evidence

If Codex executes the same skill unchanged, Codex-generated records will be stored in a Claude-named directory. The data remains usable, but provenance becomes semantically misleading.

### Why change

One shared knowledge vault should preserve the source agent without duplicating the knowledge hierarchy or forcing readers to infer provenance from context.

### Concrete change

Choose one design before implementation:

1. Minimal compatibility: keep historical `conversation-claude/`, add `conversation-codex/`, and let `source_ref` identify the agent through the path.
2. Neutral model: introduce `conversations/<agent>/` plus an explicit `source_agent` field for new cards.
3. Unified diary: use one neutral conversation directory and add agent metadata to each appended section and card.

Do not rename historical diary files merely for consistency; preserve existing provenance paths.

### Expected outcome

- Claude and Codex can write to the same vault without ambiguous source labels.
- Historical links remain valid.

### Before and after

| Aspect | Before | After |
|---|---|---|
| Claude provenance | Correctly implied by path | Preserved |
| Codex provenance | Would be mislabeled as Claude | Explicitly represented |
| Historical paths | Existing | Retained without silent rewrites |

### Costs and risks

- Adding `source_agent` may require schema version 2.
- Separate diary directories improve clarity but split chronological browsing by agent.
- A unified directory simplifies browsing but requires stronger metadata and collision handling.

## Finding KW-07: File, folder, and PDF source adapters are underspecified

Priority: P1

### Current state

- The invocation accepts a file or folder and mentions notes and PDFs.
- The skill does not define supported extensions, directory recursion, stable ordering, symlink behavior, binary-file handling, extraction tooling, size limits, or partial-failure reporting.

### Problem and evidence

Claude and Codex may choose different extraction tools and traversal rules. The same directory can therefore yield different candidate sets, provenance locators, or failure behavior.

### Why change

Source normalization is the first stage of the pipeline. If it is nondeterministic, downstream cards and deduplication cannot be fully reproducible.

### Concrete change

1. Add a directly referenced source-adapter specification.
2. Define supported text and Markdown extensions and how unsupported files are reported.
3. Define whether folders recurse, how files are ordered, whether hidden files and symlinks are included, and what maximum input size applies.
4. Define the preferred PDF text-extraction path, page-locator format, OCR boundary, and behavior for scanned or encrypted PDFs.
5. Record every source file and extraction result in a preflight report before candidate generation.
6. Treat unreadable files as explicit warnings rather than silently skipping them.

### Expected outcome

- The same input produces a stable ordered source set across supported clients.
- PDF `source_ref` values have consistent page provenance.
- Partial input failures are visible to the user.

### Before and after

| Input behavior | Before | After |
|---|---|---|
| Folder traversal | Executor decides | Specification defines recursion and order |
| Unsupported file | May be skipped or guessed | Reported explicitly |
| PDF extraction | Tool-dependent | Preferred path and fallback are defined |
| Provenance | Ad hoc locator | Stable source and page locator |

### Costs and risks

- A comprehensive source contract adds reference material and test cases.
- OCR may require an optional dependency and should not become an implicit requirement.

## Finding KW-08: Evaluation files are examples rather than executable regressions

Priority: P1

### Current state

- `evals/conversation-a.md` and `evals/conversation-b.md` provide realistic input conversations.
- No expected candidate table, expected cards, expected note mutations, assertion manifest, isolated vault fixture, or automated runner is present.
- The maintenance instructions require rerunning conversations and comparing outputs manually.

### Problem and evidence

Manual comparison cannot reliably detect subtle drift in exclusion gates, relation classification, idempotency, translation mirroring, or interrupted-run recovery.

### Why change

The skill has a detailed behavioral contract and deterministic scripts, so it is well suited to executable acceptance tests. Real regression tests would protect the exact properties the skill was designed to preserve.

### Concrete change

1. Create a disposable vault fixture with taxonomy, index, cards, notes, and user-edited examples.
2. Add expected assertions rather than requiring byte-for-byte equality for all generated prose.
3. For conversation A, assert that reusable Git commit guidance and idempotency survive while the repository rename is excluded.
4. For conversation B, assert that idempotency supplements the existing topic and pushed-history guidance creates the appropriate new card or note.
5. Add cases for zero candidates, same-input rerun, independent corroboration, conflict, restructured user note, malformed taxonomy, multilingual output, more than eight cards, file and folder input, PDF input, and interrupted recovery.
6. Run all tests against a temporary vault and prohibit access to the real vault.

### Expected outcome

- Rule changes produce an objective pass or fail signal.
- Evaluation content cannot pollute the real knowledge base.
- Forward tests can focus on model behavior while deterministic scripts cover structural invariants.

### Before and after

| Evaluation aspect | Before | After |
|---|---|---|
| Inputs | Two conversation files | Inputs plus fixtures and assertions |
| Expected behavior | Interpreted manually | Machine-readable invariants |
| Vault safety | Depends on operator discipline | Temporary vault enforced |
| Regression signal | Subjective comparison | Repeatable pass or fail result |

### Costs and risks

- Semantic assertions require maintenance when intentional behavior changes.
- Full prose golden files may be brittle; prefer structural and content-presence assertions.

## Finding KW-09: Written examples and formatting rules contain small inconsistencies

Priority: P2

### Current state

- The card and note specifications require ordered References lists.
- The worked card and note examples use unordered list markers for References.
- Generated prose is required to use soft wrapping, but several templates and specifications demonstrate hard-wrapped prose.
- Runtime skill files and maintainer documents are stored together in the source directory.

### Problem and evidence

Models learn from examples as well as rules. A contradictory example can override prose guidance during execution. Source documents that violate their own universal formatting language also make the intended scope ambiguous.

### Why change

Examples should be canonical demonstrations of the contract. Runtime content should remain focused, while maintainer history should not become part of the skill's operational reading path.

### Concrete change

1. Convert References in worked examples to ordered lists.
2. Reflow template prose to the required soft-wrap form, especially text likely to be copied into generated output.
3. Clarify whether the soft-wrap rule applies only to generated vault artifacts or also to skill source documents.
4. Keep maintainer documents in the source repository if useful, but ensure `SKILL.md` does not route runtime execution through README, TODO, or changelog material.
5. If the skill is distributed as a plugin, package only the runtime files needed for execution.

### Expected outcome

- Examples and validators reinforce the same behavior.
- Runtime context stays focused on the workflow.
- Maintainer history remains available without becoming operational instruction.

### Before and after

| Area | Before | After |
|---|---|---|
| References examples | Unordered despite an ordered-list rule | Ordered and validator-compatible |
| Wrapping examples | Mixed conventions | Templates demonstrate the declared rule |
| Maintainer documents | Co-located with runtime files | Retained but excluded from runtime routing or packaging |

### Costs and risks

- Reformatting source documents creates a large textual diff with little behavioral change.
- Packaging exclusions add a small release-maintenance step.

## Finding KW-10: Obsidian CLI readiness and vault-name resolution need a preflight contract

Priority: P2

### Current state

- The executable `/usr/local/bin/obsidian` exists.
- During the review, `obsidian --help` reported that it could not find a running Obsidian instance.
- The config records `vault_path` but not an explicit Obsidian vault name.
- Step 3 uses an Obsidian CLI command with a `<vault-name>` placeholder and falls back to filesystem search.

### Problem and evidence

Executable presence does not prove CLI readiness. Vault-name derivation is also implicit, so an executor may guess differently when the directory name and registered Obsidian vault name diverge.

### Why change

Dedupe search should use a predictable preflight result rather than fail midway or rely on an inferred name.

### Concrete change

1. Add a read-only preflight that verifies config parsing, vault skeleton, Python availability, and actual Obsidian CLI responsiveness.
2. Add an optional `vault_name` configuration field or define a verified derivation rule.
3. If the CLI is unavailable, select the filesystem fallback once and report that choice.
4. Prefer `rg -il` when available, then fall back to `grep -ril`.
5. Record the dedupe search backend in the final report for reproducibility.

### Expected outcome

- The run knows its search backend before writing begins.
- A stopped Obsidian application results in a controlled fallback rather than an ambiguous failure.

### Before and after

| Area | Before | After |
|---|---|---|
| CLI check | Executable presence may be assumed | Responsiveness is verified |
| Vault name | Placeholder requires inference | Configured or deterministically derived |
| Search backend | Chosen after failure | Selected during preflight and reported |

### Costs and risks

- An additional config key needs backward-compatible default behavior.
- CLI behavior may differ by Obsidian version, so the filesystem backend must remain supported.

## Recommended implementation phases

### Phase 1: Compatibility-only release

Scope:

- Add Codex discovery through a symlink.
- Add `agents/openai.yaml` with implicit invocation disabled.
- Add `$knowledge-wrapup` documentation.
- Resolve the stale and non-portable version field.
- Add preflight reporting without changing card or note schemas.

Acceptance criteria:

- Claude still discovers and explicitly invokes the shared skill.
- Codex lists the skill after installation or restart.
- Codex does not invoke the skill implicitly.
- A Codex dry inspection requests no vault mutation.
- Existing validators and the real vault remain unchanged.

### Phase 2: Contract alignment release

Scope:

- Fix validator and specification mismatches.
- Add a diary validator.
- Fix INDEX sorting and bounded section resolution.
- Correct examples and formatting inconsistencies.
- Introduce executable temporary-vault tests.

Acceptance criteria:

- Every deterministic hard rule has a corresponding validator or an explicit reason it remains judgment-based.
- Existing vault content is audited in report-only mode before stricter failures are enabled.
- INDEX helper tests cover duplicate, update, sort, and same-subdomain-name cases.

### Phase 3: Schema and idempotency design

Scope:

- Decide the cross-agent diary and provenance model.
- Define source fingerprints, duplicate handling, and resumable runs.
- Decide whether the result requires card schema version 2.
- Define deterministic file, folder, and PDF adapters.

Acceptance criteria:

- Repeating the same source produces zero vault changes.
- Independent corroboration is distinguishable from duplicate processing.
- Interrupted runs resume without duplicating diary, card, note, source, index, or taxonomy mutations.
- Historical provenance paths remain valid.

## Decisions required before implementation

1. Should Codex diaries use `conversation-codex/`, a neutral `conversations/<agent>/` hierarchy, or one unified directory with explicit agent metadata?
2. Should true idempotency and `source_agent` be introduced through card schema version 2 now, or should the first release remain compatibility-only?
3. Should the source repository continue to contain maintainer documents while a later plugin packages only runtime files?
4. Should Codex always require `$knowledge-wrapup`, or should an explicit natural-language request to write into the knowledge base also remain sufficient?
5. Should the first executable evaluations assert structural invariants only, or also retain selected golden prose outputs?

## Official Codex references

1. [Build skills](https://learn.chatgpt.com/docs/build-skills) — skill structure, discovery paths, explicit and implicit invocation, symlink support, optional `agents/openai.yaml`, and invocation policy.
2. [Customization overview](https://learn.chatgpt.com/docs/customization/overview) — separation among project guidance, memories, skills, MCP, and subagents.

## Review boundary

This review did not:

- modify `SKILL.md`, references, scripts, templates, evaluations, configuration, or vault contents;
- execute `/knowledge-wrapup` or `$knowledge-wrapup`;
- run Git commands;
- install the skill for Codex;
- install Python dependencies or start Obsidian;
- perform a forward test that could write to the live vault.
