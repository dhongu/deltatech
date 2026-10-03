from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPackagingCompanyAccess(AccountTestInvoicingCommon):
    """PACKMAT-003: the invoice packaging lines follow the invoice company and changing
    them needs write access on the invoice, whatever the context."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company_data["company"]
        cls.company_b = cls.setup_other_company()["company"]
        cls.invoice_a = cls._create_packaging_invoice(cls.company_a)
        cls.invoice_b = cls._create_packaging_invoice(cls.company_b)
        cls.line_a = cls.invoice_a.packaging_material_ids
        cls.line_b = cls.invoice_b.packaging_material_ids
        cls.billing_a = new_test_user(
            cls.env,
            login="packmat003_billing_a",
            groups="base.group_user,account.group_account_invoice",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.internal_a = new_test_user(
            cls.env,
            login="packmat003_internal_a",
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    @classmethod
    def _create_packaging_invoice(cls, company):
        invoice = (
            cls.env["account.move"]
            .with_company(company)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": cls.partner_a.id,
                    "invoice_date": fields.Date.today(),
                    "company_id": company.id,
                    "invoice_line_ids": [Command.create({"name": "PACKMAT-003", "quantity": 1.0, "price_unit": 10.0})],
                }
            )
        )
        cls.env["packaging.invoice.material"].create({"invoice_id": invoice.id, "material_type": "paper", "qty": 2.0})
        return invoice

    def test_search_follows_invoice_company(self):
        lines = self.env["packaging.invoice.material"].with_user(self.billing_a).search([])
        self.assertIn(self.line_a, lines)
        self.assertNotIn(self.line_b, lines)
        with self.assertRaises(AccessError):
            self.line_b.with_user(self.billing_a).read(["qty"])

    def test_sync_context_does_not_bypass_access(self):
        Lines = self.env["packaging.invoice.material"].with_user(self.billing_a)
        synced = Lines.with_context(packaging_material_sync=True)
        with self.assertRaises(AccessError):
            self.line_b.with_user(self.billing_a).with_context(packaging_material_sync=True).write({"qty": 9.0})
        with self.assertRaises(AccessError):
            self.line_b.with_user(self.billing_a).with_context(packaging_material_sync=True).unlink()
        with self.assertRaises(AccessError):
            synced.create({"invoice_id": self.invoice_b.id, "material_type": "paper", "qty": 1.0})
        with self.assertRaises(AccessError):
            self.line_a.with_user(self.billing_a).with_context(packaging_material_sync=True).write(
                {"invoice_id": self.invoice_b.id}
            )
        self.assertEqual(self.line_b.qty, 2.0)

    def test_user_without_invoice_rights(self):
        line = self.line_a.with_user(self.internal_a).with_context(packaging_material_sync=True)
        with self.assertRaises(AccessError):
            line.write({"qty": 9.0})
        with self.assertRaises(AccessError):
            line.unlink()
        self.assertEqual(self.line_a.qty, 2.0)

    def test_billing_user_edits_own_company(self):
        line = self.line_a.with_user(self.billing_a)
        line.write({"qty": 5.0})
        self.assertEqual(self.line_a.qty, 5.0)
        self.assertFalse(self.invoice_a.packaging_material_auto)
        self.invoice_a.with_user(self.billing_a).refresh_packaging_material()
        self.assertTrue(self.invoice_a.packaging_material_auto)
