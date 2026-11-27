# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseOrder(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_vendor = self.env["res.partner"].create({"name": "Vendor"})
        self.partner_customer = self.env["res.partner"].create({"name": "Customer"})
        self.product = self.env["product.product"].create({"name": "Product", "type": "consu"})

        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_customer.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "price_unit": 100.0})],
            }
        )
        self.sale_line = self.sale_order.order_line[0]

        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1.0,
                            "price_unit": 90.0,
                            "sale_line_id": self.sale_line.id,
                        },
                    )
                ],
            }
        )

    def test_purchase_price_warning(self):
        # Case 1: Purchase price (90) < Sale price (100) -> No warning
        self.purchase_order._compute_purchase_price_warning()
        self.assertFalse(self.purchase_order.purchase_price_warning)

        # Case 2: Purchase price (110) > Sale price (100) -> Warning
        self.purchase_order.order_line[0].price_unit = 110.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertTrue(self.purchase_order.purchase_price_warning)
        self.assertIn("110", self.purchase_order.purchase_price_warning)
        self.assertIn("100", self.purchase_order.purchase_price_warning)
        self.assertIn("10", self.purchase_order.purchase_price_warning)  # Diff
        self.assertIn("Purchase", self.purchase_order.purchase_price_warning)
        self.assertIn("Sale", self.purchase_order.purchase_price_warning)

        # Case 3: No sale line -> No warning
        self.purchase_order.order_line[0].sale_line_id = False
        self.purchase_order._compute_purchase_price_warning()
        self.assertFalse(self.purchase_order.purchase_price_warning)

    def test_purchase_price_warning_with_taxes(self):
        # Create a tax that is included in the price
        tax_incl = self.env["account.tax"].create(
            {
                "name": "Tax Included",
                "amount": 20.0,
                "price_include_override": "tax_included",
                "type_tax_use": "sale",
                "amount_type": "percent",
            }
        )
        self.sale_line.tax_ids = [(6, 0, tax_incl.ids)]
        self.sale_line.price_unit = 120.0  # 100 + 20% tax

        # Purchase price (110) > Sale price without tax (100) -> Warning
        self.purchase_order.order_line[0].price_unit = 110.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertTrue(self.purchase_order.purchase_price_warning)
        self.assertIn("110", self.purchase_order.purchase_price_warning)
        self.assertIn("100", self.purchase_order.purchase_price_warning)

        # Purchase price (95) < Sale price without tax (100) -> No warning
        self.purchase_order.order_line[0].price_unit = 95.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertFalse(self.purchase_order.purchase_price_warning)

    def _get_foreign_currency(self, rate):
        """O monedă diferită de a companiei, cu 1 unitate = ``rate`` unități din moneda companiei."""
        company = self.env.company
        currency = (
            self.env["res.currency"]
            .with_context(active_test=False)
            .search([("id", "!=", company.currency_id.id), ("name", "in", ["EUR", "USD"])], limit=1)
        )
        currency.active = True
        self.env["res.currency.rate"].search(
            [("currency_id", "=", currency.id), ("company_id", "in", [company.id, False])]
        ).unlink()
        self.env["res.currency.rate"].create(
            {
                "name": "2000-01-01",
                "currency_id": currency.id,
                "company_id": company.id,
                "rate": 1.0 / rate,
            }
        )
        return currency

    def test_purchase_price_warning_currency(self):
        # Vânzare 10 în moneda străină (curs 5) = 50 în moneda companiei; achiziție 40 -> fără avertizare
        currency = self._get_foreign_currency(5.0)
        pricelist = self.env["product.pricelist"].create({"name": "Foreign", "currency_id": currency.id})
        self.sale_order.pricelist_id = pricelist
        self.assertEqual(self.sale_order.currency_id, currency)
        self.sale_line.price_unit = 10.0
        self.purchase_order.order_line[0].price_unit = 40.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertFalse(self.purchase_order.purchase_price_warning)

        # Achiziție 60 > 50 -> avertizare
        self.purchase_order.order_line[0].price_unit = 60.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertTrue(self.purchase_order.purchase_price_warning)
        self.assertIn("60", self.purchase_order.purchase_price_warning)
        self.assertIn("50", self.purchase_order.purchase_price_warning)

    def test_purchase_price_warning_uom(self):
        # Achiziție 120 / duzină = 10 / bucată; vânzare 15 / bucată -> fără avertizare
        dozen = self.env.ref("uom.product_uom_dozen")
        self.purchase_order.order_line[0].write({"product_uom_id": dozen.id, "price_unit": 120.0})
        self.sale_line.price_unit = 15.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertFalse(self.purchase_order.purchase_price_warning)

        # Achiziție 240 / duzină = 20 / bucată > 15 -> avertizare
        self.purchase_order.order_line[0].price_unit = 240.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertTrue(self.purchase_order.purchase_price_warning)

    def test_purchase_price_warning_discount(self):
        # Vânzare 100 cu discount 50% = 50; achiziție 80 -> avertizare
        self.sale_line.write({"price_unit": 100.0, "discount": 50.0})
        self.purchase_order.order_line[0].price_unit = 80.0
        self.purchase_order._compute_purchase_price_warning()
        self.assertTrue(self.purchase_order.purchase_price_warning)
        self.assertIn("80", self.purchase_order.purchase_price_warning)
        self.assertIn("50", self.purchase_order.purchase_price_warning)

        # Achiziție 120 cu discount 60% = 48 < 50 -> fără avertizare
        self.purchase_order.order_line[0].write({"price_unit": 120.0, "discount": 60.0})
        self.purchase_order._compute_purchase_price_warning()
        self.assertFalse(self.purchase_order.purchase_price_warning)

    def test_purchase_price_warning_recompute_on_discount(self):
        # Avertizarea se recalculează la schimbarea discountului (dependență în @api.depends)
        self.purchase_order.order_line[0].price_unit = 80.0
        self.assertFalse(self.purchase_order.purchase_price_warning)
        self.sale_line.discount = 50.0
        self.assertTrue(self.purchase_order.purchase_price_warning)
