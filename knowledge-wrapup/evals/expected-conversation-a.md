# Expected outcome — conversation A

Run in file mode against a fresh copy of `vault-fixture/`.

## Decision table

- [ ] The `utils.py` → `helpers.py` rename appears as a candidate and is
      rejected: ❌ project-specific in Reusable, no card, Relation "—".
- [ ] Git commit message guidance survives all three gates.
- [ ] Idempotency survives all three gates.
- [ ] No manufactured extra candidates (0–5 cards is the normal envelope).

## Cards

- [ ] `cards/git-commit-messages--{run-date}.md` exists, `type: howto`,
      `domain: technology/tools`, tags from the fixture registry only.
- [ ] `cards/idempotency--{run-date}.md` exists, `type: concept` (or `term`),
      `domain: technology/api-design`.
- [ ] Both cards pass `validate_card.py --vault <scratch>`.
- [ ] git-commit-messages covers: imperative subject ≤50 chars, body explains
      why, Conventional Commits `type(scope): subject`, and its References is
      an ordered list containing https://www.conventionalcommits.org/.
- [ ] idempotency covers: safe-to-retry meaning, the PUT-vs-POST example, and
      the idempotency-key motivation for payment APIs. No invented URLs.

## Notes and index

- [ ] `notes/technology/tools/git-commit-messages.md` and
      `notes/technology/api-design/idempotency.md` exist and pass
      `validate_note.py --language zh-CN --vault <scratch>`.
- [ ] Each note ends with a `## 中文翻译` section mirroring the English
      structure (U7).
- [ ] INDEX.md lists both notes under `## technology`, inside `### tools` /
      `### api-design`, inserted via `update_index.py`.
- [ ] TAXONOMY.md is unchanged (both domains already exist; no new tags
      without an announcement in the report).

## Safety

- [ ] No diary file was written (file mode writes no diary).
- [ ] Zero writes outside the scratch vault; the real vault and real config
      are untouched.
- [ ] `check_provenance.py --vault <scratch>` reports no broken refs.
