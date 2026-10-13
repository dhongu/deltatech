# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAnalyticEnforce(AccountTestInvoicingCommon):
    """ANALYTICENFORCE-001: posting several moves at once validates each move separately.
    ANALYTICENFORCE-002: the switch is read from the company of the bill, not from the current company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.analytic_distribution_validation_enabled = True
        accounts = cls.env["account.analytic.account"]
        for name in ("Location", "Department", "Line of Business"):
            plan = cls.env["account.analytic.plan"].create({"name": f"Enforce {name}"})
            accounts |= cls.env["account.analytic.account"].create(
                {"name": f"Enforce {name} 1", "plan_id": plan.id, "company_id": False}
            )
        cls.valid_distribution = {",".join(str(account_id) for account_id in accounts.ids): 100}
        cls.company_data_2 = cls.setup_other_company()
        cls.company_2 = cls.company_data_2["company"]

    def _bill(self, distribution, move_type="in_invoice"):
        return self._create_invoice(
            move_type=move_type,
            invoice_line_ids=[self._prepare_invoice_line(price_unit=100, analytic_distribution=distribution)],
        )

    def test_post_multiple_valid_bills(self):
        bills = self._bill(self.valid_distribution) | self._bill(self.valid_distribution, "in_refund")
        bills.action_post()
        self.assertEqual(set(bills.mapped("state")), {"posted"})

    def test_post_multiple_bills_one_invalid(self):
        valid_bill = self._bill(self.valid_distribution)
        invalid_bill = self._bill(False)
        with self.assertRaises(ValidationError):
            (valid_bill | invalid_bill).action_post()

    def test_post_mixed_document_types(self):
        customer_invoice = self._create_invoice(
            move_type="out_invoice", invoice_line_ids=[self._prepare_invoice_line(price_unit=100)]
        )
        bill = self._bill(self.valid_distribution)
        (customer_invoice | bill).action_post()
        self.assertEqual(customer_invoice.state, "posted")
        self.assertEqual(bill.state, "posted")

    def test_post_single_invalid_bill(self):
        with self.assertRaises(ValidationError):
            self._bill({"1": 100}).action_post()

    def test_validation_disabled(self):
        self.env.company.analytic_distribution_validation_enabled = False
        bills = self._bill(False) | self._bill(False)
        bills.action_post()
        self.assertEqual(set(bills.mapped("state")), {"posted"})

    def _bill_company_2(self, distribution):
        """Draft vendor bill of company 2, created while company 1 stays the current company."""
        return self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company_2.id,
                "journal_id": self.company_data_2["default_journal_purchase"].id,
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-01-01",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Line",
                            "quantity": 1,
                            "price_unit": 100,
                            "account_id": self.company_data_2["default_account_expense"].id,
                            "tax_ids": [Command.clear()],
                            "analytic_distribution": distribution,
                        }
                    )
                ],
            }
        )

    def _env_current_company_1(self):
        return self.env(context=dict(self.env.context, allowed_company_ids=[self.env.company.id, self.company_2.id]))

    def test_bill_company_enabled_current_company_disabled(self):
        """An invalid bill of a company with the validation enabled is blocked even if the current company has it off."""
        self.env.company.analytic_distribution_validation_enabled = False
        self.company_2.analytic_distribution_validation_enabled = True
        bill = self._bill_company_2(False)
        env = self._env_current_company_1()
        self.assertEqual(env.company, self.env.company)
        with self.assertRaises(ValidationError):
            bill.with_env(env).action_post()

    def test_bill_company_disabled_current_company_enabled(self):
        """The policy of the current company is not applied to bills of another company."""
        self.env.company.analytic_distribution_validation_enabled = True
        self.company_2.analytic_distribution_validation_enabled = False
        bill = self._bill_company_2(False)
        bill.with_env(self._env_current_company_1()).action_post()
        self.assertEqual(bill.state, "posted")

    def test_mixed_company_batch(self):
        """In a batch, each bill is checked against the switch of its own company."""
        self.env.company.analytic_distribution_validation_enabled = False
        self.company_2.analytic_distribution_validation_enabled = True
        bill_1 = self._bill(False)
        bill_2 = self._bill_company_2(self.valid_distribution)
        (bill_1 | bill_2).with_env(self._env_current_company_1()).action_post()
        self.assertEqual((bill_1 | bill_2).mapped("state"), ["posted", "posted"])
        bill_3 = self._bill(False)
        bill_4 = self._bill_company_2(False)
        with self.assertRaises(ValidationError):
            (bill_3 | bill_4).with_env(self._env_current_company_1()).action_post()
