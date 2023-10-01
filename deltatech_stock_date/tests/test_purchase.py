# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPurchase(TransactionCase):
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
            {"name": "Test B", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("purchase.update_product_price", "True")
        set_param("purchase.update_list_price", "True")

    def test_purchase(self):
        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10

        po = form_purchase.save()

        # se valideaza comanda de achizitie
        po.button_confirm()
        self.picking = po.picking_ids[0]
        self.picking.action_assign()

        # se confirma primirea produselor
        for move_line in self.picking.move_line_ids:
            if move_line.product_id == self.product_a:
                move_line.write({"qty_done": 10})

        # se valideaza primirea
        self.picking.with_context(force_period_date="2020-01-03").button_validate()
