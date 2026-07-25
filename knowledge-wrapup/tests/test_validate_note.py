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

    def test_scope_versioned_requires_last_verified(self):
        bad = GOOD.replace("spec_version: 1", "spec_version: 1\nscope: versioned")
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("requires a last_verified", r.stdout)

    def test_privacy_home_path_fails(self):
        bad = GOOD.replace("Body prose.", "See /Users/alan/notes/x.md")
        r = self.validate(self.write_note(bad))
        self.assertEqual(r.returncode, 1)
        self.assertIn("real-looking username", r.stdout)

    def test_absolute_title_warns_not_fails(self):
        warn = GOOD.replace("# Good Note", "# Never Do This")
        r = self.validate(self.write_note(warn))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("absolute word", r.stdout)

    def test_empty_references_warns(self):
        warn = GOOD.replace("1. https://example.org — what it covers", "")
        r = self.validate(self.write_note(warn))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("empty '## References'", r.stdout)

    def test_destructive_without_recovery_warns(self):
        warn = GOOD.replace("Body prose.", "Run `git reset --hard origin/main`.")
        r = self.validate(self.write_note(warn))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("destructive command", r.stdout)

    def test_destructive_with_generic_preflight_and_recovery_passes(self):
        ok = GOOD.replace(
            "Body prose.",
            "Remove it with `rm -rf ~/data/cache/<name>` — check `<name>` "
            "first with the list command; restore anytime by re-running install.")
        r = self.validate(self.write_note(ok))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("destructive command", r.stdout)

    def test_tail_section_order_warns(self):
        warn = GOOD.replace(
            "- conversation-claude/conversation-20260718.md (discussed)",
            "- conversation-claude/conversation-20260718.md (discussed)\n\n"
            "## Related\n\n[[other]]")
        r = self.validate(self.write_note(warn))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("canonical order", r.stdout)

    def test_u7_mirror_list_count_mismatch_warns(self):
        warn = GOOD.replace(
            "Body prose.", "Body prose.\n\n1. First step.\n2. Second step.")
        r = self.validate(self.write_note(warn))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("U7 mirror: ordered-list items EN=2 vs translation=0", r.stdout)

    def test_u7_mirror_list_count_match_passes_clean(self):
        ok = GOOD.replace(
            "Body prose.", "Body prose.\n\n1. First step.\n2. Second step."
        ).replace("正文。", "正文。\n\n1. 第一步。\n2. 第二步。")
        r = self.validate(self.write_note(ok))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("U7 mirror", r.stdout)

    def test_u7_mirror_table_count_mismatch_warns(self):
        # the check only fires when the translation has >=1 table (a
        # translation with zero tables is not compared, by design) —
        # so use two EN tables against one ZH table to trigger it.
        warn = GOOD.replace(
            "Body prose.",
            "Body prose.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n"
            "| C | D |\n|---|---|\n| 3 | 4 |"
        ).replace("正文。", "正文。\n\n| 甲 | 乙 |\n|---|---|\n| 1 | 2 |")
        r = self.validate(self.write_note(warn))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("U7 mirror: tables EN=2 vs translation=1", r.stdout)


if __name__ == "__main__":
    unittest.main()
