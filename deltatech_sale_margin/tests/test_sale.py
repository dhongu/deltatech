# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):
    def setUp(self):
        super(TestSale, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 70, "list_price": 150, "seller_ids": seller_ids}
        )
        self.stock_location = self.env["ir.model.data"].xmlid_to_object("stock.stock_location_stock")
        inv_line_a = {
            "product_id": self.product_a.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inv_line_b = {
            "product_id": self.product_b.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inventory = self.env["stock.inventory"].create(
            {
                "name": "Inv. productserial1",
                "line_ids": [
                    (0, 0, inv_line_a),
                    (0, 0, inv_line_b),
                ],
            }
        )
        inventory.action_start()
        inventory.action_validate()

    def test_sale(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        self.picking = self.so.picking_ids
        self.picking.action_assign()
        for move_line in self.picking.move_lines:
            if move_line.product_uom_qty > 0 and move_line.quantity_done == 0:
                move_line.write({"quantity_done": move_line.product_uom_qty})
        self.picking._action_done()
        invoice = self.so._create_invoices()
        invoice = Form(invoice)
        invoice = invoice.save()
        invoice.post()
