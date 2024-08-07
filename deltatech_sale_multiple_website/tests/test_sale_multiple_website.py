from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "type": "product",
                "list_price": 100.0,
                "standard_price": 50.0,
                "check_min_website": True,
            }
        )

        # Create a sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )

        # Create a sale order line
        self.sale_order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.product_variant_id.id,
                "product_uom_qty": 1,
            }
        )

    def test_cart_update_order_line(self):
        # Update the order line
        self.sale_order._cart_update_order_line(self.product.product_variant_id.id, 2, self.sale_order_line)
        self.assertEqual(self.sale_order_line.product_uom_qty, 2, "The quantity of the order line should be updated")

    def test_fix_qty_multiple(self):
        # Fix the quantity
        fixed_qty = self.sale_order_line.fix_qty_multiple(self.product, self.product.uom_id, 3)
        self.assertEqual(fixed_qty, 3, "The quantity should be fixed")
