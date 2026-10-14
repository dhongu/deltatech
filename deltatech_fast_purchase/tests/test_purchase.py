# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": cls.partner_a.id})]
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test A",
                "type": "consu",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
                "purchase_method": "purchase",
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Test B",
                "type": "consu",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
                "purchase_method": "purchase",
            }
        )

    def _create_po(self, partner_ref=False):
        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        if partner_ref:
            form_purchase.partner_ref = partner_ref
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_b
            po_line.product_qty = 5
            po_line.price_unit = 20
        return form_purchase.save()

    def _check_received_and_billed(self, po, action):
        self.assertEqual(po.state, "purchase")
        self.assertTrue(po.picking_ids)
        self.assertEqual(set(po.picking_ids.mapped("state")), {"done"})
        self.assertFalse(any(po.picking_ids.mapped("notice")))
        for line in po.order_line:
            self.assertEqual(line.qty_received, line.product_qty)
        self.assertEqual(self.product_a.qty_available, 10)
        self.assertEqual(self.product_b.qty_available, 5)

        bill = po.invoice_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(action.get("res_id"), bill.id)
        self.assertEqual(bill.amount_untaxed, 200)
        quantities = {line.product_id: line.quantity for line in bill.invoice_line_ids}
        self.assertEqual(quantities, {self.product_a: 10, self.product_b: 5})

    def test_purchase_confirm_to_invoice(self):
        po = self._create_po(partner_ref="SUP-001")
        action = po.action_button_confirm_to_invoice()
        self._check_received_and_billed(po, action)
        self.assertEqual(po.picking_ids.origin, "SUP-001")

    def test_purchase_receipt_to_invoice(self):
        po = self._create_po()
        po.button_confirm()
        self.assertEqual(po.picking_ids.state, "assigned")
        action = po.action_button_confirm_to_invoice()
        self._check_received_and_billed(po, action)
        self.assertEqual(po.picking_ids.origin, po.name)

    def test_purchase_confirm_notice(self):
        po = self._create_po()
        # comanda neconfirmata nu are receptii
        self.assertFalse(po.action_button_confirm_notice())

        po.button_confirm()
        action = po.action_button_confirm_notice()
        picking = po.picking_ids
        self.assertTrue(picking.notice)
        self.assertEqual(action.get("res_id"), picking.id)
        self.assertEqual(action.get("res_model"), "stock.picking")

        # receptia pe baza de aviz anuleaza marcajul de aviz
        po.action_button_confirm_to_invoice()
        self.assertEqual(picking.state, "done")
        self.assertFalse(picking.notice)

    def test_picking_view_invoice(self):
        po = self._create_po()
        po.action_button_confirm_to_invoice()
        picking = po.picking_ids
        action = picking.action_view_invoice()
        self.assertEqual(action.get("res_id"), po.invoice_ids.id)

    def test_picking_view_invoice_without_purchase(self):
        picking_type = self.env.ref("stock.picking_type_in")
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": self.partner_a.id,
            }
        )
        self.assertFalse(picking.action_view_invoice())
