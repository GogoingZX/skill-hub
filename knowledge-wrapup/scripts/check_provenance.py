#!/usr/bin/env python3
"""Verify that every provenance reference in the vault points at a file
that still exists (SKILL.md Step 6.5 — report-only by default).

Scans:
- cards/*.md frontmatter `source_ref:` values;
- notes/**/*.md `## Sources` bullet lines.

PDF page fragments ("guide.pdf#p12") are stripped before the existence
check. Broken references are LISTED, never repaired or deleted —
knowledge is unaffected; only traceability is lost.

Usage:
    python3 check_provenance.py --vault VAULT [--strict]

Exit code: 0 normally; with --strict, 1 if any reference is broken
(useful as a pre-commit hook).
"""

import argparse
import re
import sys
from pathlib import Path

SOURCE_REF_RE = re.compile(r'^source_ref:\s*"?([^"\n]+?)"?\s*$', re.MULTILINE)
SOURCES_BULLET_RE = re.compile(r"^- ([^\s(]+)(?:\s*\(.*\))?\s*$", re.MULTILINE)


def sources_section(text):
    m = re.search(r"^## Sources\b(.*?)(?=^## |\Z)", text,
                  re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if anything is broken (hook-friendly)")
    args = ap.parse_args()
    vault = Path(args.vault).expanduser()

    refs = []  # (defining_file, referenced_path)
    for card in sorted((vault / "cards").glob("*.md")):
        for ref in SOURCE_REF_RE.findall(card.read_text()):
            refs.append((card, ref))
    for note in sorted((vault / "notes").rglob("*.md")):
        for ref in SOURCES_BULLET_RE.findall(sources_section(note.read_text())):
            refs.append((note, ref))

    broken = []
    for owner, ref in refs:
        target = ref.split("#", 1)[0].strip()  # drop "#p12" page fragments
        if not (vault / target).is_file():
            broken.append((owner.relative_to(vault), ref))

    print(f"checked {len(refs)} provenance references "
          f"across cards and notes")
    if broken:
        print(f"BROKEN ({len(broken)}):")
        for owner, ref in broken:
            print(f"  {owner}: {ref}")
    else:
        print("all provenance targets exist")
    sys.exit(1 if (broken and args.strict) else 0)


if __name__ == "__main__":
    main()
