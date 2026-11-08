#!/usr/bin/env python3
"""Tests for plan_tests.py.

Run from the repo root:

    python3 .github/scripts/test_plan_tests.py
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import plan_tests  # noqa: E402


class TestDataOnlyAddons(unittest.TestCase):
    def test_addon_without_init_is_left_out(self):
        # manifestoo does not see an addon without __init__.py; passing it in
        # INCLUDE would abort the test job.
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            for name, with_init in (("deltatech_python_addon", True), ("deltatech_data_only", False)):
                os.mkdir(os.path.join(tmp, name))
                with open(os.path.join(tmp, name, "__manifest__.py"), "w", encoding="utf-8") as handle:
                    handle.write("{'depends': ['web']}")
                if with_init:
                    open(os.path.join(tmp, name, "__init__.py"), "w", encoding="utf-8").close()
            os.chdir(tmp)
            try:
                manifests = plan_tests.load_manifests()
            finally:
                os.chdir(cwd)
        self.assertEqual(set(manifests), {"deltatech_python_addon"})


if __name__ == "__main__":
    unittest.main()
