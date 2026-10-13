# © 2026 Deltatech
# See README.rst file on addons root folder for license details

import os
import tempfile
from unittest.mock import patch

from odoo import modules
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLineCounter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = cls.env["ir.module.module"].search([("name", "=", "deltatech_line_counter")], limit=1)

    def test_line_counter_wizard(self):
        wizard = self.env["line.counter.wizard"].create({"module_ids": [(6, 0, self.module.ids)]})
        wizard.action_count_lines()
        self.assertTrue(wizard.result)
        self.assertIn("deltatech_line_counter", wizard.result)
        self.assertIn("Total", wizard.result)

    def test_counts_non_empty_lines_and_skips_tests_and_unreadable(self):
        with tempfile.TemporaryDirectory() as path:
            os.makedirs(os.path.join(path, "tests"))
            with open(os.path.join(path, "a.py"), "w", encoding="utf-8") as f:
                f.write("x = 1\n\n    \ny = 2\n")
            with open(os.path.join(path, "b.xml"), "w", encoding="utf-8") as f:
                f.write("<odoo/>\n")
            with open(os.path.join(path, "tests", "skipped.py"), "w", encoding="utf-8") as f:
                f.write("a = 1\nb = 2\n")
            with open(os.path.join(path, "bad.js"), "wb") as f:
                f.write(b"\xff\xfe\x00 not utf-8\n")
            with open(os.path.join(path, "notes.txt"), "w", encoding="utf-8") as f:
                f.write("not counted\n")
            wizard = self.env["line.counter.wizard"].create({"module_ids": [(6, 0, self.module.ids)]})
            with patch.object(modules, "get_module_path", return_value=path):
                wizard.action_count_lines()
        # a.py: 2 + b.xml: 1; tests/ and the unreadable file do not count
        self.assertIn("<td>3</td>", wizard.result)
        self.assertIn("<th>3</th>", wizard.result)

    def test_module_label_is_escaped(self):
        self.module.sudo().shortdesc = "<script>alert(1)</script>"
        wizard = self.env["line.counter.wizard"].create({"module_ids": [(6, 0, self.module.ids)]})
        wizard.action_count_lines()
        self.assertNotIn("<script>", wizard.result)
        self.assertIn("&lt;script&gt;", wizard.result)
