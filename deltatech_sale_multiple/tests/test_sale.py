# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "qty_multiple": 100,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "product",
                "standard_price": 70,
                "list_price": 150,
                "qty_minim": 10,
                "seller_ids": seller_ids,
            }
        )

        self.stock_location = self.env.ref("stock.stock_location_stock")

        self.env["stock.quant"]._update_available_quantity(self.product_a, self.stock_location, 1000)
        self.env["stock.quant"]._update_available_quantity(self.product_b, self.stock_location, 1000)

        # inv_line_a = {
        #     "product_id": self.product_a.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }
        # inv_line_b = {
        #     "product_id": self.product_b.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }
        # inventory = self.env["stock.inventory"].create(
        #     {
        #         "name": "Inv. productserial1",
        #         "line_ids": [
        #             (0, 0, inv_line_a),
        #             (0, 0, inv_line_b),
        #         ],
        #     }
        # )
        # inventory.action_start()
        # inventory.action_validate()

    def test_sale(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 1

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 1

        self.so = so.save()

    def test_write_sale_order_line(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "purchase_ok": True,
                "list_price": 100.0,  # Sale price
                "standard_price": 50.0,  # Purchase price
            }
        )
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create a sale order with one order line
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
            }
        )
        sale_order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "price_unit": 40.0,  # Below the purchase price
            }
        )
        sale_order_line.write({"product_uom_qty": 2.0})
