from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestPurchaseOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Product = self.env["product.product"]
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.AccountMove = self.env["account.move"]

        # Create a product
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "type": "product",
                "purchase_method": "purchase",
            }
        )

        # Create a purchase order
        self.purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "date_order": fields.Date.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_qty": 10,
                            "product_uom": self.env.ref("uom.product_uom_unit").id,
                            "price_unit": 100,
                            "date_planned": fields.Date.today(),
                        },
                    )
                ],
            }
        )

    def test_action_view_invoice(self):
        # Confirm the purchase order
        self.purchase_order.button_confirm()

        # Create a picking and mark it as done to receive the products
        picking = self.purchase_order.picking_ids[0]
        picking.move_line_ids.write({"qty_done": 10})
        picking.button_validate()
        self.purchase_order.action_create_invoice()
        # Create an invoice
        self.purchase_order.action_view_invoice()

    def test_prepare_account_move_line(self):
        # Confirm the purchase order
        self.purchase_order.button_confirm()

        # Create an invoice with negative quantity
        line = self.purchase_order.order_line[0]
        move = self.AccountMove.create(
            {
                "partner_id": self.purchase_order.partner_id.id,
                "move_type": "in_refund",
                "invoice_date": fields.Date.today(),
            }
        )

        move_line_vals = line._prepare_account_move_line(move=move)
        move_line_vals["move_id"] = move.id  # Ensure move_id is set

        move_line = self.env["account.move.line"].create(move_line_vals)

        # Check the quantity on the move line
        if line.product_id.purchase_method == "purchase":
            expected_qty = line.qty_invoiced - line.product_qty
        else:
            expected_qty = line.qty_invoiced - line.qty_received

        if float_compare(expected_qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            expected_qty = 0.0

        self.assertEqual(move_line.quantity, expected_qty)
