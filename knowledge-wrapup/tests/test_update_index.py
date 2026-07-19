import tempfile
import unittest
from pathlib import Path

from helpers import make_vault, run

INDEX = """# INDEX — knowledge base navigation

## finance

### tools

- [Beta Note](notes/finance/tools/beta.md) — b

## technology

### tools

- [Alpha Note](notes/technology/tools/alpha.md) — a
- [Gamma Note](notes/technology/tools/gamma.md) — g
"""


class UpdateIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = make_vault(self.tmp.name, INDEX)

    def tearDown(self):
        self.tmp.cleanup()

    def add_note(self, rel):
        p = self.vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("stub\n")

    def update(self, note, title, summary="s", *extra):
        return run("update_index.py", "--vault", self.vault, "--note", note,
                   "--title", title, "--summary", summary, *extra)

    def index(self):
        return (self.vault / "INDEX.md").read_text()

    def section(self, text, heading):
        """Body of `heading` up to the next heading of same-or-higher level."""
        lines = text.splitlines()
        i = lines.index(heading)
        level = heading.split(" ")[0]
        body = []
        for line in lines[i + 1:]:
            if line.startswith("#") and line.split(" ")[0] <= level:
                break
            body.append(line)
        return "\n".join(body)

    def test_bounded_subsection_same_name(self):
        """A '### tools' under technology must not receive finance entries."""
        self.add_note("notes/technology/tools/delta.md")
        r = self.update("notes/technology/tools/delta.md", "Delta Note")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.index()
        finance = self.section(text, "## finance")
        tech = self.section(text, "## technology")
        self.assertNotIn("delta.md", finance)
        self.assertIn("delta.md", tech)

    def test_alphabetical_insert(self):
        self.add_note("notes/technology/tools/delta.md")
        self.update("notes/technology/tools/delta.md", "Delta Note")
        tech = self.section(self.index(), "## technology")
        order = [t for t in ("Alpha Note", "Delta Note", "Gamma Note")]
        positions = [tech.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))

    def test_resorts_unsorted_block(self):
        self.add_note("notes/technology/tools/aardvark.md")
        self.update("notes/technology/tools/aardvark.md", "Aardvark Note")
        tech = self.section(self.index(), "## technology")
        self.assertLess(tech.index("Aardvark Note"), tech.index("Alpha Note"))

    def test_update_in_place_no_duplicate(self):
        self.add_note("notes/technology/tools/alpha.md")
        r = self.update("notes/technology/tools/alpha.md", "Alpha Note v2", "new hook")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.index()
        self.assertEqual(text.count("alpha.md"), 1)
        self.assertIn("Alpha Note v2", text)
        self.assertIn("new hook", text)

    def test_identical_rerun_unchanged(self):
        self.add_note("notes/technology/tools/delta.md")
        self.update("notes/technology/tools/delta.md", "Delta Note", "hook")
        before = self.index()
        r = self.update("notes/technology/tools/delta.md", "Delta Note", "hook")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("unchanged", r.stdout)
        self.assertEqual(self.index(), before)

    def test_missing_subsection_created_at_section_end(self):
        self.add_note("notes/technology/newsub/x.md")
        r = self.update("notes/technology/newsub/x.md", "X Note")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.index()
        self.assertIn("created new subsection '### newsub'", r.stdout)
        tech = self.section(text, "## technology")
        self.assertLess(tech.index("### tools"), tech.index("### newsub"))
        self.assertIn("x.md", self.section(text, "### newsub"))

    def test_level1_only_note_before_subsections(self):
        self.add_note("notes/technology/solo.md")
        r = self.update("notes/technology/solo.md", "Solo Note")
        self.assertEqual(r.returncode, 0, r.stderr)
        tech = self.section(self.index(), "## technology")
        self.assertLess(tech.index("solo.md"), tech.index("### tools"))

    def test_missing_level1_is_hard_error(self):
        self.add_note("notes/nonexistent/x.md")
        r = self.update("notes/nonexistent/x.md", "X")
        self.assertEqual(r.returncode, 2)
        self.assertIn("TAXONOMY", r.stderr)

    def test_dry_run_leaves_file_untouched(self):
        self.add_note("notes/technology/tools/delta.md")
        before = self.index()
        r = self.update("notes/technology/tools/delta.md", "Delta Note", "s",
                        "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("DRY-RUN", r.stdout)
        self.assertEqual(self.index(), before)


if __name__ == "__main__":
    unittest.main()
