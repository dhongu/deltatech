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
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 70, "list_price": 150, "seller_ids": seller_ids}
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

    def test_sale_picking_policy_direct(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so._compute_is_ready()
        self.so.action_confirm()
        self.so._compute_is_ready()

        self.picking = self.so.picking_ids
        self.picking.action_assign()
        for move_line in self.picking.move_ids:
            if move_line.product_uom_qty > 0 and move_line.quantity == 0:
                move_line.write({"quantity": move_line.product_uom_qty})
        self.picking._action_done()
        self.so._compute_is_ready()

        invoice = self.so._create_invoices()
        invoice = Form(invoice)
        invoice = invoice.save()
        # invoice.post()

    def test_sale_picking_policy_one(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.picking_policy = "one"
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so._compute_is_ready()
        self.so.action_confirm()
        self.so._compute_is_ready()

        self.picking = self.so.picking_ids
        self.picking.action_assign()
        for move_line in self.picking.move_ids:
            if move_line.product_uom_qty > 0 and move_line.quantity == 0:
                move_line.write({"quantity": move_line.product_uom_qty})
        self.picking._action_done()
        self.so._compute_is_ready()

        invoice = self.so._create_invoices()
        invoice = Form(invoice)
        invoice = invoice.save()
        # invoice.post()

    def test_sale_search_search_is_ready(self):
        self.env["sale.order"].search([("is_ready", "=", True)])