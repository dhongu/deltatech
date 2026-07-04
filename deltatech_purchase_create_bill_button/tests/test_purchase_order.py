# © 2026 Deltatech
# See README.rst file on addons root folder for license details

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
