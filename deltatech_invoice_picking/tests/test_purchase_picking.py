from odoo.exceptions import UserError
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

        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10

        self.po = form_purchase.save()
        self.po.button_confirm()

    def test_create_invoice_from_picking(self):
        for move in self.po.picking_ids.move_ids:
            move._set_quantity_done(move.product_uom_qty)
        self.po.picking_ids.button_validate()
        self.po.picking_ids.supplier_invoice_number = "Test1234"
        self.po.picking_ids.action_create_supplier_invoice()
        self.assertTrue(self.po.invoice_ids)
