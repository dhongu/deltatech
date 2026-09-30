# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseOrderCreateBill(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_vendor = self.env["res.partner"].create({"name": "Vendor"})
        self.product = self.env["product.product"].create({"name": "Product", "type": "consu"})

        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "partner_ref": "GRW0003",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        self.purchase_order.button_confirm()

    def test_prepare_invoice_copies_vendor_reference(self):
        invoice_vals = self.purchase_order._prepare_invoice()
        self.assertEqual(invoice_vals["ref"], "GRW0003")
        self.assertEqual(invoice_vals["payment_reference"], "GRW0003")

    def test_prepare_invoice_without_vendor_reference(self):
        self.purchase_order.partner_ref = False
        invoice_vals = self.purchase_order._prepare_invoice()
        self.assertEqual(invoice_vals["ref"], "")
        self.assertEqual(invoice_vals["payment_reference"], "")

    def _make_order(self, qty=1.0, price=100.0):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": price,
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        return order

    def test_create_bills_button_in_list_header(self):
        """The list view used by the RFQ/purchase order menu offers "Create Bills"."""
        view = self.env.ref("purchase.purchase_order_kpis_tree")
        arch = self.env["purchase.order"].get_view(view.id, "list")["arch"]
        self.assertIn('name="action_create_invoice"', arch)

    def test_create_bill_button_in_form(self):
        view = self.env.ref("purchase.purchase_order_form")
        arch = self.env["purchase.order"].get_view(view.id, "form")["arch"]
        self.assertIn('name="action_create_invoice"', arch)

    def test_create_bills_from_several_orders_returns_one_credit_note(self):
        """Two returned orders billed together give a single vendor credit note."""
        self.product.purchase_method = "purchase"
        orders = self._make_order(qty=2.0) | self._make_order(qty=3.0)
        orders.action_create_invoice()
        bills = orders.invoice_ids
        self.assertEqual(len(bills), 1)
        bills.invoice_date = fields.Date.context_today(bills)
        bills.action_post()

        # the goods go back to the vendor: the ordered quantities drop below what
        # was already invoiced, so both orders are left with a negative quantity
        for order in orders:
            order.order_line.product_qty = 0.0
        self.assertEqual(set(orders.mapped("invoice_status")), {"to invoice"})

        orders.action_create_invoice()
        storno = orders.invoice_ids - bills
        self.assertEqual(len(storno), 1)
        self.assertEqual(storno.move_type, "in_refund")
        self.assertEqual(storno.amount_untaxed, 500.0)
