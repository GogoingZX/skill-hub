# Simulated conversation B (regression test input — same day as A, later)

**User:** Quick follow-up on idempotency — is DELETE idempotent? And how do idempotency keys actually work?

**Assistant:** Yes, DELETE is idempotent: deleting resource 42 twice leaves the system in the same state (the second call typically returns 404, but the *state* is unchanged — idempotency is about state, not response codes).

Idempotency keys: the client generates a unique key (usually a UUID) per logical operation and sends it in a header like `Idempotency-Key`. The server stores the key with the first response; any retry with the same key returns the stored response instead of re-executing. Stripe's API popularized this pattern — keys are typically retained for 24 hours.

**User:** Also, I messed up earlier — I amended a commit I had already pushed and now my push is rejected. What happened?

**Assistant:** `git commit --amend` doesn't edit the old commit — it *replaces* it with a new commit (new hash). Your local branch history has diverged from the remote, so the push is rejected as non-fast-forward.

Fix: if nobody else pulled the branch, `git push --force-with-lease` (safer than `--force` — it aborts if the remote moved). If teammates already pulled, don't force-push; make a follow-up commit instead.

How to avoid: treat pushed history as immutable. Amend and rebase only commits that haven't left your machine.
