#!/usr/bin/env python3
"""Validate a STAGED diary section before it is appended (SKILL.md Step 5b).

The diary is append-only — a defect that lands there stays there — so this
gate runs on the staged section text, never on the diary file itself.

Usage:
    python3 validate_diary.py STAGED_FILE [--language zh-CN]
    ... | python3 validate_diary.py - [--language zh-CN]

Checks (E = error, fails; W = warning, printed only):
  E markdown-style machine checks (U1 char blacklist, U4 mermaid lint)
    via validate_card.check_style
  E at least one `### Topic:` block
  E every topic block has a `> [!summary]` callout
  E when --language is not "en": every topic block has a translation block
    (a bold marker line; default marker 中文 — override with
    --translation-marker for other languages)
  W crammed-enumeration heuristic (from check_style)

Exit code 0 = section may be appended; 1 = fix it first.
"""

import argparse
import re
import sys
from pathlib import Path

from validate_card import check_style

TOPIC_RE = re.compile(r"^### Topic:", re.MULTILINE)


def validate(text, language, marker):
    errors, warnings = [], []

    style_errors, style_warnings = check_style(text)
    errors.extend(style_errors)
    warnings.extend(style_warnings)

    starts = [m.start() for m in TOPIC_RE.finditer(text)]
    if not starts:
        errors.append("no '### Topic:' block — the diary section is topic-structured")
        return errors, warnings

    bounds = list(zip(starts, starts[1:] + [len(text)]))
    for n, (a, b) in enumerate(bounds, 1):
        block = text[a:b]
        title = block.splitlines()[0].strip()
        # split at the translation marker so the Chinese mirror can't stand in
        # for a missing English summary
        head, sep, tail = block.partition(f"**{marker}")
        if "[!summary]" not in head:
            errors.append(f"topic {n} ({title}) has no > [!summary] callout "
                          "in its English part")
        if language.lower() != "en":
            if not sep:
                errors.append(f"topic {n} ({title}) has no '**{marker}**' "
                              "translation block")
            elif "[!summary]" not in tail:
                warnings.append(f"topic {n} ({title}): translation block has "
                                "no [!summary] mirror")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("staged", help="staged section file, or '-' for stdin")
    ap.add_argument("--language", default="zh-CN",
                    help='vault localization language; "en" skips translation checks')
    ap.add_argument("--translation-marker", default="中文",
                    help="bold label that opens each topic's translation block")
    args = ap.parse_args()

    text = (sys.stdin.read() if args.staged == "-"
            else Path(args.staged).read_text())
    errors, warnings = validate(text, args.language, args.translation_marker)

    name = "<stdin>" if args.staged == "-" else args.staged
    if errors:
        print(f"FAIL {name}")
        for e in errors:
            print(f"  - {e}")
    else:
        print(f"OK   {name}")
    for w in warnings:
        print(f"  ~ warn: {w}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
