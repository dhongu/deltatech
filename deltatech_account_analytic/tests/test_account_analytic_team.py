# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountAnalyticTeam(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_team = cls.env["crm.team"].sudo().create({"name": "Test Team"})
        # Some installs (e.g. l10n_ro_efactura_enhancement) refuse to post out_invoice/out_refund
        # for a partner without a country, so give the test partner one regardless of the install.
        cls.partner_a.write({"country_id": cls.env.ref("base.us").id})
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

    def test_entry_analytic_line_no_team_id(self):
        """A manual journal entry is not team-based: its analytic line must not get team_id."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "team_id": self.sale_team.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.company_data["default_account_revenue"].id,
                            "analytic_distribution": {str(self.analytic_account.id): 100},
                            "debit": 0.0,
                            "credit": 100.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.company_data["default_account_expense"].id,
                            "debit": 100.0,
                            "credit": 0.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        analytic_lines = self.env["account.analytic.line"].search([("move_line_id.move_id", "=", move.id)])
        self.assertTrue(analytic_lines)
        self.assertFalse(analytic_lines.team_id)

    def test_vendor_bill_additional_plan_only(self):
        """ANALYTICSPLIT-004: a vendor distribution only on an additional plan has no account_id"""
        project_plan, _other_plans = self.env["account.analytic.plan"]._get_all_plans()
        extra_plan = self.env["account.analytic.plan"].create({"name": "Extra Plan"})
        self.assertNotEqual(extra_plan, project_plan)
        extra_account = self.env["account.analytic.account"].create({"name": "Test Team", "plan_id": extra_plan.id})
        bill = self._create_invoice(
            move_type="in_invoice",
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    analytic_distribution={str(extra_account.id): 100},
                ),
            ],
        )
        bill.action_post()
        analytic_lines = self.env["account.analytic.line"].search([("move_line_id.move_id", "=", bill.id)])
        self.assertEqual(analytic_lines[extra_plan._column_name()], extra_account)
