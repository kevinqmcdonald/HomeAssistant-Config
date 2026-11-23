"""Tests for lint_dashboard.py."""
import fnmatch
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lint_dashboard as ld  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FIX = os.path.join(HERE, "fixtures", "lint")
ALLOWLIST = ld.load_allowlist(os.path.join(REPO, ".claude", "reference", "installed-cards.yaml"))


def lint(name):
    return ld.lint_file(os.path.join(FIX, name), ALLOWLIST)


def by_rule(findings, rule):
    return [f for f in findings if f.rule == rule]


class LintDashboardTest(unittest.TestCase):
    def test_good_file_clean(self):
        self.assertEqual(lint("good.yaml"), [])

    def test_unknown_custom_card(self):
        found = by_rule(lint("bad.yaml"), "unknown-card-type")
        self.assertEqual([(f.severity, f.where) for f in found], [("error", "/views/0/sections/0/cards/0")])

    def test_hex_and_rgba_flagged(self):
        found = by_rule(lint("bad.yaml"), "hardcoded-color")
        self.assertEqual(sorted(f.where for f in found), ["line 12", "line 15"])
        self.assertTrue(all(f.severity == "error" for f in found))

    def test_colour_message_quotes_full_literal(self):
        found = {f.where: f.message for f in by_rule(lint("bad.yaml"), "hardcoded-color")}
        self.assertIn("rgba(180,130,80,0.15)", found["line 15"])
        self.assertIn("#c47a3a", found["line 12"])

    def test_token_colours_not_flagged(self):
        self.assertEqual(by_rule(lint("good.yaml"), "hardcoded-color"), [])

    def test_lint_ignore_comment(self):
        self.assertEqual(by_rule(lint("allow.yaml"), "hardcoded-color"), [])

    def test_card_mod_on_tile_is_error(self):
        found = by_rule(lint("bad.yaml"), "card-mod-not-allowed")
        self.assertEqual([(f.severity, f.where) for f in found], [("error", "/views/0/sections/0/cards/1")])

    def test_card_mod_on_tier_d_is_warning(self):
        found = by_rule(lint("bad.yaml"), "card-mod-used")
        self.assertEqual([(f.severity, f.where) for f in found], [("warning", "/views/0/sections/0/cards/2")])

    def test_view_missing_path(self):
        found = by_rule(lint("bad.yaml"), "view-missing-path")
        self.assertEqual([(f.severity, f.where) for f in found], [("warning", "/views/1")])

    def test_duplicated_template(self):
        found = by_rule(lint("bad.yaml"), "duplicated-template")
        self.assertEqual(len(found), 1)
        self.assertIn("/views/0/sections/0/cards/3/primary", found[0].where)
        self.assertIn("/views/0/sections/0/cards/4/primary", found[0].where)

    def test_template_only_file_is_clean(self):
        path = os.path.join(FIX, "templates_only.yaml")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# Fixture: templates file\nwn_base:\n  section_mode: true\n")
        try:
            self.assertEqual(ld.lint_file(path, ALLOWLIST), [])
        finally:
            os.remove(path)

    def test_cli_exit_codes(self):
        allow = os.path.join(REPO, ".claude", "reference", "installed-cards.yaml")
        self.assertEqual(ld.main(["--allowlist", allow, os.path.join(FIX, "good.yaml")]), 0)
        self.assertEqual(ld.main(["--allowlist", allow, os.path.join(FIX, "bad.yaml")]), 1)

    def test_allowlist_covers_catalogue(self):
        with open(os.path.join(REPO, ".claude", "reference", "dashboard-catalog.md"), encoding="utf-8") as fh:
            rows = [line for line in fh if line.startswith("|")]
        types = set(re.findall(r"custom:[\w*-]+", "".join(rows)))
        globs = [entry["type"] for entry in ALLOWLIST]
        missing = sorted(t for t in types if not any(fnmatch.fnmatchcase(t, g) for g in globs))
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
