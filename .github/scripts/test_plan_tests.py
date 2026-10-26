#!/usr/bin/env python3
"""Tests for the shard split of plan_tests.py.

Run from the repo root:

    python3 .github/scripts/test_plan_tests.py

The manifests are synthetic; addon names follow the prefixes of `group_of`, so
every addon lands in the family (hence the shard) the test wants.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import plan_tests  # noqa: E402


def shard_of(shards, module):
    return next(shard["name"] for shard in shards if module in shard["modules"].split(","))


def caught_anywhere(manifests, shards):
    return {
        module
        for shard in shards
        for module in plan_tests.preinstalled(manifests, set(shard["modules"].split(",")))
    }


class TestColocatePreinstalled(unittest.TestCase):
    # `partner_generic` (family misc) is required by `account_partner` (family
    # account), itself required by `misc_report` (misc): the misc shard installs
    # `account_partner` at init, and with it `partner_generic`.
    MANIFESTS = {
        "deltatech_partner_generic": {"depends": ["account"]},
        "deltatech_account_partner": {"depends": ["deltatech_partner_generic"]},
        "deltatech_misc_report": {"depends": ["deltatech_partner_generic", "deltatech_account_partner"]},
        "deltatech_account_other": {"depends": ["account"]},
    }

    def test_preinstalled_detects_addon_pulled_in_by_other_shard(self):
        caught = plan_tests.preinstalled(self.MANIFESTS, {"deltatech_partner_generic", "deltatech_misc_report"})
        self.assertEqual(caught, {"deltatech_partner_generic": ["deltatech_account_partner"]})

    def test_without_manifests_matrix_is_unchanged(self):
        shards = plan_tests.build_matrix(set(self.MANIFESTS))
        self.assertEqual(shard_of(shards, "deltatech_partner_generic"), "misc")
        self.assertIn("deltatech_partner_generic", caught_anywhere(self.MANIFESTS, shards))

    def test_addon_moves_next_to_intermediary(self):
        shards = plan_tests.build_matrix(set(self.MANIFESTS), self.MANIFESTS)
        self.assertEqual(shard_of(shards, "deltatech_partner_generic"), "account")
        self.assertEqual(caught_anywhere(self.MANIFESTS, shards), set())
        # Nothing lost, nothing duplicated.
        listed = [module for shard in shards for module in shard["modules"].split(",")]
        self.assertCountEqual(listed, self.MANIFESTS)

    def test_intermediary_outside_selection_joins_the_shard(self):
        # Targeted manual run: `account_partner` is not selected but is installed
        # at init; it joins the shard so that `partner_generic` runs its tests.
        selection = {"deltatech_partner_generic", "deltatech_misc_report"}
        shards = plan_tests.build_matrix(selection, self.MANIFESTS)
        self.assertEqual(len(shards), 1)
        self.assertEqual(
            set(shards[0]["modules"].split(",")),
            selection | {"deltatech_account_partner"},
        )

    def test_excludes_blocks_the_move(self):
        manifests = {
            "deltatech_stock_fifo": {"depends": ["deltatech_stock_base"]},
            "deltatech_stock_base": {"depends": ["stock"]},
            "deltatech_stock_cmp": {"depends": ["deltatech_stock_base"], "excludes": ["deltatech_stock_fifo"]},
            "deltatech_stock_report": {"depends": ["deltatech_stock_fifo"]},
        }
        # FIFO is not selected, but `stock_report` requires it, so it is installed
        # at init and pulls in `stock_base`. It would have to join the stock
        # shard, next to CMP which excludes it: the move is refused and planning ends.
        selection = {"deltatech_stock_base", "deltatech_stock_cmp", "deltatech_stock_report"}
        shards = plan_tests.build_matrix(selection, manifests)
        self.assertEqual(shards, [{"name": "stock", "modules": ",".join(sorted(selection))}])
        self.assertTrue(plan_tests.excludes_conflict(manifests, "deltatech_stock_fifo", {"deltatech_stock_cmp"}))
        self.assertFalse(plan_tests.excludes_conflict(manifests, "deltatech_stock_base", {"deltatech_stock_cmp"}))

    def test_real_repo_has_no_preinstalled_addon(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cwd = os.getcwd()
        os.chdir(root)
        try:
            manifests = plan_tests.load_manifests()
        finally:
            os.chdir(cwd)
        shards = plan_tests.build_matrix(set(manifests), manifests)
        self.assertEqual(caught_anywhere(manifests, shards), set())


class TestNeutralRootFiles(unittest.TestCase):
    def test_lint_configs_are_neutral(self):
        for path in (".pre-commit-config.yaml", ".ruff.toml", ".pylintrc-mandatory", ".editorconfig"):
            self.assertTrue(plan_tests.is_neutral(path), path)

    def test_only_at_repo_root(self):
        self.assertFalse(plan_tests.is_neutral("deltatech/.pre-commit-config.yaml"))

    def test_test_inputs_still_force_a_full_run(self):
        for path in (".github/workflows/test.yml", "requirements.txt", ".gitattributes"):
            self.assertFalse(plan_tests.is_neutral(path), path)


if __name__ == "__main__":
    unittest.main()
