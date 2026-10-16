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
