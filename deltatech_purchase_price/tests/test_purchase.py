# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPurchase(TransactionCase):
    def setUp(self):
        super().setUp()
        # se creeaza un furnizor
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "last_purchase_price": 100,
                "trade_markup": 10,
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
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("purchase.update_product_price", "True")
        set_param("purchase.update_list_price", "True")

    def test_product_change_last_purchase_price(self):
        product = Form(self.product_a.product_tmpl_id)
        product.last_purchase_price = 200
        product = product.save()
        product = Form(self.product_b.product_tmpl_id)
        product.last_purchase_price = 200
        product = product.save()

    def test_product_change_trade_markup(self):
        product = Form(self.product_a.product_tmpl_id)
        product.trade_markup = 10
        product = product.save()
        product = Form(self.product_b.product_tmpl_id)
        product.trade_markup = 10
        product = product.save()

    def test_product_change_list_price(self):
        product = Form(self.product_a.product_tmpl_id)
        product.list_price = 250
        product = product.save()
        product = Form(self.product_b.product_tmpl_id)
        product.list_price = 250
        product = product.save()

    def test_purchase(self):
        # se creeaza o comanda de achizitie
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

        # se confirma primirea produselor
        for move_line in self.picking.move_line_ids:
            if move_line.product_id == self.product_a:
                move_line.write({"quantity": 10})

        # se valideaza primirea
        self.picking.button_validate()

        # se verifica ultimul pret de achizitie
        self.assertEqual(self.product_a.last_purchase_price, 10.0)

    def test_wizard_trade_markup(self):
        wizard = Form(self.env["product.markup.wizard"])
        wizard.trade_markup = 10
        wizard.selected_line = True
        wizard = wizard.save()
        active_ids = [
            self.product_a.product_tmpl_id.id,
            self.product_b.product_tmpl_id.id,
        ]
        wizard.with_context(active_ids=active_ids).do_set_trade_markup()

        wizard = Form(self.env["product.markup.wizard"])
        wizard.trade_markup = 10
        wizard.partner_id = self.partner_a
        wizard = wizard.save()
        wizard.do_set_trade_markup()
