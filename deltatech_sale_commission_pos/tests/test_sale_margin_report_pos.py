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
        self.env.user.group_ids |= self.env.ref("deltatech_sale_commission.group_commission_manager")
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
        self.env["commission.users"].create(
            {"user_id": self.env.user.id, "journal_id": self.config.journal_id.id, "rate": 0.1}
        )
        order = self._order(2)
        row = self._rows(pos_order_id=order.id)
        self.assertEqual(row.user_id, self.env.user)
        self.assertAlmostEqual(row.commission_computed, 8)

    def test_order_rows_read_only(self):
        order = self._order(1)
        row = self._rows(pos_order_id=order.id)
        with self.assertRaises(UserError):
            row.write({"commission": 5})
        # Set Paid leaves the order rows out instead of failing
        row.action_set_commission_paid()
        self.assertFalse(row._invoice_rows())
