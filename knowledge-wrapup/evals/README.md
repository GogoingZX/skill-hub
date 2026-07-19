# Evals — executable regression protocol

Two simulated conversations plus a disposable vault fixture turn the skill's
behavioral contract into a repeatable pass/fail check. Structural invariants are
verified by the deterministic scripts; extraction/integration judgment is
verified against the assertion checklists.

**Hard rule: eval runs never touch the real vault or the real config.** All
writes go to a scratch copy; any write outside it fails the eval.

## Protocol

1. Copy `vault-fixture/` to a scratch directory, e.g.
   `cp -R evals/vault-fixture /tmp/kw-eval-vault`.
2. Run the skill in file mode on `evals/conversation-a.md`, with `vault_path`
   pointed at the scratch copy and `language` = `zh-CN` for the run. Do not
   read or modify `~/.config/knowledge-wrapup/config.json` or the real vault.
   Pin file-mode provenance: `source: note`, `source_ref` = the transcript path
   as given.
3. Check every assertion in `expected-conversation-a.md`.
4. On the SAME scratch vault, run the skill on `evals/conversation-b.md`, then
   check `expected-conversation-b.md`.
5. Idempotency regression: snapshot the scratch vault (`cp -R`), run
   conversation B once more, then `diff -r` the snapshots — the rerun must
   produce zero changes (all candidates are duplicates of an already-listed
   `source_ref`).
6. Deterministic close-out on the scratch vault: every card passes
   `validate_card.py --vault`, every note passes `validate_note.py --language
   zh-CN --vault`, and `check_provenance.py --vault` reports no broken refs.

## Maintenance

The assertion files describe intended behavior, not golden prose — assert
structure and content presence, never exact wording. When a rule changes
intentionally, update the affected assertions in the same change.
