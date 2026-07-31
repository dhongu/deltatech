# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountAnalyticTeam(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_team = cls.env["crm.team"].sudo().create({"name": "Test Team"})
        cls.analytic_plan = cls.env["account.analytic.plan"].create({"name": "Test Plan"})
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "Test Analytic Account", "plan_id": cls.analytic_plan.id}
        )

    def _post_invoice_with_team(self, move_type):
        invoice = self._create_invoice(
            move_type=move_type,
            team_id=self.sale_team.id,
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    analytic_distribution={str(self.analytic_account.id): 100},
                ),
            ],
        )
        invoice.action_post()
        return self.env["account.analytic.line"].search([("move_line_id.move_id", "=", invoice.id)])

    def test_out_invoice_analytic_line_team_id(self):
        analytic_lines = self._post_invoice_with_team("out_invoice")
        self.assertTrue(analytic_lines)
        self.assertEqual(analytic_lines.team_id, self.sale_team)

    def test_out_receipt_analytic_line_team_id(self):
        """Analytic lines generated from out_receipt must get team_id, same as out_invoice."""
        analytic_lines = self._post_invoice_with_team("out_receipt")
        self.assertTrue(analytic_lines)
        self.assertEqual(analytic_lines.team_id, self.sale_team)
