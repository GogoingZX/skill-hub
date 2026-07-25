# TODO — deferred improvements (revisit after a few runs)

Done (2026-07-25): resolved the source_ref-single-valued item (below,
superseded) by removing card-level same-day extension entirely instead of
adding a multi-source field. Every extraction is now a new card file, never a
re-opened one; a same-day same-topic collision gets a disambiguating filename
suffix (`{topic}--{yyyyMMdd}-2.md`). Each card's single `source_ref` is now
always accurate — the ambiguity the deferred item worried about can no longer
occur, and no spec_version bump or schema change was needed. Superseded item,
kept for context: "Card `source_ref` is single-valued (found by the
2026-07-19 eval run): when the same-day rule extends an existing card with
content from a SECOND source, the card keeps only its creation source — the
second source's provenance lives solely in the note's Sources section."

Done (2026-07-19): eval protocol executed end-to-end for the first time
(A → B → B-replay on a scratch vault): all assertions in both expected-*
checklists passed, replay was a byte-identical no-op, real vault untouched.

Done (2026-07-19): same-day sibling-session awareness — Step 3 now starts by
listing today's already-written cards, so a second session sees what a sibling
run extracted instead of discovering collisions card-by-card (recorded
2026-07-16 after two sessions collided on mermaid-special-characters).

Done (2026-07-16): helper-script consolidation — `scripts/update_index.py`
and `scripts/check_provenance.py` exist, functionally tested against the
live vault (245 refs checked; idempotent insert/update/skip verified).

Observing (2026-07-16, per user decision): whether spec-driven validation
gets skipped in practice. Automatic enforcement (e.g. a PostToolUse hook)
will be configured only if observation shows real misses — not preemptively.
