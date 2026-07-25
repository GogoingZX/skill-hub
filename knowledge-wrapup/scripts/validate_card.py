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
from datetime import date
from pathlib import Path

SPEC_VERSION = "1"
# A topic may carry one optional '--<id>' suffix anchor (card-spec: spec/standard
# numbers, e.g. python-inline-script-deps--pep723); tags may not. A same-day
# sibling card (card-spec: file naming — every extraction is a new card, never
# an edit) may carry a trailing '-<n>' disambiguator before '.md', n >= 2.
FILENAME_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:--[a-z0-9]+)?--\d{8}(?:-\d+)?\.md$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOPIC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:--[a-z0-9]+)?$")

ENUMS = {
    "type": {"concept", "term", "howto", "gotcha", "tutorial"},
    "source": {"conversation", "note", "pdf"},
    "confidence": {"verified", "discussed"},
    "status": {"raw", "merged", "dropped"},
}

# Optional claim-scope field (spec 1.1+): validated when present, never required
# (a judgment field — enforced at spec level, not as a hard gate). universal |
# versioned | observed | policy; versioned/observed also require last_verified.
SCOPE_ENUM = {"universal", "versioned", "observed", "policy"}

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


def validate(card_path, domains, tag_registry, denylist=None):
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
    if not TOPIC_RE.match(fm["topic"]):
        errors.append(f"topic '{fm['topic']}' is not lowercase kebab-case "
                      f"(one optional '--<id>' suffix allowed)")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", fm["date"]):
        errors.append(f"date '{fm['date']}' is not yyyy-MM-dd")
    else:
        try:
            date.fromisoformat(fm["date"])
        except ValueError:
            errors.append(f"date '{fm['date']}' is not a real calendar date")
        expected = f"{fm['topic']}--{fm['date'].replace('-', '')}.md"
        expected_stem = expected[:-3]  # strip '.md' for the disambiguator check
        same_day_sibling = re.match(re.escape(expected_stem) + r"-\d+\.md$", p.name)
        if FILENAME_RE.match(p.name) and p.name != expected and not same_day_sibling:
            errors.append(f"filename '{p.name}' does not match topic+date "
                          f"('{expected}', optionally '{expected_stem}-<n>.md')")

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
        required = REQUIRED_SECTIONS[fm["type"]]
        headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
        missing = [s for s in required if s not in headings]
        for section in missing:
            errors.append(f"missing required section for type '{fm['type']}': ## {section}")
        if not missing:
            found = [h for h in headings if h in required]
            if found != required:  # wrong order, or a duplicated section
                errors.append(
                    f"required sections out of order for type '{fm['type']}': "
                    f"found {found}, spec order is {required}")

    errors.extend(check_scope(fm))
    style_errors, style_warnings = check_style(text)
    errors.extend(style_errors)
    priv_errors, priv_warnings = check_privacy(text, denylist)
    errors.extend(priv_errors)
    warnings = style_warnings + priv_warnings + check_references(text)
    if fm["status"] == "merged":
        # Frozen provenance snapshots (card-spec: freeze rule) may not be edited
        # to act on advisory warnings — suppressing them keeps audit output
        # signal-bearing. Errors (structure, enums, privacy) still apply.
        # 'merged' is terminal (card-spec: every extraction is a new card,
        # never a re-opened one) — the sole edit path is an in-place privacy
        # scrub, which does not change status.
        warnings = []
    return errors, warnings


# --- markdown-style.md machine checks (U1/U2/U4) ---------------------------
# ①-⑳ (U+2460-2473), ⑴-⒇ (U+2474-2487), ➀-➉ (U+2780-2789), Ⅰ-Ⅻ (U+2160-216B),
# full-width digits (U+FF10-FF19), bullet glyphs.
CHAR_BLACKLIST_RE = re.compile(r"[①-⒇➀-➉Ⅰ-Ⅻ０-９•●▪◦]")
FENCE_RE = re.compile(r"```.*?```", flags=re.DOTALL)
# an enumeration marker: 1-2 digits + . 、 ) followed by space/CJK/bold —
# the lookbehind keeps decimals like "2.5" and ratios like "4/4、" from matching.
ENUM_MARKER_RE = re.compile(r"(?<![\d./])\d{1,2}[.、)](?=\s|[一-鿿*])")


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


