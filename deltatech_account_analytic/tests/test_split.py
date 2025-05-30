# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details


from odoo import fields
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
