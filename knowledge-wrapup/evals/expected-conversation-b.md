# Expected outcome — conversation B

Run in file mode against the SAME scratch vault, after conversation A.

## Integration relations

- [ ] The DELETE-idempotency + idempotency-key material classifies as
      **supplements** for the existing idempotency note — no second
      idempotency note is created.
- [ ] The idempotency note gains the new content (state-not-response-codes
      nuance, Idempotency-Key mechanism) with an inline source marker, its
      Sources section gains the conversation-b ref, and the translation
      section is redone to mirror the updated English body.
- [ ] The amended-pushed-commit material is **new**: a gotcha card (symptom =
      rejected non-fast-forward push; fix = `--force-with-lease` when safe,
      follow-up commit otherwise; avoid = treat pushed history as immutable)
      and a corresponding note under `technology/tools`.

## Same-day card rule (when B runs on the same date as A)

- [ ] B's idempotency content extends the EXISTING
      `idempotency--{run-date}.md` card (flip to `status: raw`, re-validate,
      re-integrate) — no second filename for the same topic and date.

## Index and validation

- [ ] INDEX.md gains the new gotcha note's line under `## technology` /
      `### tools` in alphabetical position; the idempotency line's hook is
      refreshed if the note was significantly enriched.
- [ ] All cards and notes still pass their validators; `check_provenance.py`
      reports no broken refs.

## Rerun idempotency (step 5 of the protocol)

- [ ] Running conversation B a second time changes NOTHING in the scratch
      vault (`diff -r` between snapshots is empty): every candidate hits an
      already-listed `source_ref` and is reported as duplicate — not
      corroboration, no new source lines, no INDEX churn.
