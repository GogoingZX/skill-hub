#!/usr/bin/env python3
"""Validate curated notes against integration-rules + markdown-style.

Usage:
    python3 validate_note.py NOTE [NOTE ...] [--language zh-CN]

Checks (E = error, fails; W = warning, printed only):
  E frontmatter: topic/domain/tags/status/spec_version present,
    status in {active, disputed}, filename == <topic>.md
  E at least one [!summary] callout in the English body
  E translation section present when --language is not "en"
  E markdown-style machine checks (U1 char blacklist, U4 mermaid lint)
    via validate_card.check_style, on the WHOLE file
  W crammed-enumeration heuristic (from check_style)
  W structure mirroring (U7): ordered-list item count and table count
    should match between the English body (Related/Sources excluded)
    and the translation section

Exit code 0 = all notes pass; 1 = at least one error.
"""

import argparse
import re
import sys
from pathlib import Path

from validate_card import check_style, parse_frontmatter

REQUIRED_FIELDS = ["topic", "domain", "tags", "status", "spec_version"]
STATUS_ENUM = {"active", "disputed"}
TRANSLATION_HEADING_RE = re.compile(r"^## \S*(翻译|译文|translation)\S*\s*$",
                                    re.MULTILINE | re.IGNORECASE)
ORDERED_ITEM_RE = re.compile(r"^\s*\d+\.\s", re.MULTILINE)
TABLE_SEP_RE = re.compile(r"^\|[-| :]+\|\s*$", re.MULTILINE)


def _strip_sections(text, names):
    """Drop `## <name>` sections (until the next ## or end) from text."""
    for name in names:
        text = re.sub(rf"^## {name}\b.*?(?=^## |\Z)", "", text,
                      flags=re.MULTILINE | re.DOTALL)
    return text


def validate(path, language):
    p = Path(path)
    text = p.read_text()
    errors, warnings = [], []

    fm, fm_err = parse_frontmatter(text)
    if fm_err:
        return [fm_err], warnings
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"missing frontmatter field: {field}")
    if fm.get("status") and fm["status"] not in STATUS_ENUM:
        errors.append(f"status '{fm['status']}' not in {sorted(STATUS_ENUM)}")
    if fm.get("topic") and p.name != f"{fm['topic']}.md":
        errors.append(f"filename '{p.name}' != topic '{fm['topic']}.md'")

    m = TRANSLATION_HEADING_RE.search(text)
    en_body, zh_body = (text[:m.start()], text[m.start():]) if m else (text, "")

    if "[!summary]" not in en_body:
        errors.append("English body has no > [!summary] callout")
    if language.lower() != "en":
        if not m:
            errors.append(f"language is '{language}' but no translation "
                          "section heading found")
        elif "[!summary]" not in zh_body:
            warnings.append("translation section has no [!summary] mirror")

    style_errors, style_warnings = check_style(text)
    errors.extend(style_errors)
    warnings.extend(style_warnings)

    # U7 structure mirroring — WARN only; Related/Sources/References exist
    # only on the English side by design, so exclude them before counting.
    if m:
        en_core = _strip_sections(en_body, ["Related", "Sources", "References"])
        en_items = len(ORDERED_ITEM_RE.findall(en_core))
        zh_items = len(ORDERED_ITEM_RE.findall(zh_body))
        if en_items != zh_items:
            warnings.append(f"U7 mirror: ordered-list items EN={en_items} "
                            f"vs translation={zh_items}")
        en_tables = len(TABLE_SEP_RE.findall(en_core))
        zh_tables = len(TABLE_SEP_RE.findall(zh_body))
        if zh_tables > 0 and en_tables != zh_tables:
            warnings.append(f"U7 mirror: tables EN={en_tables} "
                            f"vs translation={zh_tables}")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notes", nargs="+")
    ap.add_argument("--language", default="zh-CN",
                    help='vault localization language; "en" skips translation checks')
    args = ap.parse_args()

    failed = False
    for note in args.notes:
        errs, warns = validate(note, args.language)
        if errs:
            failed = True
            print(f"FAIL {note}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK   {note}")
        for w in warns:
            print(f"  ~ warn: {w}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
