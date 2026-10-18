from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestPosChangeReconcile(TestPoSCommon):
    """Factură POS plătită în numerar cu rest, când contul de creanțe POS
    este același cu contul de creanțe al clientului (4111 în planul RO)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        cls.company.account_default_pos_receivable_account_id = cls.receivable_account
        cls.customer.property_account_receivable_id = cls.receivable_account
        cls.product = cls.create_product("Produs rest", cls.categ_basic, 298.5)

    def _create_invoiced_order_with_change(self):
        order_data = self.create_ui_order_data(
            [(self.product, 1)],
            customer=self.customer,
            is_invoiced=True,
            payments=[(self.cash_pm1, 300.0)],
        )
        order_data["amount_return"] = -1.5
        order_id = self.env["pos.order"].sync_from_ui([order_data])["pos.order"][0]["id"]
        return self.env["pos.order"].browse(order_id)

    def _assert_invoice_paid(self, invoice, payment_moves):
        self.assertEqual(invoice.payment_state, "paid")
        self.assertTrue(invoice.currency_id.is_zero(invoice.amount_residual))
        credit_line = payment_moves.line_ids.filtered(lambda line: line.balance < 0)
        invoice_line = invoice.line_ids.filtered(lambda line: line.account_id == self.receivable_account)
        self.assertIn(credit_line, invoice_line.matched_credit_ids.credit_move_id)

    def test_invoice_paid_with_cash_change(self):
        self.open_new_session()
        order = self._create_invoiced_order_with_change()
        self.assertRecordValues(
            order.payment_ids.sorted("amount"),
            [{"amount": -1.5, "is_change": True}, {"amount": 300.0, "is_change": False}],
        )
        invoice = order.account_move
        payment_moves = order.payment_ids.account_move_id
        self.assertEqual(len(payment_moves), 1)
        self.assertEqual(payment_moves.amount_total, 298.5)
        self._assert_invoice_paid(invoice, payment_moves)

        self.pos_session.post_closing_cash_details(self.pos_session.cash_register_balance_end_real)
        self.pos_session.close_session_from_ui()
        self.assertEqual(self.pos_session.state, "closed")
        self._assert_invoice_paid(invoice, payment_moves)
        debit_line = payment_moves.line_ids.filtered(lambda line: line.balance > 0)
        self.assertTrue(debit_line.reconciled)
        self.assertEqual(
            debit_line.full_reconcile_id.reconciled_line_ids.move_id - payment_moves, self.pos_session.move_id
        )

    def test_invoice_paid_without_change(self):
        """Fără rest selecția era deja corectă; rămâne neschimbată."""
        self.open_new_session()
        order_data = self.create_ui_order_data(
            [(self.product, 1)],
            customer=self.customer,
            is_invoiced=True,
            payments=[(self.cash_pm1, 298.5)],
        )
        order_id = self.env["pos.order"].sync_from_ui([order_data])["pos.order"][0]["id"]
        order = self.env["pos.order"].browse(order_id)
        self._assert_invoice_paid(order.account_move, order.payment_ids.account_move_id)
