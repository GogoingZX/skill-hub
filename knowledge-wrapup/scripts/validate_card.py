#!/usr/bin/env python3
"""Validate knowledge cards against card-spec (spec_version 1).

Usage:
    python3 validate_card.py CARD [CARD ...] --vault VAULT_PATH

Exit code 0 = all cards valid; 1 = at least one violation (printed per card).
No third-party dependencies: frontmatter is flat key/value YAML parsed here.
"""

import argparse
import re
import sys
from pathlib import Path

SPEC_VERSION = "1"
FILENAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*--\d{8}\.md$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

ENUMS = {
    "type": {"concept", "term", "howto", "gotcha", "tutorial"},
    "source": {"conversation", "note", "pdf"},
    "confidence": {"verified", "discussed"},
    "status": {"raw", "merged", "dropped"},
}

REQUIRED_FIELDS = [
    "spec_version", "topic", "type", "domain", "tags",
    "source", "source_ref", "confidence", "date", "status",
]

REQUIRED_SECTIONS = {
    "concept": ["Definition", "Usage scenarios", "Example", "Related"],
    "term": ["Definition", "Usage scenarios", "Example", "Related"],
    "howto": ["Goal", "Prerequisites", "Steps", "Verification", "Related"],
    "gotcha": ["Symptom", "Cause", "Fix", "How to avoid", "Related"],
    "tutorial": ["Goal", "Steps", "Result", "Related"],
}


