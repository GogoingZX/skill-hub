# TODO — deferred improvements (revisit after a few runs)

1. **Same-day sibling-session awareness** (recorded 2026-07-16): Step 3
   could start by listing today's already-merged cards, so a second session
   on the same day sees what a sibling run already extracted instead of
   discovering collisions card-by-card (2026-07-16: two sessions collided
   on mermaid-special-characters).

Done (2026-07-16): helper-script consolidation — `scripts/update_index.py`
and `scripts/check_provenance.py` exist, functionally tested against the
live vault (245 refs checked; idempotent insert/update/skip verified).

Observing (2026-07-16, per user decision): whether spec-driven validation
gets skipped in practice. Automatic enforcement (e.g. a PostToolUse hook)
will be configured only if observation shows real misses — not preemptively.
