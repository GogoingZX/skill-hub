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

    def test_forbidden_dingbat_digit_fails(self):
        bad = GOOD.replace("## Goal\nX.", "## Goal\n➀ first ➁ second")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("forbidden list-substitute character", r.stdout)

    def test_forbidden_fullwidth_digit_fails(self):
        bad = GOOD.replace("## Goal\nX.", "## Goal\n１. first ２. second")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("forbidden list-substitute character", r.stdout)

    def test_unregistered_tag_fails(self):
        bad = GOOD.replace("tags: [git, best-practice]", "tags: [notatag]")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not in TAXONOMY.md '## Tags' registry", r.stdout)

    def test_scope_invalid_value_fails(self):
        bad = GOOD.replace("status: raw", "status: raw\nscope: bogus")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("scope 'bogus' not in", r.stdout)

    def test_scope_versioned_requires_last_verified(self):
        bad = GOOD.replace("status: raw", "status: raw\nscope: versioned")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("requires a last_verified", r.stdout)

    def test_scope_versioned_with_last_verified_passes(self):
        ok = GOOD.replace("status: raw",
                          "status: raw\nscope: versioned\nlast_verified: 2026-07-21")
        r = run("validate_card.py", self.write_card(ok), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_privacy_home_path_fails(self):
        bad = GOOD.replace("## Goal\nX.", "## Goal\nRun /Users/alan/proj/x.py")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("real-looking username", r.stdout)

    def test_privacy_placeholder_home_path_passes(self):
        ok = GOOD.replace("## Goal\nX.", "## Goal\nRun /Users/<user>/proj/x.py")
        r = run("validate_card.py", self.write_card(ok), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_privacy_denylist_fails(self):
        bad = GOOD.replace("## Goal\nX.", "## Goal\nCredit to alan here.")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault,
                "--privacy-denylist", "alan")
        self.assertEqual(r.returncode, 1)
        self.assertIn("privacy denylist", r.stdout)

    def test_empty_references_warns(self):
        warn = GOOD.replace("## Related\n[[other-topic]]",
                            "## References\n\n## Related\n[[other-topic]]")
        r = run("validate_card.py", self.write_card(warn), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("empty '## References'", r.stdout)

    def test_ratio_data_line_does_not_warn_crammed(self):
        ok = GOOD.replace("## Goal\nX.",
                          "## Goal\n- 实测:欧洲 4/4、加拿大 4/4、日本 3/4、澳洲 3/4")
        r = run("validate_card.py", self.write_card(ok), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("crammed", r.stdout)

    def test_crammed_enumeration_still_warns(self):
        warn = GOOD.replace("## Goal\nX.",
                            "## Goal\n步骤:1、克隆仓库 2、安装依赖 3、运行测试")
        r = run("validate_card.py", self.write_card(warn), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("crammed", r.stdout)

    def test_topic_with_id_suffix_passes(self):
        ok = GOOD.replace("topic: good-card", "topic: good-card--pep723")
        r = run("validate_card.py",
                self.write_card(ok, "good-card--pep723--20260718.md"),
                "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_tag_with_id_suffix_fails(self):
        bad = GOOD.replace("tags: [git, best-practice]", "tags: [git--pep723]")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("kebab-case", r.stdout)

    def test_same_day_sibling_disambiguator_passes(self):
        # card-spec: every extraction is a new card, never a re-opened one —
        # a second same-day same-topic card gets a '-<n>' filename suffix.
        r = run("validate_card.py",
                self.write_card(GOOD, "good-card--20260718-2.md"),
                "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_filename_disambiguator_on_wrong_topic_fails(self):
        bad = GOOD.replace("topic: good-card", "topic: other-card")
        r = run("validate_card.py",
                self.write_card(bad, "good-card--20260718-2.md"),
                "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match topic+date", r.stdout)

    def test_merged_card_warnings_suppressed(self):
        warn = GOOD.replace("## Related\n[[other-topic]]",
                            "## References\n\n## Related\n[[other-topic]]") \
                   .replace("status: raw", "status: merged")
        r = run("validate_card.py", self.write_card(warn), "--vault", self.vault)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("warn:", r.stdout)

    def test_merged_card_errors_still_fail(self):
        bad = GOOD.replace("status: raw", "status: merged") \
                  .replace("## Goal\nX.", "## Goal\nRun /Users/alan/proj/x.py")
        r = run("validate_card.py", self.write_card(bad), "--vault", self.vault)
        self.assertEqual(r.returncode, 1)
        self.assertIn("real-looking username", r.stdout)


if __name__ == "__main__":
    unittest.main()
