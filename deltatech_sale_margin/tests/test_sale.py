from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a product with a purchase price
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "purchase_ok": True,
                "list_price": 100.0,  # Sale price
                "standard_price": 50.0,  # Purchase price
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create a sale order with one order line
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )
        self.sale_order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 40.0,  # Below the purchase price
            }
        )

    def test_price_warning_message(self):
        # Test that the warning message is computed correctly
        self.sale_order._compute_price_warning_message()
        expected_warning = (
            "The unit price of product Test Product is lower than the purchase price. The margin is negative."
        )
        self.assertEqual(self.sale_order.price_warning_message, expected_warning)

    def test_onchange_product_id_warning(self):
        # Test that a warning is raised when setting a product with a price below purchase price
        sale_order_line = self.env["sale.order.line"].new(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 40.0,
            }
        )
        sale_order_line._onchange_product_id_warning()
        self.assertIn("warning", sale_order_line._onchange_product_id_warning())
        self.assertEqual(
            sale_order_line._onchange_product_id_warning()["warning"]["message"],
            "Do not sell below the purchase price.",
        )

    def test_price_unit_change(self):
        # Test that a warning is raised when changing the price unit below the purchase price
        sale_order_line = self.env["sale.order.line"].new(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 60.0,
            }
        )
        sale_order_line.price_unit_change()
        sale_order_line.price_unit = 40.0
        sale_order_line.price_unit_change()
        self.assertIn("warning", sale_order_line.price_unit_change())
        self.assertEqual(
            sale_order_line.price_unit_change()["warning"]["message"], "Do not sell below the purchase price."
        )

    def test_website_order_ignores_margin_check(self):
        # Test that website orders ignore the margin check
        self.env["ir.config_parameter"].sudo().set_param("sale.margin_limit_check_validate", "True")
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )
        self.sale_order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 40.0,  # Below the purchase price
            }
        )
        self.sale_order.action_confirm()

        self.sale_order.order_line.write({"product_uom_qty": 2})

    def test_sale_order_line_write(self):
        self.env["ir.config_parameter"].sudo().set_param("sale.margin_limit_check_validate", "True")
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.sale_order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 40.0,  # Below the purchase price
            }
        )
        self.sale_order.order_line.write({"product_uom_qty": 2})
