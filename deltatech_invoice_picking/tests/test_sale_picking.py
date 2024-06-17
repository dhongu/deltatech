from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
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
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )

        form_sale_order = Form(self.env["sale.order"])
        form_sale_order.partner_id = self.partner_a
        with form_sale_order.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 10
            so_line.price_unit = 20

        self.sale_order = form_sale_order.save()
        self.sale_order.action_confirm()

    def test_create_invoice_from_picking(self):
        domain = [("name", "=", "deltatech_stock_negative"), ("state", "=", "installed")]
        no_negative_module = self.env["ir.module.module"].sudo().search(domain)
        if no_negative_module:
            for picking in self.sale_order.picking_ids:
                picking.location_id.write({"allow_negative_stock": True})
        for move in self.sale_order.picking_ids.move_ids:
            move._set_quantity_done(move.product_uom_qty)

        self.sale_order.picking_ids.button_validate()

        self.sale_order.picking_ids.action_create_invoice()
