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
- [ ] Topic naming: the gotcha card's topic names the concept (e.g.
      `amending-pushed-commits`), never the flag or command — a
      `force-with-lease`-led topic fails the naming rule.
- [ ] Destructive-operation form: the gotcha note treats force-push as
      destructive — five-part form present (command breakdown incl.
      `--force-with-lease` vs `--force`, when it applies + safer alternative,
      consequences, recovery written as if already executed, preflight
      cautions). Recovery/preflight material beyond the transcript is
      enrichment: card stays `confidence: discussed` and carries a canonical
      reference (e.g. git-scm.com). `validate_note.py` raises no
      destructive-command warning.
- [ ] Claim scope: the Stripe 24-hour key-retention detail, if kept, is
      attributed as a provider example — never stated as a universal property
      of idempotency keys.

## Same-day card rule (when B runs on the same date as A)

- [ ] B's idempotency content gets its OWN new card file,
      `idempotency--{run-date}-2.md` — the existing `idempotency--{run-date}.md`
      from A is never re-opened or edited (card-spec: every extraction is a
      new card). Each card's `source_ref` names exactly one source: A's card
      points only at conversation-a, B's card points only at conversation-b.
- [ ] Both idempotency cards reach `status: merged` independently; the note
      accumulates both via two separate supplements-relation merges, not one.

## Index and validation

- [ ] INDEX.md gains the new gotcha note's line under `## technology` /
      `### tools` in alphabetical position; the idempotency line's hook is
      refreshed if the note was significantly enriched.
- [ ] All cards and notes still pass their validators (with
      `--privacy-denylist "alan"`) and emit zero warnings;
      `check_provenance.py` reports no broken refs.

## Rerun idempotency (step 5 of the protocol)

- [ ] Running conversation B a second time changes NOTHING in the scratch
      vault (`diff -r` between snapshots is empty): every candidate hits an
      already-listed `source_ref` and is reported as duplicate — not
      corroboration, no new source lines, no INDEX churn.
