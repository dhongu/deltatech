# © 2026 Deltatech
# See README.rst file on addons root folder for license details

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

    def test_line_counter_no_modules(self):
        wizard = self.env["line.counter.wizard"].create({})
        action = wizard.action_count_lines()
        self.assertEqual(action["res_model"], "line.counter.wizard")
        self.assertEqual(action["res_id"], wizard.id)
        self.assertIn("<th>0</th>", wizard.result)

    def test_line_counter_access(self):
        user = self.env["res.users"].create(
            {
                "name": "Line Counter User",
                "login": "line_counter_user",
                "group_ids": [(6, 0, self.env.ref("base.group_user").ids)],
            }
        )
        model = self.env["line.counter.wizard"].with_user(user)
        self.assertFalse(model.has_access("create"))
        self.assertTrue(self.env["line.counter.wizard"].has_access("create"))
