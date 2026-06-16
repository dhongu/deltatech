# ©  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleReturnCause(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "list_price": 100.0,
            }
        )
        cls.return_cause = cls.env["sale.return.cause"].create(
            {
                "name": "Test Cause",
            }
        )

    def test_01_create_sale_order_with_cause(self):
        """Test automatic setting of return_cause_date on create"""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "return_cause_id": self.return_cause.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(order.return_cause_date, fields.Date.today())

    def test_02_write_sale_order_with_cause(self):
        """Test automatic setting of return_cause_date on write"""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )
        self.assertFalse(order.return_cause_date)
        order.write({"return_cause_id": self.return_cause.id})
        self.assertEqual(order.return_cause_date, fields.Date.today())

    def test_03_calculate_return_amount(self):
        """Test check_and_update_return_amount method"""
        # Create Sale Order
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "return_cause_id": self.return_cause.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        order.action_confirm()

        # Create Invoice
        invoice = order._create_invoices()
        invoice.action_post()

        # Manually set return_cause because Odoo might not have it in the invoice
        # But wait, the logic uses order.invoice_ids.filtered(lambda x: x.move_type == 'out_refund'...)

        # Create Credit Note (Refund)
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "date": fields.Date.today(),
                    "reason": "Test Refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal_res = move_reversal.refund_moves()
        credit_note = self.env["account.move"].browse(reversal_res["res_id"])
        credit_note.action_post()

        # Check return amount
        order.check_and_update_return_amount()

        # amount_total_signed for out_refund is negative in Odoo
        # Let's check the code logic:
        # total_credit_amount = sum(credit_notes.mapped(lambda x: x.amount_total_signed))
        # order.return_amount = total_credit_amount

        self.assertNotEqual(order.return_amount, 0.0)
        self.assertEqual(order.return_amount, credit_note.amount_total_signed)

    def test_04_cron_check_and_update_return_amount(self):
        """Test cron method"""
        # Create SO with cause
        self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "return_cause_id": self.return_cause.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )
        # Set config parameter to True
        self.env["ir.config_parameter"].sudo().set_param("deltatech_sale_return_cause.auto_calculate", "True")

        # Just call the cron method to see if it runs without error
        self.env["sale.order"]._cron_check_and_update_return_amount()
