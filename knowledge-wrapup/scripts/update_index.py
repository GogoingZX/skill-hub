#!/usr/bin/env python3
"""Insert (or update) one note's line in INDEX.md — idempotently, in sorted order.

Usage:
    python3 update_index.py --vault VAULT --note notes/<l1>/<l2>/<topic>.md \
        --title "Human Title" --summary "one-line hook for the index"
    [--dry-run]

Behavior:
- The target section is derived from the note path: notes/finance/quant/x.md
  → under "## finance" / "### quant". The "### <level2>" lookup is BOUNDED
  to its "## <level1>" section, so identically named subdomains under
  different domains can never receive each other's entries.
- If a line pointing at the same note path already exists anywhere in
  INDEX.md, it is removed first (title/summary refresh, or move to the
  correct section) — never duplicated.
- Entries within the target (sub)section's bullet block are kept
  ALPHABETICAL by title (case-insensitive), per integration-rules.md.
  Only the target bullet block is rewritten; all other sections, prose,
  and spacing are preserved.
- Missing "### <level2>" section: created at the END of its "## <level1>"
  section. Missing "## <level1>": hard error — level-1 domains are
  TAXONOMY decisions, not something this script invents.

Exit codes: 0 = inserted/updated/skipped-identical; 2 = usage or structure
error (message on stderr).
"""

import argparse
import re
import sys
from pathlib import Path

BULLET_RE = re.compile(r"^- \[(?P<title>[^\]]*)\]\((?P<path>[^)]+)\).*$")


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def section_bounds(lines, heading, start=0, end=None, level=2):
    """Return (heading_idx, end_idx) of the section opened by `heading`
    (exact line match) inside lines[start:end], or None. The section runs
    until the next heading of the same or higher level."""
    end = len(lines) if end is None else end
    stop = re.compile(r"^#{1,%d} " % level)
    for i in range(start, end):
        if lines[i].rstrip() == heading:
            j = i + 1
            while j < end and not stop.match(lines[j]):
                j += 1
            return i, j
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--note", required=True,
                    help="vault-relative note path, e.g. notes/finance/quant/x.md")
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", required=True,
                    help="short hook text after the em-dash")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser()
    index = vault / "INDEX.md"
    if not index.is_file():
        fail(f"INDEX.md not found under {vault}")
    if not (vault / args.note).is_file():
        fail(f"note file does not exist: {args.note}")

    parts = Path(args.note).parts
    if len(parts) not in (3, 4) or parts[0] != "notes":
        fail("--note must look like notes/<level1>/[<level2>/]<topic>.md")
    level1 = parts[1]
    level2 = parts[2] if len(parts) == 4 else None

    original = index.read_text()
    lines = original.splitlines()
    new_line = f"- [{args.title}]({args.note}) — {args.summary}"

    # remove any existing line for this note path (refresh / move, never duplicate)
    kept, removed = [], False
    for line in lines:
        m = BULLET_RE.match(line)
        if m and m.group("path") == args.note:
            removed = True
            continue
        kept.append(line)
    lines = kept

    h1 = f"## {level1}"
    found = section_bounds(lines, h1, level=2)
    if found is None:
        fail(f"section '{h1}' not in INDEX.md — level-1 domains come "
             "from TAXONOMY; add the section there first")
    h1_idx, h1_end = found

    created = None
    if level2:
        h2 = f"### {level2}"
        # bounded lookup: only inside this level-1 section
        sub = section_bounds(lines, h2, start=h1_idx + 1, end=h1_end, level=3)
        if sub is None:
            # create the subsection at the END of the level-1 section
            insert_at = h1_end
            while insert_at > h1_idx + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            lines[insert_at:insert_at] = ["", h2, ""]
            created = f"created new subsection '{h2}' under '{h1}'"
            sub = section_bounds(lines, h2, start=h1_idx + 1, level=3)
        sec_idx, sec_end = sub
    else:
        sec_idx, sec_end = h1_idx, h1_end
        # a level-1-only entry belongs before the first subsection, if any
        for i in range(sec_idx + 1, sec_end):
            if lines[i].startswith("### "):
                sec_end = i
                break

    # rewrite the target block: non-bullet lines stay, bullets come back sorted
    body = lines[sec_idx + 1:sec_end]
    bullets = [ln for ln in body if BULLET_RE.match(ln)]
    others = [ln for ln in body if not BULLET_RE.match(ln) and ln.strip()]
    bullets.append(new_line)
    bullets.sort(key=lambda ln: BULLET_RE.match(ln).group("title").casefold())
    new_body = ([""] + others if others else [""]) + bullets + [""]
    lines[sec_idx + 1:sec_end] = new_body

    updated = "\n".join(lines) + ("\n" if original.endswith("\n") else "")
    if updated == original:
        print(f"unchanged: {args.note} already indexed identically")
        return
    action = (f"updated existing line for {args.note}" if removed
              else f"inserted under '{h2 if level2 else h1}' (sorted)")
    if created:
        print(created)
    if args.dry_run:
        print(f"DRY-RUN would have: {action}\n  {new_line}")
        return
    index.write_text(updated)
    print(action)


if __name__ == "__main__":
    main()
