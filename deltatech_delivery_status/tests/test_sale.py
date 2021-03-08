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
            {"name": "Test B", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )

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

        self.so.postpone_delivery()
        self.so.release_delivery()
