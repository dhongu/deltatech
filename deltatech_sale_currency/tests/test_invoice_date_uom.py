# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInvoiceDateUom(TransactionCase):
    """SALECUR-001: repricing at the invoice date respects the invoice line UoM."""

    @classmethod
    def _get_account(cls, account_type, code, **vals):
        account = cls.env["account.account"].search(
            [("company_ids", "in", cls.company.id), ("account_type", "=", account_type)], limit=1
        )
        return account or cls.env["account.account"].create(
            {"name": code, "code": code, "account_type": account_type, "company_ids": [(6, 0, cls.company.ids)], **vals}
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        income = cls._get_account("income", "XSALEUOM")
        receivable = cls._get_account("asset_receivable", "XRECUOM", reconcile=True)
        payable = cls._get_account("liability_payable", "XPAYUOM", reconcile=True)
        cls.product = cls.env["product.product"].create(
            {"name": "UoM Product", "type": "consu", "list_price": 10.0, "property_account_income_id": income.id}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "UoM Partner",
                "property_account_receivable_id": receivable.id,
                "property_account_payable_id": payable.id,
            }
        )

    def _create_invoice_10_per_unit(self):
        pricelist = self.env["product.pricelist"].create(
            {"name": "Company currency pricelist", "currency_id": self.company.currency_id.id}
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": pricelist.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 24.0, "price_unit": 10.0}),
                ],
            }
        )
        if "journal_id" in sale_order._fields:
            sale_order.journal_id = False
        sale_order.action_confirm()
        invoice = sale_order._create_invoices()
        inv_line = invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product")
        self.assertEqual(inv_line.product_uom_id, self.env.ref("uom.product_uom_unit"))
        self.assertAlmostEqual(inv_line.price_unit, 10.0)
        return invoice, inv_line

    def test_invoice_date_reprice_converts_to_invoice_uom(self):
        invoice, inv_line = self._create_invoice_10_per_unit()
        inv_line.write(
            {"product_uom_id": self.env.ref("uom.product_uom_dozen").id, "quantity": 2.0, "price_unit": 120.0}
        )

        invoice.invoice_date = fields.Date.today() - timedelta(days=1)
        invoice._onchange_invoice_date()
        invoice.flush_recordset()
        inv_line.invalidate_recordset()

        # 10 per Unit = 120 per Dozen, the invoice amount must stay 2 Dozens x 120
        self.assertAlmostEqual(inv_line.price_unit, 120.0)
        self.assertAlmostEqual(invoice.amount_untaxed, 240.0)

    def test_invoice_date_reprice_same_uom_unchanged(self):
        invoice, inv_line = self._create_invoice_10_per_unit()
        inv_line.price_unit = 12.0

        invoice.invoice_date = fields.Date.today() - timedelta(days=1)
        invoice._onchange_invoice_date()

        # same UoM and currency: the sale price is taken back as it is
        self.assertAlmostEqual(inv_line.price_unit, 10.0)
