# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSplit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.analytic_plan = self.env["account.analytic.plan"].create(
            {"name": "Plan1", "default_applicability": "optional"}
        )
        self.analytic1 = self.env["account.analytic.account"].create(
            {"name": "Analytic1", "plan_id": self.analytic_plan.id}
        )
        self.analytic2 = self.env["account.analytic.account"].create(
            {"name": "Analytic2", "plan_id": self.analytic_plan.id}
        )

        self.split_template = self.env["account.analytic.split.template"].create(
            {
                "name": "test_split",
                "line_ids": [
                    (0, 0, {"analytic_id": self.analytic1.id, "percent": 60}),
                    (0, 0, {"analytic_id": self.analytic2.id, "percent": 40}),
                ],
            }
        )

    def test_split_amount(self):
        new_split = self.env["account.analytic.split"].create(
            {
                "name": "test_split",
                "date": fields.Date.today(),
                "split_template_id": self.split_template.id,
                "split_type": "amount",
                "amount": 100,
            }
        )
        new_split.action_prepare_lines()
        new_split.action_create_analytic_lines()
        line1 = self.env["account.analytic.line"].search(
            [("date", "=", fields.Date.today()), ("account_id", "=", self.analytic1.id)]
        )
        line2 = self.env["account.analytic.line"].search(
            [("date", "=", fields.Date.today()), ("account_id", "=", self.analytic2.id)]
        )
        self.assertEqual(line1.amount, 60)
        self.assertEqual(line2.amount, 40)

    def _amount_split(self, amount=100):
        return self.env["account.analytic.split"].create(
            {
                "name": "test_split",
                "split_template_id": self.split_template.id,
                "split_type": "amount",
                "amount": amount,
            }
        )

    def _line_split(self):
        source = self.env["account.analytic.line"].create(
            {"name": "Source", "account_id": self.analytic1.id, "amount": -200}
        )
        split = self.env["account.analytic.split"].create(
            {
                "name": "line_split",
                "split_template_id": self.split_template.id,
                "split_type": "line",
                "line_to_split": source.id,
            }
        )
        return split, source

    def test_confirm_line_split_without_lines_keeps_source(self):
        """ANALYTICSPLIT-001: Confirm before Compute must not delete the source line"""
        split, source = self._line_split()
        with self.assertRaises(UserError):
            split.action_create_analytic_lines()
        self.assertTrue(source.exists())
        self.assertEqual(split.state, "draft")

    def test_line_split_replaces_source(self):
        split, source = self._line_split()
        split.action_prepare_lines()
        lines = split.action_create_analytic_lines()
        self.assertFalse(source.exists())
        self.assertEqual(sorted(lines.mapped("amount")), [-120, -80])

    def test_confirm_with_changed_amounts_refused(self):
        split, source = self._line_split()
        split.action_prepare_lines()
        split.line_ids[0].amount = -50
        with self.assertRaises(UserError):
            split.action_create_analytic_lines()
        self.assertTrue(source.exists())

    def test_confirm_twice_does_not_duplicate(self):
        """ANALYTICSPLIT-002: a second confirmation creates no further entries"""
        split = self._amount_split()
        split.action_prepare_lines()
        lines = split.action_create_analytic_lines()
        with self.assertRaises(UserError):
            split.action_create_analytic_lines()
        self.assertEqual(split.line_ids.analytic_line_id, lines)
        self.assertEqual(
            self.env["account.analytic.line"].search_count([("name", "=", "test_split")]),
            2,
        )
        split.action_reset_split()
        self.assertFalse(lines.exists())
