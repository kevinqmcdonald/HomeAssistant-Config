"""Tests for render_dashboard.py."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import render_dashboard as rd  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "render")


def fx(name):
    return os.path.join(FIX, name)


class RenderDashboardTest(unittest.TestCase):
    def test_plain_include(self):
        cfg = rd.load_dashboard(fx("main.yaml"))
        self.assertEqual(cfg["button_card_templates"], {"wn_base": {"section_mode": True}})

    def test_nested_include_resolves_relative_to_including_file(self):
        cfg = rd.load_dashboard(fx("main.yaml"))
        self.assertEqual(cfg["views"][0]["cards"][0]["type"], "custom:clock-weather-card")

    def test_include_dir_merge_named(self):
        cfg = rd.load_dashboard(fx("dir_merge.yaml"))
        self.assertEqual(cfg["merged"], {"alpha": {"value": 1}, "beta": {"value": 2}})

    def test_include_dir_list_sorted(self):
        cfg = rd.load_dashboard(fx("dir_merge.yaml"))
        self.assertEqual(cfg["listed"], [{"alpha": {"value": 1}}, {"beta": {"value": 2}}])

    def test_dir_includes_recurse_like_ha(self):
        with tempfile.TemporaryDirectory() as tmp:
            views = os.path.join(tmp, "views", "home")
            os.makedirs(views)
            os.makedirs(os.path.join(tmp, "views", ".hidden"))
            with open(os.path.join(views, "main.yaml"), "w", encoding="utf-8") as fh:
                fh.write("- title: Main\n  path: main\n")
            with open(os.path.join(tmp, "views", ".hidden", "x.yaml"), "w", encoding="utf-8") as fh:
                fh.write("- title: Hidden\n")
            with open(os.path.join(views, "notes.yml"), "w", encoding="utf-8") as fh:
                fh.write("- title: Yml\n")
            root = os.path.join(tmp, "dash.yaml")
            with open(root, "w", encoding="utf-8") as fh:
                fh.write("views: !include_dir_merge_list views\n")
            cfg = rd.load_dashboard(root)
        self.assertEqual([v["title"] for v in cfg["views"]], ["Main"])

    def test_secret_raises(self):
        with self.assertRaises(rd.DashboardLoadError) as ctx:
            rd.load_dashboard(fx("secret.yaml"))
        self.assertIn("!secret", str(ctx.exception))

    def test_missing_include_raises(self):
        with self.assertRaises(rd.DashboardLoadError) as ctx:
            rd.load_dashboard(fx("missing.yaml"))
        self.assertIn("nope.yaml", str(ctx.exception))

    def test_files_list_includes_every_loaded_file(self):
        _, files = rd.load_dashboard_with_files(fx("main.yaml"))
        names = sorted(os.path.basename(f) for f in files)
        self.assertEqual(names, ["button_card_templates.yaml", "clock.yaml", "home.yaml", "main.yaml"])

    def test_theme_flag_sets_only_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.json")
            self.assertEqual(rd.main([fx("main.yaml"), "--theme", "Walnut", "--out", out]), 0)
            with open(out, encoding="utf-8") as fh:
                cfg = json.load(fh)
        self.assertEqual(cfg["views"][0]["theme"], "Walnut")
        self.assertEqual(cfg["views"][1]["theme"], "Other")

    def test_cli_exit_code_on_error(self):
        self.assertEqual(rd.main([fx("secret.yaml")]), 2)


if __name__ == "__main__":
    unittest.main()
