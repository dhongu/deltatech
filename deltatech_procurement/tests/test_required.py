from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):
    def setUp(self):
        super(TestSale, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "route_ids": [
                    (4, self.ref("stock.route_warehouse0_mto")),
                    (4, self.ref("purchase_stock.route_warehouse0_buy")),
                ],
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "product",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
                "route_ids": [
                    (4, self.ref("stock.route_warehouse0_mto")),
                    (4, self.ref("purchase_stock.route_warehouse0_buy")),
                ],
            }
        )

    def test_new_required_order(self):
        required_order_form = Form(self.env["required.order"])

        with required_order_form.required_line.new() as line:
            line.product_id = self.product_a
            line.product_qty = 100

        with required_order_form.required_line.new() as line:
            line.product_id = self.product_b
            line.product_qty = 10

        required_order = required_order_form.save()
        required_order.order_confirm()
