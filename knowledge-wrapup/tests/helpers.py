"""Shared plumbing for the script tests: run a script as a subprocess
against a throwaway vault, exactly as the skill invokes it."""

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

TAXONOMY = """# TAXONOMY — test fixture

## technology
- tools

## finance
- tools

## Tags

- git
- best-practice

## Rules

Prose, ignored by the parser.
"""


def run(script, *args, stdin=None):
    """Run scripts/<script> with args; returns CompletedProcess (text mode)."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *[str(a) for a in args]],
        capture_output=True, text=True, input=stdin)


def make_vault(root, index_text):
    """Create a minimal vault: INDEX.md, TAXONOMY.md, cards/, notes/."""
    root = Path(root)
    (root / "INDEX.md").write_text(index_text)
    (root / "TAXONOMY.md").write_text(TAXONOMY)
    (root / "cards").mkdir()
    (root / "notes").mkdir()
    return root
