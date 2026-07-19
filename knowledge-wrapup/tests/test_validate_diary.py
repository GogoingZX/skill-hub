import tempfile
import unittest
from pathlib import Path

from helpers import run

GOOD = """## 14:30 — one-line session headline

### Topic: Testing the gate

> [!summary]
> A 1–2 sentence takeaway.

**Details**

- one point per bullet
- a concrete example inline

**中文**

> [!summary]
> 中文要点。

- 中文细节,一条一行。
"""


class ValidateDiaryTest(unittest.TestCase):
    def check(self, text, *extra):
        return run("validate_diary.py", "-", "--language", "zh-CN", *extra,
                   stdin=text)

    def test_valid_section_passes(self):
        r = self.check(GOOD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_file_argument_works(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(GOOD)
        r = run("validate_diary.py", f.name, "--language", "zh-CN")
        Path(f.name).unlink()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_no_topic_block_fails(self):
        r = self.check("## 14:30 — headline\n\njust prose\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no '### Topic:' block", r.stdout)

    def test_missing_summary_fails(self):
        r = self.check(GOOD.replace("> [!summary]\n> A 1–2 sentence takeaway.\n", ""))
        self.assertEqual(r.returncode, 1)
        self.assertIn("[!summary]", r.stdout)

    def test_missing_translation_fails_for_zh(self):
        bad = GOOD.split("**中文**")[0]
        r = self.check(bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn("translation block", r.stdout)

    def test_translation_not_required_for_en(self):
        bad = GOOD.split("**中文**")[0]
        r = run("validate_diary.py", "-", "--language", "en", stdin=bad)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_forbidden_list_character_fails(self):
        r = self.check(GOOD.replace("- one point per bullet", "① one point"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("forbidden list-substitute character", r.stdout)


if __name__ == "__main__":
    unittest.main()
