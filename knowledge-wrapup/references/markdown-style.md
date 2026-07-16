# Markdown Writing Standard (spec_version: 1)

Why this exists: a 2026-07-16 review found four recurring defects in generated
documents — circled-number characters (①②③) standing in for lists, steps
crammed into single paragraphs, literal word-stacked translations, and session
war stories woven through teaching material. Three of the four had no rule to
violate. This spec closes the gaps, and its machine-checkable subset moves
into the validator: rules that can be enforced by code are not left to
discipline.

## Scope & precedence

- Applies to ALL markdown this skill generates: cards, notes, diary sections,
  INDEX/TAXONOMY appends.
- Also applies, as a general standard, to any other markdown the assistant
  writes (engineering repo docs, chat-generated files) — except where a
  repository's own conventions differ (see T4).
- Type-specific templates (card-spec, note template, diary template) override
  this document only where they explicitly say so.

## Universal rules (U1–U7)

**U1 — Enumerations and steps use markdown lists.** Any run of ≥2 parallel
items or sequential steps is a markdown list: ordered (`1.`) when order
matters, unordered (`-`) when it doesn't. Substitute characters are FORBIDDEN
as list markers: ①②③…⑳, ⑴⑵⑶, •, ●, ▪, ➀, Ⅰ/Ⅱ/Ⅲ, full-width digits.
They render inconsistently, defeat search, and are hostile to screen readers.

**U2 — Soft-wrap constrains paragraphs, never structure.** "One paragraph =
one physical line, never hard-wrap" applies INSIDE a paragraph. It is not a
license to fold a list into a paragraph: one list item = one line, blank-line
separation between blocks stays. (This mis-generalization was the root cause
of the 2026-07-16 defects.)

**U3 — Representation by content kind.** Comparisons and enumerable facts →
tables. Processes, decision trees, architectures → Mermaid (≤10 nodes, label
the edges). Definitions, reasoning, nuance → prose. Don't force a diagram
where two sentences are clearer.

**U4 — Mermaid labels are plain text, always quoted.** No braces, no inline
LaTeX/`$`, no pipes inside node labels or subgraph titles; `<br/>` is the only
allowed markup. Formulas belong in prose next to the diagram (Mermaid never
hands labels to the page's math renderer). Quote every label — parentheses
and braces are shape syntax when unquoted.

**U5 — Math notation by medium.** Documents use LaTeX (`$...$` inline,
`$$...$$` display — GitHub and Obsidian render natively). Unicode math
(Σ, β̂, σ²) is only for terminal chat, where LaTeX doesn't render.

**U6 — Examples must be self-standing.** A teaching example's numbers are
chosen for clarity (a $1000 portfolio, a 4-day return series), and the example
re-teaches without any session context. Session/project outcomes may appear
at most ONCE per note, one line, framed as evidence ("validated in practice:
two independent implementations agreed to float noise"), never as narrative
("we then found...", "in the original incident..."). Rationale: cards/notes
are for the reader six months out; war stories belong to the diary.

**U7 — Translations mirror structure, not words.** The translation section
reproduces the source structure one-to-one — list for list, table for table,
code block for code block (code itself is not translated; translate
surrounding prose). Wording is idiomatic, never literal; headings and titles
are REWRITTEN in the target language's own idiom (noun-stack transliterations
like "数值引擎的已知答案锚点测试" fail this rule; "数值引擎的锚点测试法" passes).
CJK prose: one paragraph = one physical line (renderers turn newlines into
spaces and corrupt CJK).

## Type-specific rules (T1–T4, deltas over universal)

**T1 — Cards** (`cards/`): English only, no translation section; fixed section
order per card-spec; `## References` links are ordered lists with one-line
annotations.

**T2 — Notes** (`notes/`): bilingual; exactly one `> [!summary]` callout at
top (mirrored in translation); pitfalls in `> [!warning]` callouts; soft-wrap
everywhere.

**T3 — Diary** (`conversation-claude/`): topic blocks per diary template;
Details are bullets (U1 applies); append-only — never reformat earlier
content, even your own from a previous run. Session-specific detail is
CORRECT here (the diary is the record; U6 does not apply).

**T4 — Engineering repo docs** (outside the vault): the repository's own
conventions win where they conflict — e.g. hard-wrap at ~72 columns if that
is the repo's house style. All other universal rules (U1, U3–U6) still apply.

## Machine-checkable subset (validator enforcement)

`validate_card.py` (and any future note linter) enforces:

1. Character blacklist: `[①-⑳⑴-⒇•●▪◦➀-➉Ⅰ-Ⅻ]` anywhere in generated body
   text → FAIL with pointer to U1.
2. Mermaid lint: inside ```mermaid fences, flag unquoted labels containing
   `(`, `{`, `$`, or `|` → FAIL with pointer to U4.
3. Crammed-enumeration heuristic: a single line containing ≥3 occurrences of
   `\d+[.、)]` outside code fences → WARN with pointer to U1/U2.

Everything else (U6 genericity, U7 idiomaticity) stays human/model judgment —
reviewed, not linted.

## Change discipline

This spec is binding during skill runs, same as SKILL.md's ground rule: if a
rule feels wrong mid-run, follow it, flag the friction in the report, and
propose a change; the change lands only after the user approves.
