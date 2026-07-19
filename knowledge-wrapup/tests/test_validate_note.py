import tempfile
import unittest
from pathlib import Path

from helpers import make_vault, run

GOOD = """---
topic: good-note
domain: technology/tools
tags: [git]
status: active
spec_version: 1
---

# Good Note

> [!summary]
> The essence of the note.

Body prose.

## References

1. https://example.org — what it covers

## Sources

- conversation-claude/conversation-20260718.md (discussed)

---

## 中文翻译

**好笔记**

> [!summary]
> 笔记要点。

正文。
"""


class ValidateNoteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = make_vault(self.tmp.name, "# INDEX\n\n## technology\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write_note(self, text, name="good-note.md", subdir="technology/tools"):
        p = self.vault / "notes" / subdir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def validate(self, path, *extra):
        return run("validate_note.py", path, "--language", "zh-CN",
                   "--vault", self.vault, *extra)

    def test_valid_note_passes(self):
        r = self.validate(self.write_note(GOOD))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unregistered_tag_fails_with_vault(self):
        bad = GOOD.replace("tags: [git]", "tags: [notatag]")
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("not in TAXONOMY.md '## Tags' registry", r.stdout)

    def test_unknown_domain_fails_with_vault(self):
        bad = GOOD.replace("domain: technology/tools", "domain: technology/nope")
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("not in TAXONOMY.md", r.stdout)

    def test_empty_required_field_fails(self):
        bad = GOOD.replace("tags: [git]", "tags:")
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing frontmatter field: tags", r.stdout)

    def test_missing_translation_fails_for_zh(self):
        bad = GOOD.split("---\n\n## 中文翻译")[0]
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("no translation", r.stdout)

    def test_wrong_spec_version_fails(self):
        bad = GOOD.replace("spec_version: 1", "spec_version: 2")
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("spec_version", r.stdout)

    def test_domain_folder_mismatch_fails(self):
        r = self.validate(self.write_note(GOOD, subdir="technology/api-design"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match the note's folder", r.stdout)

    def test_note_directly_in_notes_fails(self):
        r = self.validate(self.write_note(GOOD, subdir="."))
        self.assertEqual(r.returncode, 1)
        self.assertIn("directly in notes/", r.stdout)

    def test_staged_note_outside_vault_skips_path_check(self):
        with tempfile.TemporaryDirectory() as outside:
            staged = Path(outside) / "good-note.md"
            staged.write_text(GOOD)
            r = self.validate(staged)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