def check_scope(fm):
    """Validate the optional claim-scope field. Returns a list of errors (empty
    when scope is absent — the field is optional)."""
    errors = []
    scope = fm.get("scope", "")
    if not scope:
        return errors
    if scope not in SCOPE_ENUM:
        return [f"scope '{scope}' not in {sorted(SCOPE_ENUM)}"]
    if scope in {"versioned", "observed"}:
        lv = fm.get("last_verified", "")
        if not lv:
            errors.append(f"scope '{scope}' requires a last_verified date (yyyy-MM-dd)")
        elif not re.match(r"^\d{4}-\d{2}-\d{2}$", lv):
            errors.append(f"last_verified '{lv}' is not yyyy-MM-dd")
        else:
            try:
                date.fromisoformat(lv)
            except ValueError:
                errors.append(f"last_verified '{lv}' is not a real calendar date")
    return errors


# --- privacy scan (A1): synthetic-data rule from card-spec ------------------
# A literal home path with a real-looking username, or a non-example email, is a
# privacy-red-line violation in vault content. Placeholders are allowed.
HOME_PATH_RE = re.compile(r"/(?:Users|home)/(?!<|\$)([A-Za-z0-9._-]+)/")
PLACEHOLDER_USERS = {"user", "username", "you", "me", "name", "example",
                     "youruser", "dev-a", "someone"}
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
EXAMPLE_EMAIL_DOMAINS = {"example.com", "example.org", "example.net", "test.com",
                         "company.com", "foo.com", "acme.com", "email.com"}


def check_references(text):
    """A3: a present-but-empty '## References' heading is a defect — omit it or
    state 'none — <why>'. Returns a list of warnings."""
    m = re.search(r"^##+\s+References\s*\n(.*?)(?=^##+\s|\Z)", text,
                  re.MULTILINE | re.DOTALL)
    if m and not m.group(1).strip():
        return ["empty '## References' heading — omit it, or write "
                "'none — <why>' (card-spec: references policy)"]
    return []


def check_privacy(text, denylist=None):
    """Scan for private identifiers (A1). Returns (errors, warnings).
    Home paths with a real-looking user and denylisted terms are errors;
    non-example emails are warnings."""
    errors, warnings = [], []
    for m in HOME_PATH_RE.finditer(text):
        if m.group(1).lower() not in PLACEHOLDER_USERS:
            errors.append(
                f"absolute home path with a real-looking username: '{m.group(0)}' "
                f"— use ~ or a placeholder like /Users/<user>/ (card-spec: synthetic data)")
    for m in EMAIL_RE.finditer(text):
        if m.group(0).split("@", 1)[1].lower() not in EXAMPLE_EMAIL_DOMAINS:
            warnings.append(
                f"email address '{m.group(0)}' — if real, replace with an "
                f"example.com address or remove (card-spec: synthetic data)")
    for term in (denylist or []):
        term = term.strip()
        if term and re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I):
            errors.append(
                f"private identifier '{term}' (privacy denylist) appears in the "
                f"content — synthesize it (card-spec: synthetic data)")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards", nargs="+")
    ap.add_argument("--vault", required=True, help="vault path (for TAXONOMY.md lookup)")
    ap.add_argument("--privacy-denylist", default="",
                    help="comma-separated private identifiers to flag (usernames, real names)")
    args = ap.parse_args()

    denylist = [t for t in args.privacy_denylist.split(",") if t.strip()]
    domains, tag_registry = load_taxonomy(Path(args.vault).expanduser())
    if domains is None:
        print(f"WARNING: TAXONOMY.md not found under {args.vault}; domain check skipped")
    if tag_registry is None:
        print(f"WARNING: no '## Tags' registry in TAXONOMY.md; tag vocabulary check skipped")

    failed = False
    for card in args.cards:
        result = validate(card, domains, tag_registry, denylist)
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
