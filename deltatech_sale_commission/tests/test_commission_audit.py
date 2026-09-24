# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Regression tests for the defects found by the consultant sheet audit
# (readme/FISA_CONSULTANT.md, "Limitări cunoscute").

from datetime import timedelta
from types import SimpleNamespace

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from .test_sale import TestSaleCommissionBase


@tagged("post_install", "-at_install")
class TestCommissionAccess(TestSaleCommissionBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        common = {"company_id": company.id, "company_ids": [(6, 0, company.ids)]}
        # a commission manager with the sales role only: no right to write invoice lines
        cls.commission_manager = new_test_user(
            cls.env,
            "commission.manager",
            groups="sales_team.group_sale_salesman,deltatech_sale_commission.group_commission_manager",
            **common,
        )
        cls.commission_viewer = new_test_user(
            cls.env,
            "commission.viewer",
            groups="sales_team.group_sale_salesman,deltatech_sale_commission.group_commission_viewer",
            **common,
        )
        cls.salesman = new_test_user(cls.env, "commission.salesman", groups="sales_team.group_sale_salesman", **common)

    def _invoice_report_lines(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        self.env.flush_all()
        return invoice, self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])

    def test_compute_commission_manager_without_invoicing_right(self):
        self.env["ir.config_parameter"].sudo().set_param("deltatech_sale_commission.days_for_commission", "")
        invoice, lines = self._invoice_report_lines()
        self.assertFalse(self.commission_manager.has_group("account.group_account_invoice"))
        wizard = (
            self.env["commission.compute"]
            .with_user(self.commission_manager)
            .with_context(active_ids=lines.ids)
            .create({})
        )
        wizard.do_compute()
        invoice_lines = self.env["account.move.line"].browse(lines.ids)
        for report_line, invoice_line in zip(lines, invoice_lines, strict=True):
            self.assertAlmostEqual(invoice_line.commission, report_line.commission_computed)

    def test_compute_wizard_refused_to_salesman(self):
        with self.assertRaises(AccessError):
            self.env["commission.compute"].with_user(self.salesman).create({})

    def test_update_purchase_price_wizard_refused_to_viewer(self):
        with self.assertRaises(AccessError):
            self.env["commission.update.purchase.price"].with_user(self.commission_viewer).create({"for_all": True})
        with self.assertRaises(AccessError):
            self.env["commission.update.purchase.price"].with_user(self.salesman).create({})

    def test_viewer_can_not_write_report(self):
        _invoice, lines = self._invoice_report_lines()
        with self.assertRaises(AccessError):
            lines.with_user(self.commission_viewer).write({"commission": 5.0})
        with self.assertRaises(AccessError):
            lines.with_user(self.commission_viewer).action_set_commission_paid()
        self.assertFalse(any(self.env["account.move.line"].browse(lines.ids).mapped("commission_paid")))

    def test_manager_write_report(self):
        _invoice, lines = self._invoice_report_lines()
        lines.with_user(self.commission_manager).write({"commission": 12.5, "commission_paid": True})
        invoice_lines = self.env["account.move.line"].browse(lines.ids)
        self.assertEqual(invoice_lines.mapped("commission"), [12.5] * len(lines))
        self.assertTrue(all(invoice_lines.mapped("commission_paid")))
        # the report reads the new values back
        self.assertTrue(all(lines.mapped("commission_paid")))

    def test_write_keeps_zero_cost(self):
        _invoice, lines = self._invoice_report_lines()
        invoice_lines = self.env["account.move.line"].browse(lines.ids)
        invoice_lines.write({"purchase_price": 0.0})
        lines.with_user(self.commission_manager).action_set_commission_paid()
        self.assertEqual(invoice_lines.mapped("purchase_price"), [0.0] * len(lines))
        self.assertTrue(all(invoice_lines.mapped("commission_paid")))


@tagged("post_install", "-at_install")
class TestRefundPurchasePrice(TestSaleCommissionBase):
    def _refund(self, invoice):
        refund = invoice._reverse_moves()
        refund.action_post()
        return refund.invoice_line_ids.filtered(lambda line: line.product_id == self.product_a)

    def test_value_only_refund_has_no_cost(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        refund_line = self._refund(invoice)
        self.assertEqual(refund_line.purchase_price, 0.0)
        self.assertEqual(refund_line.get_purchase_price(), 0.0)
        self.env.flush_all()
        report_line = self.env["sale.margin.report"].search([("id", "=", refund_line.id)])
        self.assertEqual(report_line.stock_val, 0.0)
        self.assertLess(report_line.profit_val, 0.0)

        # neither the update wizard nor the daily cron bring the product cost back
        self.env["commission.update.purchase.price"].with_context(active_ids=report_line.ids).create({}).do_compute()
        self.env["sale.margin.report"].cron_update_purchase_price()
        self.assertEqual(refund_line.purchase_price, 0.0)

    def test_refund_with_return_takes_returned_cost(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        delivery = so.picking_ids
        self._validate_picking(delivery)
        invoice = self._create_invoice(so)

        wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=delivery.id, active_model="stock.picking")
            .create({})
        )
        wizard.product_return_moves.quantity = 10
        self._validate_picking(wizard._create_return())

        refund_line = self._refund(invoice)
        self.assertAlmostEqual(refund_line.purchase_price, 100.0)