def parse_frontmatter(text):
    """Parse flat key/value frontmatter. Returns (dict, error_or_None)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing frontmatter opening '---'"
    fm, end = {}, None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    if end is None:
        return {}, "missing frontmatter closing '---'"
    return fm, None


def parse_tags(raw):
    if not (raw.startswith("[") and raw.endswith("]")):
        return None
    inner = raw[1:-1].strip()
    if not inner:
        return []
    return [t.strip().strip('"').strip("'") for t in inner.split(",")]


def load_taxonomy(vault):
    """Parse TAXONOMY.md.

    Returns (domains, tag_registry):
      domains      — set like {'finance', 'finance/risk-management'}, or None
                     if TAXONOMY.md is missing.
      tag_registry — set of registered tags from the '## Tags' section, or None
                     if that section is absent (tag check is then skipped).
    """
    path = Path(vault) / "TAXONOMY.md"
    if not path.exists():
        return None, None
    domains, tags, current, in_tags = set(), None, None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Tags":
            in_tags, current, tags = True, None, set() if tags is None else tags
            continue
        h = re.match(r"^##\s+([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", line)
        if h:
            in_tags, current = False, h.group(1)
            domains.add(current)
            continue
        if re.match(r"^##\s+", line):  # non-slug heading, e.g. "## Rules"
            in_tags, current = False, None
            continue
        item = re.match(r"^-\s+([a-z0-9]+(?:-[a-z0-9]+)*)\s*(?:—.*)?$", line)
        if item:
            if in_tags:
                tags.add(item.group(1))
            elif current:
                domains.add(f"{current}/{item.group(1)}")
    return domains, tags


def validate(card_path, domains, tag_registry):
    errors = []
    p = Path(card_path)
    if not p.exists():
        return [f"file not found: {p}"]
    if not FILENAME_RE.match(p.name):
        errors.append(f"filename '{p.name}' must match '<topic-slug>--<yyyyMMdd>.md'")

    text = p.read_text(encoding="utf-8")
    fm, fm_err = parse_frontmatter(text)
    if fm_err:
        return errors + [fm_err]

    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] == "":
            errors.append(f"missing frontmatter field: {field}")
    if errors:
        return errors  # field-level checks below assume presence

    if fm["spec_version"] != SPEC_VERSION:
        errors.append(f"spec_version is '{fm['spec_version']}', expected '{SPEC_VERSION}'")
    for field, allowed in ENUMS.items():
        if fm[field] not in allowed:
            errors.append(f"{field} '{fm[field]}' not in {sorted(allowed)}")
    if not SLUG_RE.match(fm["topic"]):
        errors.append(f"topic '{fm['topic']}' is not lowercase kebab-case")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", fm["date"]):
        errors.append(f"date '{fm['date']}' is not yyyy-MM-dd")
    else:
        expected = f"{fm['topic']}--{fm['date'].replace('-', '')}.md"
        if FILENAME_RE.match(p.name) and p.name != expected:
            errors.append(f"filename '{p.name}' does not match topic+date ('{expected}')")

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
        domain_parts = set(fm["domain"].split("/"))
        redundant = [t for t in tags if t in domain_parts]
        if redundant:
            errors.append(
                f"tags {redundant} duplicate the domain '{fm['domain']}' — "
                f"the folder already says this; use tags for cross-cutting facets"
            )

    if not re.match(r"^[a-z0-9-]+(?:/[a-z0-9-]+)?$", fm["domain"]):
        errors.append(f"domain '{fm['domain']}' must be '<level1>' or '<level1>/<level2>'")
    elif domains is not None and fm["domain"] not in domains:
        errors.append(
            f"domain '{fm['domain']}' not in TAXONOMY.md — add it there first (and announce it)"
        )

    if fm["type"] in REQUIRED_SECTIONS:
        headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
        for section in REQUIRED_SECTIONS[fm["type"]]:
            if section not in headings:
                errors.append(f"missing required section for type '{fm['type']}': ## {section}")

    style_errors, style_warnings = check_style(text)
    errors.extend(style_errors)
    return errors, style_warnings


# --- markdown-style.md machine checks (U1/U2/U4) ---------------------------
# ①-⑳ (U+2460-2473), ⑴-⒇ (U+2474-2487), Ⅰ-Ⅻ (U+2160-216B), bullet glyphs.
CHAR_BLACKLIST_RE = re.compile(r"[①-⒇Ⅰ-Ⅻ•●▪◦]")
FENCE_RE = re.compile(r"```.*?```", flags=re.DOTALL)
# an enumeration marker: 1-2 digits + . 、 ) followed by space/CJK/bold —
# the lookbehind keeps decimals like "2.5" from matching.
ENUM_MARKER_RE = re.compile(r"(?<![\d.])\d{1,2}[.、)](?=\s|[一-鿿*])")


def check_style(text):
    """Enforce the machine-checkable subset of references/markdown-style.md:
    U1 char blacklist (errors), U4 mermaid label lint (errors),
    U1/U2 crammed-enumeration heuristic (warnings only)."""
    errors, warnings = [], []
    prose = FENCE_RE.sub("", text)

    hit = CHAR_BLACKLIST_RE.search(prose)
    if hit:
        errors.append(
            f"forbidden list-substitute character '{hit.group(0)}' "
            "(markdown-style U1) — use markdown list syntax")

    for lang, body in re.findall(r"```(\w*)\n(.*?)```", text, flags=re.DOTALL):
        if lang != "mermaid":
            continue
        for line in body.splitlines():
            bare = re.sub(r'"[^"]*"', "", line)  # quoted labels are fine
            snippet = line.strip()[:60]
            if "$" in bare:
                errors.append(f"mermaid label contains '$' (markdown-style U4"
                              f" — formulas go in prose): {snippet}")
            elif re.search(r"\[[^\]]*[({|][^\]]*\]", bare):
                errors.append(f"mermaid unquoted label with special char "
                              f"(markdown-style U4): {snippet}")
            elif bare.strip().startswith("subgraph") and re.search(r"[({]", bare):
                errors.append(f"mermaid unquoted subgraph title "
                              f"(markdown-style U4): {snippet}")

    for line in prose.splitlines():
        if line.lstrip().startswith(("|", "#")):
            continue  # tables and headings legitimately pack numbers
        if len(ENUM_MARKER_RE.findall(line)) >= 3:
            warnings.append(f"possible crammed enumeration — split into a "
                            f"markdown list (U1/U2): {line.strip()[:60]}")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards", nargs="+")
    ap.add_argument("--vault", required=True, help="vault path (for TAXONOMY.md lookup)")
    args = ap.parse_args()

    domains, tag_registry = load_taxonomy(Path(args.vault).expanduser())
    if domains is None:
        print(f"WARNING: TAXONOMY.md not found under {args.vault}; domain check skipped")
    if tag_registry is None:
        print(f"WARNING: no '## Tags' registry in TAXONOMY.md; tag vocabulary check skipped")

    failed = False
    for card in args.cards:
        result = validate(card, domains, tag_registry)
        errs, warns = result if isinstance(result, tuple) else (result, [])
        if errs:
            failed = True
            print(f"FAIL {card}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK   {card}")
        for w in warns:
            print(f"  ~ warn: {w}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
