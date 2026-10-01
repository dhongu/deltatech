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
                "type": "consu",
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
        self.env["ir.config_parameter"].sudo().set_bool("deltatech_sale_return_cause.auto_calculate", True)

        # Just call the cron method to see if it runs without error
        self.env["sale.order"]._cron_check_and_update_return_amount()

    def _create_order(self, **vals):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0, "price_unit": 100.0})],
                **vals,
            }
        )

    def _invoice_and_refund(self, order, refund_price):
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.action_post()
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({"date": fields.Date.today(), "reason": "Test Refund", "journal_id": invoice.journal_id.id})
        )
        credit_note = self.env["account.move"].browse(move_reversal.refund_moves()["res_id"])
        credit_note.invoice_line_ids.price_unit = refund_price
        credit_note.action_post()
        return credit_note

    def test_05_bulk_write_mixed_dates(self):
        """RETURNCAUSE-001: bulk write keeps existing dates and fills only the missing ones"""
        old_date = fields.Date.add(fields.Date.today(), days=-10)
        order_with_date = self._create_order(return_cause_date=old_date)
        order_without_date = self._create_order()
        orders = order_with_date | order_without_date
        orders.write({"return_cause_id": self.return_cause.id})
        self.assertEqual(order_with_date.return_cause_date, old_date)
        self.assertEqual(order_without_date.return_cause_date, fields.Date.today())
        self.assertEqual(orders.return_cause_id, self.return_cause)

    def test_06_write_explicit_date_is_kept(self):
        """RETURNCAUSE-001: an explicit return_cause_date in vals is not replaced with today"""
        explicit_date = fields.Date.add(fields.Date.today(), days=-5)
        order = self._create_order()
        order.write({"return_cause_id": self.return_cause.id, "return_cause_date": explicit_date})
        self.assertEqual(order.return_cause_date, explicit_date)
        orders = self._create_order() | self._create_order()
        orders.write({"return_cause_id": self.return_cause.id, "return_cause_date": explicit_date})
        self.assertEqual(orders.mapped("return_cause_date"), [explicit_date, explicit_date])

    def test_07_bulk_return_amount(self):
        """RETURNCAUSE-001: multi-order recalculation uses each order's own credit notes"""
        order_1 = self._create_order(return_cause_id=self.return_cause.id)
        order_2 = self._create_order(return_cause_id=self.return_cause.id)
        order_3 = self._create_order()
        credit_1 = self._invoice_and_refund(order_1, 30.0)
        credit_2 = self._invoice_and_refund(order_2, 70.0)
        self._invoice_and_refund(order_3, 50.0)
        (order_1 | order_2 | order_3).check_and_update_return_amount()
        self.assertEqual(order_1.return_amount, credit_1.amount_total_signed)
        self.assertEqual(order_2.return_amount, credit_2.amount_total_signed)
        self.assertNotEqual(order_1.return_amount, order_2.return_amount)
        self.assertEqual(order_3.return_amount, 0.0)
