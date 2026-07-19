#!/usr/bin/env python3
"""Validate curated notes against integration-rules + markdown-style.

Usage:
    python3 validate_note.py NOTE [NOTE ...] [--language zh-CN] [--vault VAULT]

Checks (E = error, fails; W = warning, printed only):
  E frontmatter: topic/domain/tags/status/spec_version present and non-empty,
    status in {active, disputed}, spec_version == 1, filename == <topic>.md
  E tags are a [list] of 1-5 kebab-case slugs; with --vault, tags must be in
    the TAXONOMY '## Tags' registry and must not duplicate the domain
  E domain is '<level1>' or '<level1>/<level2>'; with --vault, it must exist
    in TAXONOMY.md, and when the note lives under <vault>/notes/ its folder
    path must equal the declared domain
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

from validate_card import SLUG_RE, check_style, load_taxonomy, parse_frontmatter, parse_tags

REQUIRED_FIELDS = ["topic", "domain", "tags", "status", "spec_version"]
STATUS_ENUM = {"active", "disputed"}
SPEC_VERSION = "1"
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


def validate(path, language, domains=None, tag_registry=None, vault=None):
    p = Path(path)
    text = p.read_text()
    errors, warnings = [], []

    fm, fm_err = parse_frontmatter(text)
    if fm_err:
        return [fm_err], warnings
    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] == "":
            errors.append(f"missing frontmatter field: {field}")
    if fm.get("status") and fm["status"] not in STATUS_ENUM:
        errors.append(f"status '{fm['status']}' not in {sorted(STATUS_ENUM)}")
    if fm.get("spec_version") and fm["spec_version"] != SPEC_VERSION:
        errors.append(f"spec_version is '{fm['spec_version']}', expected '{SPEC_VERSION}'")
    if fm.get("topic") and p.name != f"{fm['topic']}.md":
        errors.append(f"filename '{p.name}' != topic '{fm['topic']}.md'")

    if fm.get("tags"):
        tags = parse_tags(fm["tags"])
        if tags is None:
            errors.append(f"tags '{fm['tags']}' is not a [list]")
        elif not 1 <= len(tags) <= 5:
            errors.append(f"tags count {len(tags)} outside 1–5")
        elif not all(SLUG_RE.match(t) for t in tags):
            errors.append(f"tags {tags} must all be lowercase kebab-case")
        else:
            if tag_registry is not None:
                unregistered = [t for t in tags if t not in tag_registry]
                if unregistered:
                    errors.append(
                        f"tags {unregistered} not in TAXONOMY.md '## Tags' registry — "
                        f"reuse a registered tag or register the new one first (and announce it)"
                    )
            if fm.get("domain"):
                redundant = [t for t in tags if t in set(fm["domain"].split("/"))]
                if redundant:
                    errors.append(
                        f"tags {redundant} duplicate the domain '{fm['domain']}' — "
                        f"the folder already says this; use tags for cross-cutting facets"
                    )
    if fm.get("domain"):
        if not re.match(r"^[a-z0-9-]+(?:/[a-z0-9-]+)?$", fm["domain"]):
            errors.append(f"domain '{fm['domain']}' must be '<level1>' or '<level1>/<level2>'")
        elif domains is not None and fm["domain"] not in domains:
            errors.append(
                f"domain '{fm['domain']}' not in TAXONOMY.md — add it there first (and announce it)"
            )
        if vault is not None:
            try:
                rel = p.resolve().relative_to((Path(vault) / "notes").resolve())
            except ValueError:
                rel = None  # staged outside the vault; nothing to compare
            if rel is not None:
                if len(rel.parts) < 2:
                    errors.append("note sits directly in notes/ — it must live "
                                  "in notes/<domain>/ (one concept = one note file)")
                else:
                    path_domain = "/".join(rel.parts[:-1])
                    if path_domain != fm["domain"]:
                        errors.append(
                            f"domain '{fm['domain']}' does not match the note's "
                            f"folder 'notes/{path_domain}/'")

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
    ap.add_argument("--vault", default=None,
                    help="vault path; enables TAXONOMY domain/tag checks")
    args = ap.parse_args()

    domains = tag_registry = vault = None
    if args.vault:
        vault = Path(args.vault).expanduser()
        domains, tag_registry = load_taxonomy(vault)
        if domains is None:
            print(f"WARNING: TAXONOMY.md not found under {args.vault}; domain check skipped")
        if tag_registry is None:
            print(f"WARNING: no '## Tags' registry in TAXONOMY.md; tag vocabulary check skipped")

    failed = False
    for note in args.notes:
        errs, warns = validate(note, args.language, domains, tag_registry, vault)
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
