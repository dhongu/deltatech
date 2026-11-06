from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestGenericPartnerPaymentRegister(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generic_partner = cls.env["res.partner"].create({"name": "Generic supplier", "is_company": True})
        cls.env.company.generic_partner_id = cls.generic_partner
        cls.restricted_journal = cls.company_data["default_journal_bank"]
        cls.restricted_journal.restriction = True
        cls.allowed_journal = cls.company_data["default_journal_cash"]

    def _posted_bill(self, partner, preferred_journal=None):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": partner.id,
                "invoice_date": "2026-01-15",
                "invoice_line_ids": [Command.create({"name": "Line", "quantity": 1, "price_unit": 100})],
            }
        )
        if preferred_journal:
            bill.preferred_payment_method_line_id = preferred_journal.outbound_payment_method_line_ids[:1]
        bill.action_post()
        return bill

    def _register(self, bill):
        return (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=bill.ids)
            .create({})
        )

    def test_restricted_journal_is_hidden_for_generic_partner(self):
        wizard = self._register(self._posted_bill(self.generic_partner))

        self.assertNotIn(self.restricted_journal, wizard.available_journal_ids._origin)
        self.assertEqual(wizard.journal_id._origin, self.allowed_journal)

    def test_restricted_journal_is_available_for_regular_partner(self):
        wizard = self._register(self._posted_bill(self.partner_a))

        self.assertIn(self.restricted_journal, wizard.available_journal_ids._origin)
        self.assertEqual(wizard.journal_id._origin, self.restricted_journal)

    def test_preferred_restricted_journal_is_replaced_for_generic_partner(self):
        bill = self._posted_bill(self.generic_partner, preferred_journal=self.restricted_journal)
        self.assertEqual(bill.preferred_payment_method_line_id.journal_id, self.restricted_journal)

        wizard = self._register(bill)

        self.assertEqual(wizard.journal_id._origin, self.allowed_journal)
