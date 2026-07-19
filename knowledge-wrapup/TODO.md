# TODO — deferred improvements (revisit after a few runs)

1. **Card `source_ref` is single-valued** (found by the 2026-07-19 eval run):
   when the same-day rule extends an existing card with content from a SECOND
   source, the card keeps only its creation source — the second source's
   provenance lives solely in the note's Sources section. Acceptable (notes
   are the product), but if card-level provenance ever matters, this needs a
   multi-source field and a spec_version bump. Decide only when it bites.

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
