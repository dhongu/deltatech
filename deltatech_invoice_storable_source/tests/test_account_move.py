# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMove(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_storable = cls.env["product.product"].create(
            {
                "name": "Storable Product",
                "is_storable": True,
                "standard_price": 10.0,
                "list_price": 20.0,
                "invoice_policy": "order",
            }
        )
        cls.product_service = cls.env["product.product"].create(
            {"name": "Service Product", "type": "service", "list_price": 15.0}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.env.company.write({"check_storable_sale_source": True, "check_storable_purchase_source": True})

    def _create_move(self, move_type, product):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "invoice_line_ids": [(0, 0, {"product_id": product.id, "quantity": 1, "price_unit": 20.0})],
            }
        )

    def test_01_out_invoice_storable_no_so(self):
        invoice = self._create_move("out_invoice", self.product_storable)
        with self.assertRaisesRegex(UserError, "only from a sale order"):
            invoice.action_post()

    def test_02_out_invoice_service_no_so(self):
        invoice = self._create_move("out_invoice", self.product_service)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_03_in_invoice_storable_no_po(self):
        bill = self._create_move("in_invoice", self.product_storable)
        with self.assertRaisesRegex(UserError, "only from a purchase order"):
            bill.action_post()

    def test_04_out_invoice_storable_no_so_check_off(self):
        self.env.company.check_storable_sale_source = False
        invoice = self._create_move("out_invoice", self.product_storable)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_05_in_invoice_storable_no_po_purchase_check_off(self):
        """The vendor bill check is independent of the customer invoice check"""
        self.env.company.check_storable_purchase_source = False
        bill = self._create_move("in_invoice", self.product_storable)
        bill.action_post()
        self.assertEqual(bill.state, "posted")

    def test_06_out_invoice_and_refund_from_so(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product_storable.id, "product_uom_qty": 1})],
            }
        )
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        refund = invoice._reverse_moves()
        refund.action_post()
        self.assertEqual(refund.state, "posted")

    def test_07_in_invoice_from_po(self):
        self.product_storable.purchase_method = "purchase"
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product_storable.id, "product_qty": 1})],
            }
        )
        order.button_confirm()
        order.action_create_invoice()
        bill = order.invoice_ids
        bill.invoice_date = "2026-01-01"
        bill.action_post()
        self.assertEqual(bill.state, "posted")

    def test_08_mass_confirm_storable_no_so(self):
        """Confirming from the list (Actions > Confirm) goes through the same check"""
        invoice = self._create_move("out_invoice", self.product_storable)
        wizard = (
            self.env["validate.account.move"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({})
        )
        with self.assertRaisesRegex(UserError, "only from a sale order"):
            wizard.validate_move()

    def test_09_sale_receipt_storable_no_so(self):
        receipt = self._create_move("out_receipt", self.product_storable)
        with self.assertRaisesRegex(UserError, "only from a sale order"):
            receipt.action_post()

    def test_10_in_refund_from_po_bill(self):
        self.product_storable.purchase_method = "purchase"
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product_storable.id, "product_qty": 1})],
            }
        )
        order.button_confirm()
        order.action_create_invoice()
        bill = order.invoice_ids
        bill.invoice_date = "2026-01-01"
        bill.action_post()
        refund = bill._reverse_moves([{"invoice_date": "2026-01-02"}])
        refund.action_post()
        self.assertEqual(refund.state, "posted")
