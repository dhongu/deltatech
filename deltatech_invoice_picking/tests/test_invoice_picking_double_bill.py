from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestSupplierInvoiceDoubleBill(common.TransactionCase):
    """PICKINV-004: a receipt must not be billed again once it is billed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor PICKINV-004"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product PICKINV-004",
                "is_storable": True,
                "purchase_method": "receive",
                "standard_price": 10.0,
            }
        )

    def _create_order(self, qty):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": 10.0,
                            "date_planned": fields.Date.today(),
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        return order

    def _receive(self, picking, qty):
        picking.move_ids.quantity = qty
        res = picking.button_validate()
        if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
            self.env["stock.backorder.confirmation"].with_context(**res["context"]).process()
        return picking

    def _bill(self, pickings, ref):
        pickings.write({"supplier_invoice_number": ref})
        action = pickings.action_create_supplier_invoice()
        return self.env["account.move"].browse(action.get("res_id")) or self.env["account.move"].search(
            action.get("domain") or [("id", "=", 0)]
        )

    def test_billed_receipt_cannot_be_billed_again(self):
        order = self._create_order(5)
        picking = self._receive(order.picking_ids, 5)
        bill = self._bill(picking, "BILL-004-A")
        self.assertEqual(bill.invoice_line_ids.quantity, 5)
        self.assertEqual(picking.account_move_id, bill)

        with self.assertRaises(UserError):
            self._bill(picking, "BILL-004-B")
        self.assertEqual(order.invoice_ids, bill, "No second bill may be created")
        self.assertEqual(picking.account_move_id, bill, "The invoice link must not be overwritten")
        self.assertEqual(order.order_line.qty_invoiced, 5)

    def test_receipt_billed_from_order_is_capped(self):
        # 10 ordered, receipt of 4, backorder of 6; the order is billed natively for the 4 received
        order = self._create_order(10)
        first = self._receive(order.picking_ids, 4)
        backorder = order.picking_ids - first
        order.action_create_invoice()
        self.assertEqual(order.order_line.qty_invoiced, 4)

        # the first receipt has nothing left to bill
        with self.assertRaises(UserError):
            self._bill(first, "BILL-004-C")

        # receive the rest; billing both receipts bills only the 6 still to bill, not 10
        self._receive(backorder, 6)
        bill = self._bill(first | backorder, "BILL-004-D")
        self.assertEqual(bill.invoice_line_ids.quantity, 6)
        self.assertEqual(order.order_line.qty_invoiced, 10)

    def test_cancelled_bill_allows_billing_again(self):
        order = self._create_order(3)
        picking = self._receive(order.picking_ids, 3)
        bill = self._bill(picking, "BILL-004-E")
        bill.button_cancel()
        self.assertFalse(picking.account_move_id)

        new_bill = self._bill(picking, "BILL-004-F")
        self.assertNotEqual(new_bill, bill)
        self.assertEqual(new_bill.invoice_line_ids.quantity, 3)
        self.assertEqual(picking.account_move_id, new_bill)
