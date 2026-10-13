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
                "is_storable": True,
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
                "is_storable": True,
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

    def test_multi_variant_last_purchase_price(self):
        # produs cu mai multe variante: pe sablon ultimul pret de achizitie nu
        # mai trebuie sa fie 0, ci pretul de la furnizor (tichet 8403)
        attribute = self.env["product.attribute"].create(
            {
                "name": "Test Size",
                "create_variant": "always",
                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "L"})],
            }
        )
        template = self.env["product.template"].create(
            {
                "name": "Variant template",
                "is_storable": True,
                "trade_markup": 10,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, attribute.value_ids.ids)],
                        },
                    )
                ],
            }
        )
        self.assertEqual(len(template.product_variant_ids), 2)
        # nativ, sablonul multi-varianta ar avea 0
        self.assertEqual(template.last_purchase_price, 0.0)

        variant_l = template.product_variant_ids[-1]
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner_a.id,
                "product_tmpl_id": template.id,
                "product_id": variant_l.id,
                "price": 20,
            }
        )
        # furnizorul actualizeaza pretul variantei, iar sablonul il preia
        self.assertEqual(variant_l.last_purchase_price, 20.0)
        self.assertEqual(template.last_purchase_price, 20.0)

    def test_last_purchase_price_readable_as_public(self):
        # tichet 8921: last_purchase_price este afisat indirect pe website
        # (deltatech_price_categ). Pentru sabloanele multi-varianta compute-ul
        # citeste seller_ids (product.supplierinfo), la care userul Public nu are
        # drept. Fara compute_sudo, citirea crapa cu 403 la /shop. Verificam ca
        # un user public poate citi campul fara AccessError.
        attribute = self.env["product.attribute"].create(
            {
                "name": "Public Size",
                "create_variant": "always",
                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "L"})],
            }
        )
        template = self.env["product.template"].create(
            {
                "name": "Public variant template",
                "is_storable": True,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, attribute.value_ids.ids)],
                        },
                    )
                ],
            }
        )
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner_a.id,
                "product_tmpl_id": template.id,
                "product_id": template.product_variant_ids[-1].id,
                "price": 20,
            }
        )
        public_user = self.env.ref("base.public_user")
        template.invalidate_recordset(["last_purchase_price"])
        # nu trebuie sa ridice AccessError pe product.supplierinfo
        price = template.with_user(public_user).last_purchase_price
        self.assertEqual(price, 20.0)

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
