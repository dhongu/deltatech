# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPurchase(TransactionCase):
    def setUp(self):
        super().setUp()
        # se adauga un furnizor
        self.partner_a = self.env["res.partner"].create({"name": "Test"})
        # se adauga un produs
        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        # se adauga un produs
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )

    def test_purchase_confirm_to_invoice(self):
        # se creaza o comanda de achizitie
        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10

        # se salveaza comanda de achizitie
        po = form_purchase.save()

        # se confirma comanda de achizitie
        po.action_button_confirm_to_invoice()
        # se verifica ca comanda de achizitie este confirmata
        self.assertEqual(po.state, "purchase")

        # se verifica daca comanda de achizitie are o factura
        self.assertTrue(po.invoice_ids)

    def test_purchase_receipt_to_invoice(self):
        # se creaza o comanda de achizitie
        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10

        # se salveaza comanda de achizitie
        po = form_purchase.save()

        # se confirma comanda de achizitie
        po.button_confirm()

        # se confirna si se genereaza raceptia si factura
        po.action_button_confirm_to_invoice()

        # se verifica ca comanda de achizitie are o factura
        self.assertTrue(po.invoice_ids)

    def test_purchase_confirm_notice(self):
        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10

        po = form_purchase.save()
        po.action_button_confirm_notice()
