# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import common


class TestSaleCurrency(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.currency_eur = cls.env.ref("base.EUR")
        cls.currency_usd = cls.env.ref("base.USD")

        # Create a pricelist in USD
        cls.pricelist_usd = cls.env["product.pricelist"].create(
            {
                "name": "USD Pricelist",
                "currency_id": cls.currency_usd.id,
            }
        )

        # Create a product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )

        # Create a partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create a journal with EUR currency
        cls.journal_eur = cls.env["account.journal"].create(
            {
                "name": "EUR Journal",
                "type": "sale",
                "code": "S_EUR",
                "currency_id": cls.currency_eur.id,
            }
        )

    def test_01_sale_to_invoice_currency_conversion(self):
        # Create Sale Order in USD
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist_usd.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 100.0,  # 100 USD
                        },
                    )
                ],
            }
        )

        # Set journal on SO (if possible, or we'll mock _prepare_invoice)
        # In standard Odoo, journal is not on SO, but deltatech_sale_currency uses self.journal_id
        # Let's check if journal_id is added to sale.order by this or another module

        if "journal_id" in self.env["sale.order"]._fields:
            sale_order.journal_id = self.journal_eur.id

        # Confirm Sale Order
        sale_order.action_confirm()

        # Create Invoice
        invoice = sale_order._create_invoices()

        # Check Invoice Currency
        # Based on models/sale.py:
        # currency = self.journal_id.currency_id or self.company_id.currency_id
        # res["currency_id"] = currency.id

        expected_currency = (
            self.journal_eur.currency_id if "journal_id" in sale_order._fields else self.company.currency_id
        )
        self.assertEqual(invoice.currency_id, expected_currency)

        # Check Price Unit Conversion
        # Based on models/sale.py _prepare_invoice_line:
        # price_unit = from_currency._convert(res["price_unit"], to_currency, company, date_eval)

        so_line = sale_order.order_line[0]
        inv_line = invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product")

        from_currency = sale_order.pricelist_id.currency_id
        to_currency = invoice.currency_id
        expected_price = from_currency._convert(so_line.price_unit, to_currency, self.company, fields.Date.today())

        self.assertAlmostEqual(inv_line.price_unit, expected_price)
