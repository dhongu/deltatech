# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPaymentReport(TransactionCase):
    """PAYREPORT-001: the report must include the Odoo 20 posted payment states."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.journal = cls.env["account.journal"].create(
            {"name": "Payment report bank", "code": "PRBNK", "type": "bank", "company_id": cls.company.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Payment report customer"})
        cls.today = fields.Date.today()

    def _payment(self, amount, state):
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner.id,
                "amount": amount,
                "date": self.today,
                "journal_id": self.journal.id,
            }
        )
        if state != "draft":
            payment.action_post()
        if state == "reconciled":
            payment.action_validate()
        elif state == "canceled":
            payment.action_cancel()
        elif state == "rejected":
            payment.action_reject()
        self.assertEqual(payment.state, state)
        return payment

    def test_report_includes_only_valid_payments(self):
        self._payment(100, "paid")
        self._payment(200, "reconciled")
        self._payment(300, "draft")
        self._payment(400, "canceled")
        self._payment(500, "rejected")
        report = self.env["account.payment.report"].create(
            {
                "date_from": self.today,
                "date_to": self.today,
                "company_id": self.company.id,
                "journal_payment_ids": [(6, 0, self.journal.ids)],
            }
        )
        action = report.button_show_report()
        lines = self.env["account.payment.report.line"].search(action["domain"])
        self.assertEqual(sorted(lines.mapped("amount")), [100.0, 200.0])
        self.assertEqual(lines.partner_id, self.partner)

    def test_card_payment_method_information(self):
        info = self.env["account.payment.method"]._get_payment_method_information()
        self.assertEqual(info["card"], {"mode": "unique", "type": ("bank",)})
        domain = self.env["account.payment.method"]._get_payment_method_domain("card")
        self.assertIn(self.journal, self.env["account.journal"].search(domain))
        cash = self.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", self.company.id)], limit=1
        )
        if cash:
            self.assertNotIn(cash, self.env["account.journal"].search(domain))

    def test_default_journals(self):
        report = self.env["account.payment.report"].create({})
        self.assertIn(self.journal, report.journal_payment_ids)
        self.assertTrue(all(j.type in ("cash", "bank") for j in report.journal_payment_ids))
