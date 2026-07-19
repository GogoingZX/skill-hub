import tempfile
import unittest
from pathlib import Path

from helpers import make_vault, run

GOOD = """---
spec_version: 1
topic: good-card
type: howto
domain: technology/tools
tags: [git, best-practice]
source: conversation
source_ref: "conversation-claude/conversation-20260718.md"
confidence: discussed
date: 2026-07-18
status: raw
---

# Good Card

## Goal
X.

## Prerequisites
Y.

## Steps
1. Do the thing.

## Verification
Z.

## Related
[[other-topic]]
"""


class ValidateCardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = make_vault(self.tmp.name, "# INDEX\n\n## technology\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write_card(self, text, name="good-card--20260718.md"):
        p = self.vault / "cards" / name
        p.write_text(text)
        return p

    def test_valid_card_passes(self):
        r = run("validate_card.py", self.write_card(GOOD), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_sections_out_of_order_fail(self):
        swapped = GOOD.replace("## Prerequisites\nY.", "## TMP\nY.") \
                      .replace("## Steps\n1. Do the thing.",
                               "## Prerequisites\n1. Do the thing.") \
                      .replace("## TMP\nY.", "## Steps\nY.")
        r = run("validate_card.py", self.write_card(swapped), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("out of order", r.stdout)

    def test_impossible_calendar_date_fails(self):
        bad = GOOD.replace("date: 2026-07-18", "date: 2026-13-45")
        r = run("validate_card.py",
                self.write_card(bad, "good-card--20261345.md"),
                "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a real calendar date", r.stdout)

    def test_forbidden_list_character_fails(self):
        bad = GOOD.replace("## Goal\nX.", "## Goal\n① first ② second")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("forbidden list-substitute character", r.stdout)

    def test_unregistered_tag_fails(self):
        bad = GOOD.replace("tags: [git, best-practice]", "tags: [notatag]")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not in TAXONOMY.md '## Tags' registry", r.stdout)


if __name__ == "__main__":
    unittest.main()
