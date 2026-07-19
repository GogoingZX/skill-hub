import tempfile
import unittest
from pathlib import Path

from helpers import make_vault, run

CARD = """---
source_ref: "{ref}"
---

# Card
"""

NOTE = """---
topic: n
---

# Note

## Sources

- {ref} (discussed)
"""


class CheckProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = make_vault(self.tmp.name, "# INDEX\n")
        diary = self.vault / "conversation-claude"
        diary.mkdir()
        (diary / "conversation-20260718.md").write_text("record\n")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, *extra):
        return run("check_provenance.py", "--vault", self.vault, *extra)

    def add_card(self, ref, name="c--20260718.md"):
        (self.vault / "cards" / name).write_text(CARD.format(ref=ref))

    def add_note(self, ref, name="n.md"):
        (self.vault / "notes" / name).write_text(NOTE.format(ref=ref))

    def test_existing_targets_pass(self):
        self.add_card("conversation-claude/conversation-20260718.md")
        self.add_note("conversation-claude/conversation-20260718.md")
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all provenance targets exist", r.stdout)
        self.assertIn("checked 2 provenance references", r.stdout)

    def test_pdf_page_fragment_is_stripped(self):
        (self.vault / "guide.pdf").write_bytes(b"%PDF-stub")
        self.add_card("guide.pdf#p12")
        r = self.check()
        self.assertIn("all provenance targets exist", r.stdout)

    def test_broken_ref_is_listed_but_exit_zero(self):
        self.add_card("conversation-claude/conversation-19990101.md")
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("BROKEN (1):", r.stdout)
        self.assertIn("conversation-19990101.md", r.stdout)

    def test_strict_mode_fails_on_broken_ref(self):
        self.add_note("does/not/exist.md")
        r = self.check("--strict")
        self.assertEqual(r.returncode, 1)
        self.assertIn("BROKEN (1):", r.stdout)


if __name__ == "__main__":
    unittest.main()
