# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentDefault(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("base.group_partner_manager") | cls.env.ref(
            "account.group_account_invoice"
        )
        cls.bank_journal_2 = cls.env["account.journal"].create(
            {"name": "Second Bank", "code": "BNK2", "type": "bank", "company_id": cls.company_data["company"].id}
        )
        cls.in_line_2 = cls.bank_journal_2.inbound_payment_method_line_ids[:1]
        cls.out_line_2 = cls.bank_journal_2.outbound_payment_method_line_ids[:1]

    def _register(self, moves, **vals):
        return (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=moves.ids)
            .create(vals)
        )

    def test_set_default_inbound(self):
        invoice = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[100.0], post=True)
        wizard = self._register(invoice)
        self.assertTrue(wizard.can_set_as_default)
        wizard.write(
            {"journal_id": self.bank_journal_2.id, "payment_method_line_id": self.in_line_2.id, "set_as_default": True}
        )
        wizard.action_create_payments()
        partner = self.partner_a.with_company(self.company_data["company"])
        self.assertEqual(partner.property_inbound_payment_method_line_id, self.in_line_2)
        self.assertFalse(partner.property_outbound_payment_method_line_id)
        self.assertIn("Second Bank", partner.message_ids[:1].body)

        # a new invoice gets the default, the wizard proposes it
        invoice_2 = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[50.0], post=True)
        self.assertEqual(invoice_2.preferred_payment_method_line_id, self.in_line_2)
        wizard_2 = self._register(invoice_2)
        self.assertEqual(wizard_2.journal_id, self.bank_journal_2)
        self.assertEqual(wizard_2.payment_method_line_id, self.in_line_2)

    def test_set_default_outbound(self):
        bill = self.init_invoice("in_invoice", partner=self.partner_a, amounts=[100.0], post=True)
        wizard = self._register(bill)
        wizard.write(
            {"journal_id": self.bank_journal_2.id, "payment_method_line_id": self.out_line_2.id, "set_as_default": True}
        )
        wizard.action_create_payments()
        partner = self.partner_a.with_company(self.company_data["company"])
        self.assertEqual(partner.property_outbound_payment_method_line_id, self.out_line_2)
        self.assertFalse(partner.property_inbound_payment_method_line_id)

    def test_unchecked_no_write(self):
        invoice = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[100.0], post=True)
        wizard = self._register(invoice)
        wizard.write({"journal_id": self.bank_journal_2.id, "payment_method_line_id": self.in_line_2.id})
        wizard.action_create_payments()
        self.assertFalse(
            self.partner_a.with_company(self.company_data["company"]).property_inbound_payment_method_line_id
        )

    def test_fallback_open_invoice(self):
        # invoice created before the default was set: no preferred method on it
        invoice = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[100.0], post=True)
        self.assertFalse(invoice.preferred_payment_method_line_id)
        self.partner_a.with_company(
            self.company_data["company"]
        ).property_inbound_payment_method_line_id = self.in_line_2
        wizard = self._register(invoice)
        self.assertEqual(wizard.journal_id, self.bank_journal_2)
        self.assertEqual(wizard.payment_method_line_id, self.in_line_2)

    def test_explicit_preferred_wins(self):
        self.partner_a.with_company(
            self.company_data["company"]
        ).property_inbound_payment_method_line_id = self.in_line_2
        invoice = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[100.0])
        invoice.preferred_payment_method_line_id = self.inbound_payment_method_line
        invoice.action_post()
        wizard = self._register(invoice)
        self.assertEqual(wizard.payment_method_line_id, self.inbound_payment_method_line)

    def test_contact_uses_commercial_partner(self):
        company_partner = self.env["res.partner"].create({"name": "Company Partner", "is_company": True})
        contact = self.env["res.partner"].create({"name": "Contact", "parent_id": company_partner.id})
        company_partner.with_company(
            self.company_data["company"]
        ).property_inbound_payment_method_line_id = self.in_line_2
        invoice = self.init_invoice("out_invoice", partner=contact, amounts=[100.0], post=True)
        self.assertEqual(invoice.preferred_payment_method_line_id, self.in_line_2)

        wizard = self._register(invoice)
        wizard.journal_id = self.inbound_payment_method_line.journal_id
        wizard.write({"payment_method_line_id": self.inbound_payment_method_line.id, "set_as_default": True})
        wizard.action_create_payments()
        self.assertEqual(
            company_partner.with_company(self.company_data["company"]).property_inbound_payment_method_line_id,
            self.inbound_payment_method_line,
        )
        self.assertFalse(contact.with_company(self.company_data["company"]).property_inbound_payment_method_line_id)

    def test_hidden_for_several_partners(self):
        invoice_a = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[100.0], post=True)
        invoice_b = self.init_invoice("out_invoice", partner=self.partner_b, amounts=[100.0], post=True)
        wizard = self._register(invoice_a + invoice_b, set_as_default=True)
        self.assertFalse(wizard.can_set_as_default)
        wizard.action_create_payments()
        for partner in self.partner_a | self.partner_b:
            self.assertFalse(partner.with_company(self.company_data["company"]).property_inbound_payment_method_line_id)

    def test_hidden_without_contact_creation(self):
        user = self.env["res.users"].create(
            {
                "name": "Billing only",
                "login": "billing_only_payment_default",
                "company_id": self.company_data["company"].id,
                "company_ids": [Command.set(self.company_data["company"].ids)],
                "group_ids": [Command.set([self.env.ref("account.group_account_invoice").id])],
            }
        )
        self.assertFalse(user.has_group("base.group_partner_manager"))
        invoice = self.init_invoice("out_invoice", partner=self.partner_a, amounts=[100.0], post=True)
        wizard = self._register(invoice).with_user(user)
        wizard.invalidate_recordset(["can_set_as_default"])
        self.assertFalse(wizard.can_set_as_default)
