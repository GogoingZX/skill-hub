#!/usr/bin/env python3
"""Insert (or update) one note's line in INDEX.md — idempotently.

Usage:
    python3 update_index.py --vault VAULT --note notes/<l1>/<l2>/<topic>.md \
        --title "Human Title" --summary "one-line hook for the index"
    [--dry-run]

Behavior:
- The target section is derived from the note path: notes/finance/quant/x.md
  → under "## finance" / "### quant".
- If a line pointing at the same note path already exists anywhere in
  INDEX.md, it is REPLACED in place (title/summary refresh) — never
  duplicated. Otherwise the new line is appended at the end of the
  section's bullet block.
- Missing "### <level2>" section: created right after the "## <level1>"
  heading block. Missing "## <level1>": hard error — level-1 domains are
  TAXONOMY decisions, not something this script invents.

Exit codes: 0 = inserted/updated/skipped-identical; 2 = usage or structure
error (message on stderr).
"""

import argparse
import re
import sys
from pathlib import Path


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


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
    if len(parts) < 3 or parts[0] != "notes":
        fail("--note must look like notes/<level1>/[<level2>/]<topic>.md")
    level1 = parts[1]
    level2 = parts[2] if len(parts) == 4 else None

    text = index.read_text()
    new_line = f"- [{args.title}]({args.note}) — {args.summary}"

    # already present? replace in place (idempotent refresh)
    pattern = re.compile(rf"^- \[[^\]]*\]\({re.escape(args.note)}\).*$",
                         re.MULTILINE)
    if pattern.search(text):
        old = pattern.search(text).group(0)
        if old == new_line:
            print(f"unchanged: {args.note} already indexed identically")
            return
        updated = pattern.sub(new_line, text, count=1)
        action = f"updated existing line for {args.note}"
    else:
        h1 = f"## {level1}"
        if f"\n{h1}\n" not in f"\n{text}":
            fail(f"section '{h1}' not in INDEX.md — level-1 domains come "
                 "from TAXONOMY; add the section there first")
        if level2:
            h2 = f"### {level2}"
            if f"\n{h2}\n" not in f"\n{text}":
                # create the subsection right after the level-1 heading
                text = text.replace(f"{h1}\n", f"{h1}\n\n{h2}\n", 1)
                print(f"created new subsection '{h2}' under '{h1}'")
            anchor = h2
        else:
            anchor = h1
        # append after the section's last bullet (before the next heading)
        pos = text.index(anchor)
        nxt = re.search(r"^#{2,3} ", text[pos + len(anchor):], re.MULTILINE)
        end = pos + len(anchor) + (nxt.start() if nxt else
                                   len(text) - pos - len(anchor))
        block = text[pos:end].rstrip() + f"\n{new_line}\n\n"
        updated = text[:pos] + block + text[end:]
        action = f"inserted under '{anchor}'"

    if args.dry_run:
        print(f"DRY-RUN would have: {action}\n  {new_line}")
        return
    index.write_text(updated)
    print(action)


if __name__ == "__main__":
    main()
