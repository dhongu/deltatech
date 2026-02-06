# © 2026 Deltatech
# See README.rst file on the addons root folder for license details

from odoo.tests.common import TransactionCase


class TestKitPrice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        self.component_a = self.env["product.product"].create(
            {"name": "Component A", "type": "product", "standard_price": 10.0}
        )
        self.component_b = self.env["product.product"].create(
            {"name": "Component B", "type": "product", "standard_price": 20.0}
        )
        self.kit_product = self.env["product.product"].create({"name": "Kit Product", "type": "product"})

        # Delete any reordering rules that might have been created automatically
        self.env["stock.warehouse.orderpoint"].search(
            [("product_id", "in", [self.component_a.id, self.component_b.id, self.kit_product.id])]
        ).unlink()

        self.bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.kit_product.product_tmpl_id.id,
                "product_id": self.kit_product.id,
                "type": "phantom",
                "bom_line_ids": [
                    (0, 0, {"product_id": self.component_a.id, "product_qty": 1}),
                    (0, 0, {"product_id": self.component_b.id, "product_qty": 2}),
                ],
            }
        )

    def test_kit_purchase_price(self):
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        sale_order_line = self.env["sale.order.line"].create(
            {"order_id": sale_order.id, "product_id": self.kit_product.id, "product_uom_qty": 1}
        )

        # purchase_price is computed by sale_margin
        # deltatech_kit_price overrides _compute_purchase_price to use BoM price for kits
        # BoM price = 1 * 10.0 + 2 * 20.0 = 50.0

        sale_order_line._compute_purchase_price()
        self.assertEqual(sale_order_line.purchase_price, 50.0)

    def test_kit_purchase_price_multi_currency(self):
        # Setup currency EUR
        currency_eur = self.env.ref("base.EUR")
        currency_eur.active = True

        # Set exchange rate: 1 Company Currency = 0.5 EUR
        self.env["res.currency.rate"].create(
            {"currency_id": currency_eur.id, "rate": 0.5, "name": "2026-01-01", "company_id": self.env.company.id}
        )

        # Create a pricelist in EUR to force the SO currency
        pricelist_eur = self.env["product.pricelist"].create(
            {
                "name": "EUR Pricelist",
                "currency_id": currency_eur.id,
            }
        )

        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": pricelist_eur.id,
            }
        )
        # Verify SO currency
        self.assertEqual(sale_order.currency_id, currency_eur)

        sale_order_line = self.env["sale.order.line"].create(
            {"order_id": sale_order.id, "product_id": self.kit_product.id, "product_uom_qty": 1}
        )

        # purchase_price should be computed during creation, but let's call it explicitly to be sure
        sale_order_line._compute_purchase_price()

        # BoM price in company currency = 50.0
        # Expected price in EUR = 50.0 * 0.5 = 25.0

        self.assertAlmostEqual(sale_order_line.purchase_price, 25.0)
