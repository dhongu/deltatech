# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestSaleMarginReportPos(TestPoSCommon):
    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.env.user.group_ids |= self.env.ref("sales_team.group_sale_manager")
        self.product = self.create_product("Margin POS", self.categ_basic, 100, 60)
        self.open_new_session()

    def _order(self, qty, is_invoiced=False):
        orders = self._create_orders(
            [
                {
                    "pos_order_lines_ui_args": [(self.product, qty)],
                    "payments": [(self.cash_pm1, 100 * qty)],
                    "customer": self.customer,
                    "is_invoiced": is_invoiced,
                }
            ]
        )
        self.env.flush_all()
        return next(iter(orders.values()))

    def _rows(self, **domain):
        return self.env["sale.margin.report"].search(
            [("product_id", "=", self.product.id)] + [(name, "=", value) for name, value in domain.items()]
        )

    def test_order_without_invoice(self):
        order = self._order(2)
        row = self._rows(pos_order_id=order.id)
        self.assertEqual(len(row), 1)
        self.assertLess(row.id, 0)
        self.assertFalse(row.invoice_id)
        self.assertAlmostEqual(row.product_uom_qty, 2)
        self.assertAlmostEqual(row.sale_val, 200)
        # session still open: the current cost of the product
        self.assertAlmostEqual(row.stock_val, 120)
        self.assertAlmostEqual(row.profit_val, 80)
        self.assertAlmostEqual(row.purchase_price, 60)
        self.assertEqual(row.journal_id, self.config.journal_id)
        self.assertEqual(row.payment_state, "paid")
        self.assertEqual(row.user_id, order.user_id)

    def test_storable_column(self):
        """The POS rows say whether the product is storable, for the default filter of the report."""
        order = self._order(1)
        self.assertTrue(self.product.is_storable)
        row = self._rows(pos_order_id=order.id, is_storable=True)
        self.assertEqual(len(row), 1)
        self.product.is_storable = False
        self.env.flush_all()
        self.assertFalse(self._rows(pos_order_id=order.id, is_storable=True))
        self.assertEqual(len(self._rows(pos_order_id=order.id, is_storable=False)), 1)

    def test_invoiced_order_not_counted_twice(self):
        order = self._order(1, is_invoiced=True)
        self.assertTrue(order.account_move)
        self.assertFalse(self._rows(pos_order_id=order.id))
        row = self._rows(invoice_id=order.account_move.id)
        self.assertEqual(len(row), 1)
        self.assertGreater(row.id, 0)
        self.assertFalse(row.pos_order_id)
        self.assertAlmostEqual(row.sale_val, 100)

    def test_return_is_negative(self):
        order = self._order(-1)
        row = self._rows(pos_order_id=order.id)
        self.assertAlmostEqual(row.sale_val, -100)
        self.assertAlmostEqual(row.stock_val, -60)
        self.assertAlmostEqual(row.profit_val, -40)

    def test_cost_after_closing(self):
        order = self._order(1)
        self.pos_session.post_closing_cash_details(100)
        self.pos_session.close_session_from_ui()
        line = order.lines
        self.assertTrue(line.is_total_cost_computed)
        self.env.invalidate_all()
        row = self._rows(pos_order_id=order.id)
        self.assertAlmostEqual(row.stock_val, line.total_cost)

    def test_commission_rate_of_the_pos_journal(self):
        if "commission.users" not in self.env:
            self.skipTest("deltatech_sale_commission is not installed")
        self.env.user.group_ids |= self.env.ref("deltatech_sale_commission.group_commission_manager")
        self.env["commission.users"].create(
            {"user_id": self.env.user.id, "journal_id": self.config.invoice_journal_id.id, "rate": 0.1}
        )
        order = self._order(2)
        row = self._rows(pos_order_id=order.id)
        self.assertEqual(row.user_id, self.env.user)
        self.assertAlmostEqual(row.commission_computed, 8)

    def test_order_rows_read_only(self):
        order = self._order(1)
        row = self._rows(pos_order_id=order.id)
        with self.assertRaises(UserError):
            row.write({"purchase_price": 5})
        self.assertFalse(row._invoice_rows())

    def _invoiced_return(self, qty=2, **refund_line_vals):
        """Receipt (not invoiced) of ``qty`` pieces, then a return of the whole order invoiced."""
        order = self._order(qty)
        refund = self.env["pos.order"].browse(order.refund()["res_id"])
        refund.lines.write(refund_line_vals)
        refund.to_invoice = True
        context = {"active_ids": refund.ids, "active_id": refund.id}
        payment = self.env["pos.make.payment"].with_context(**context).create({"payment_method_id": self.cash_pm1.id})
        payment.with_context(**context).check()
        self.assertTrue(refund.account_move)
        return refund

    def test_invoiced_return_of_a_receipt_has_the_cost(self):
        """The credit note of a return of a receipt reverses no invoice: the cost comes from the POS."""
        refund = self._invoiced_return()
        credit_note = refund.account_move
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertFalse(credit_note.reversed_entry_id)
        self.assertTrue(refund.lines.is_total_cost_computed)
        line = credit_note.invoice_line_ids.filtered("product_id")
        self.assertAlmostEqual(line.purchase_price, 60)
        # the refresh of the cost from the documents (wizard, cron) gives the same cost
        self.assertAlmostEqual(line._purchase_price_from_document(), 60)
        self.env.flush_all()
        row = self._rows(invoice_id=credit_note.id)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.stock_val, -120)

    def test_invoiced_return_unit_of_measure(self):
        """The cost is per unit of the invoice line, not of the product."""
        refund = self._invoiced_return()
        line = refund.account_move.invoice_line_ids.filtered("product_id")
        dozen = self.env.ref("uom.product_uom_dozen")
        line.product_uom_id = dozen
        self.assertAlmostEqual(line._get_refund_purchase_price_from_invoice(), 60 * 12)