@tagged("post_install", "-at_install")
class TestCommissionUsersConstraints(TestSaleCommissionBase):
    def test_journal_required(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.env["commission.users"].create({"user_id": self.env.user.id, "rate": 0.1})
            self.env.flush_all()

    def test_unique_user_journal_company(self):
        journal = self.company_data["default_journal_sale"]
        vals = {"user_id": self.env.user.id, "rate": 0.1, "journal_id": journal.id}
        self.env["commission.users"].create(vals)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.env["commission.users"].create(vals)
            self.env.flush_all()

    def test_report_lines_not_duplicated(self):
        journal = self.company_data["default_journal_sale"]
        self.env["commission.users"].create({"user_id": self.env.user.id, "rate": 0.1, "journal_id": journal.id})
        so = self._create_and_confirm_sale(qty_a=10, qty_b=5)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        self.assertEqual(invoice.journal_id, journal)
        self.env.flush_all()
        lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertEqual(len(lines), 2)
        self.assertEqual(len(set(lines.ids)), 2)
        line_a = lines.filtered(lambda line: line.product_id == self.product_a)
        self.assertAlmostEqual(line_a.commission_computed, 0.1 * line_a.profit_val)


@tagged("post_install", "-at_install")
class TestSettingsRebuildReport(TestSaleCommissionBase):
    def _view_definition(self):
        self.env.cr.execute("SELECT pg_get_viewdef('sale_margin_report'::regclass)")
        return self.env.cr.fetchone()[0]

    def test_report_rebuilt_after_save(self):
        self.env["res.config.settings"].create({"sale_user_detail": "invoice"}).execute()
        self.assertNotIn("sale_user_id", self._view_definition())
        self.env["res.config.settings"].create({"sale_user_detail": "sale"}).execute()
        self.assertIn("sale_user_id", self._view_definition())
        self.env["res.config.settings"].create({"sale_user_detail": "invoice"}).execute()
        self.assertNotIn("sale_user_id", self._view_definition())


@tagged("post_install", "-at_install")
class TestCommissionPaymentRules(TestSaleCommissionBase):
    def _set_days(self, value):
        self.env["ir.config_parameter"].sudo().set_param("deltatech_sale_commission.days_for_commission", value)

    def _get_days(self, value):
        self._set_days(value)
        return self.env["commission.compute"]._get_days_for_commission()

    def _line(self, payment_state, days_late=None, move_type="out_invoice", commission=100.0):
        due = self.env.cr.now().date()
        payments = False
        if days_late is not None:
            payments = {"content": [{"date": due + timedelta(days=days_late)}]}
        invoice = SimpleNamespace(
            move_type=move_type,
            payment_state=payment_state,
            invoice_payments_widget=payments,
            invoice_date_due=due,
        )
        return SimpleNamespace(invoice_id=invoice, commission_computed=commission)

    def test_days_parameter(self):
        self.assertIsNone(self._get_days(""))
        self.assertEqual(self._get_days("0"), 0)
        self.assertEqual(self._get_days("10"), 10)
        self._set_days("ten")
        with self.assertRaises(UserError):
            self.env["commission.compute"]._get_days_for_commission()
        self._set_days("-1")
        with self.assertRaises(UserError):
            self.env["commission.compute"]._get_days_for_commission()

    def test_line_commission(self):
        compute = self.env["commission.compute"]
        # no limit: the computed commission, whatever the payment
        self.assertEqual(compute._get_line_commission(self._line("not_paid"), None), 100.0)
        # "in payment" is a received payment, not yet matched with the bank statement
        self.assertEqual(compute._get_line_commission(self._line("in_payment", 3), 10), 100.0)
        self.assertEqual(compute._get_line_commission(self._line("in_payment", 20), 10), 0.0)
        self.assertEqual(compute._get_line_commission(self._line("paid", 3), 10), 100.0)
        self.assertEqual(compute._get_line_commission(self._line("not_paid"), 10), 0.0)
        self.assertEqual(compute._get_line_commission(self._line("partial", 1), 10), 0.0)
        # 0 days: paid at the latest on the due date, not "no limit"
        self.assertEqual(compute._get_line_commission(self._line("paid", 0), 0), 100.0)
        self.assertEqual(compute._get_line_commission(self._line("paid", 1), 0), 0.0)
        self.assertEqual(compute._get_line_commission(self._line("paid", -2), 0), 100.0)
        # credit notes always keep their (negative) commission
        refund = self._line("not_paid", move_type="out_refund", commission=-40.0)
        self.assertEqual(compute._get_line_commission(refund, 0), -40.0)

    def test_default_lines_without_selection(self):
        self._set_days("")
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        self.env["account.payment.register"].with_context(active_model="account.move", active_ids=invoice.ids).create(
            {}
        )._create_payments()
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        self.env.flush_all()
        lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        wizard = self.env["commission.compute"].create({})
        self.assertTrue(lines)
        self.assertLessEqual(lines, wizard.invoice_line_ids)
        wizard = self.env["commission.update.purchase.price"].create({})
        self.assertLessEqual(lines, wizard.invoice_line_ids)
