# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAnalyticEnforce(AccountTestInvoicingCommon):
    """ANALYTICENFORCE-001: posting several moves at once validates each move separately."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.analytic_distribution_validation_enabled = True
        accounts = cls.env["account.analytic.account"]
        for name in ("Location", "Department", "Line of Business"):
            plan = cls.env["account.analytic.plan"].create({"name": f"Enforce {name}"})
            accounts |= cls.env["account.analytic.account"].create({"name": f"Enforce {name} 1", "plan_id": plan.id})
        cls.valid_distribution = {",".join(str(account_id) for account_id in accounts.ids): 100}

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
