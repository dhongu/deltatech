from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestGenericPartnerInvoiceBlock(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Some RO localization modules refuse to post an invoice whose partner
        # has no country/state, so the test partners are fully addressed.
        cls.country = cls.env.ref("base.ro")
        cls.state = cls.env["res.country.state"].search([("country_id", "=", cls.country.id)], limit=1)
        cls.address = {
            "country_id": cls.country.id,
            "state_id": cls.state.id,
            "city": "Cluj-Napoca",
            "street": "Str. Test 1",
        }
        cls.generic_partner = cls.env["res.partner"].create(
            {"name": "Generic customer", "is_company": True, **cls.address}
        )
        cls.generic_child = cls.env["res.partner"].create(
            {"name": "Generic delivery address", "parent_id": cls.generic_partner.id, **cls.address}
        )
        cls.partner_a.write(cls.address)
        cls.env.company.generic_partner_id = cls.generic_partner

    def _new_invoice(self, partner, move_type="out_invoice"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": "2026-01-15",
                "invoice_line_ids": [(0, 0, {"name": "Line", "quantity": 1, "price_unit": 100})],
            }
        )

    def test_customer_invoice_on_generic_partner_is_blocked(self):
        invoice = self._new_invoice(self.generic_partner)
        with self.assertRaises(UserError):
            invoice.action_post()
        self.assertEqual(invoice.state, "draft")

    def test_credit_note_on_generic_partner_is_blocked(self):
        invoice = self._new_invoice(self.generic_partner, move_type="out_refund")
        with self.assertRaises(UserError):
            invoice.action_post()
        self.assertEqual(invoice.state, "draft")

    def test_child_of_generic_partner_is_blocked(self):
        """An address under the generic partner is the same commercial entity."""
        invoice = self._new_invoice(self.generic_child)
        with self.assertRaises(UserError):
            invoice.action_post()
        self.assertEqual(invoice.state, "draft")

    def test_draft_on_generic_partner_stays_allowed(self):
        """POS and e-commerce flows must keep creating drafts."""
        invoice = self._new_invoice(self.generic_partner)
        self.assertEqual(invoice.state, "draft")

    def test_regular_customer_invoice_is_posted(self):
        invoice = self._new_invoice(self.partner_a)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_vendor_bill_on_generic_partner_is_allowed(self):
        invoice = self._new_invoice(self.generic_partner, move_type="in_invoice")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_no_generic_partner_configured_changes_nothing(self):
        self.env.company.generic_partner_id = False
        invoice = self._new_invoice(self.generic_partner)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_generic_partner_of_another_company_is_not_blocked(self):
        """Only the generic partner of the invoice's own company is protected."""
        other_company = self.env["res.company"].create({"name": "Other company"})
        other_company.generic_partner_id = self.partner_a
        invoice = self._new_invoice(self.partner_a)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
