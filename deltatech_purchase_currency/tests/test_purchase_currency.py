# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from freezegun import freeze_time

from odoo import Command, fields
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@freeze_time("2026-11-19")
@tagged("post_install", "-at_install")
class TestPurchaseCurrency(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # 1 company currency = 0.2 EUR from January, 0.25 EUR from November
        cls.eur = cls.setup_other_currency("EUR", rates=[("2026-01-01", 0.2), ("2026-11-01", 0.25)])
        cls.journal_company = cls.company_data["default_journal_purchase"]
        cls.journal_company.currency_id = False
        cls.journal_eur = cls.env["account.journal"].create(
            {
                "name": "Vendor Bills EUR",
                "code": "BEUR",
                "type": "purchase",
                "currency_id": cls.eur.id,
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Profile",
                "type": "consu",
                "purchase_method": "purchase",
                "standard_price": 10.0,
                "supplier_taxes_id": [Command.clear()],
            }
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")

    def _create_po(self, journal=None, price=100.0):
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_a.id,
                "currency_id": self.eur.id,
                "journal_id": journal.id if journal else False,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_qty": 1.0,
                            "uom_id": self.uom_unit.id,
                            "price_unit": price,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        po.button_confirm()
        return po

    def _create_bill(self, po):
        po.action_create_invoice()
        return po.invoice_ids

    def test_ca1_bill_in_journal_currency(self):
        """CA1: EUR order with a journal without currency is billed in the company currency."""
        po = self._create_po(self.journal_company)
        bill = self._create_bill(po)
        self.assertEqual(bill.currency_id, self.company.currency_id)
        self.assertEqual(bill.journal_id, self.journal_company)
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 400.0)  # 100 / 0.25

    def test_ca2_bill_date_rate(self):
        """CA2: changing the bill date converts the order price at that date's rate."""
        bill = self._create_bill(self._create_po(self.journal_company))
        with Form(bill) as form:
            form.invoice_date = fields.Date.to_date("2026-03-01")
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 500.0)  # 100 / 0.2

    def test_ca3_no_journal_keeps_order_currency(self):
        """CA3: without an invoicing journal the bill stays in the order currency."""
        bill = self._create_bill(self._create_po())
        self.assertEqual(bill.currency_id, self.eur)
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 100.0)
        with Form(bill) as form:
            form.invoice_date = fields.Date.to_date("2026-03-01")
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 100.0)

    def test_ca4_eur_journal(self):
        """CA4: with a journal in EUR the bill is in EUR, on that journal."""
        bill = self._create_bill(self._create_po(self.journal_eur))
        self.assertEqual(bill.currency_id, self.eur)
        self.assertEqual(bill.journal_id, self.journal_eur)
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 100.0)

    def test_ca5_bill_line_uom(self):
        """CA5: the order price is brought to the bill line unit, then converted."""
        bill = self._create_bill(self._create_po(self.journal_company, price=10.0))
        with Form(bill) as form:
            with form.invoice_line_ids.edit(0) as line:
                line.product_uom_id = self.uom_dozen
            form.invoice_date = fields.Date.to_date("2026-03-01")
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 600.0)  # 10 * 12 / 0.2

    def test_ca6_matching_flag(self):
        """CA6: the matching flag compares prices in the bill currency."""
        bill = self._create_bill(self._create_po(self.journal_company))
        line = bill.invoice_line_ids
        self.assertFalse(line.purchase_matching_issue_msg)
        line.price_unit = 450.0
        self.assertTrue(line.purchase_matching_issue_msg)
        self.assertIn("⬆", line.purchase_matching_issue_msg)

    def test_ca7_auto_complete(self):
        """CA7: a new bill auto-completed from the order takes its journal and currency."""
        po = self._create_po(self.journal_company)
        form = Form(self.env["account.move"].with_context(default_move_type="in_invoice"))
        form.partner_id = self.partner_a
        form.invoice_date = fields.Date.to_date("2026-03-01")
        with mute_logger("odoo.tests.form.onchange"):
            form.purchase_vendor_bill_id = self.env["purchase.bill.union"].browse(-po.id)
        bill = form.save()
        self.assertEqual(bill.currency_id, self.company.currency_id)
        self.assertEqual(bill.journal_id, self.journal_company)
        self.assertAlmostEqual(bill.invoice_line_ids.price_unit, 500.0)
