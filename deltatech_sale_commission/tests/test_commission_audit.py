# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Regression tests for the defects found by the consultant sheet audit
# (readme/FISA_CONSULTANT.md, "Limitări cunoscute").

import importlib.util
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
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
    def _invoice(self, qty=10):
        so = self._create_and_confirm_sale(qty_a=qty, qty_b=0)
        self._validate_picking(so.picking_ids)
        return so, self._create_invoice(so)

    def _draft_refund(self, invoice):
        refund = invoice._reverse_moves()
        return refund, refund.invoice_line_ids.filtered(lambda line: line.product_id == self.product_a)

    def _refund(self, invoice):
        refund, line = self._draft_refund(invoice)
        refund.action_post()
        return line

    def _invoice_cost(self, invoice):
        return invoice.invoice_line_ids.filtered(lambda line: line.product_id == self.product_a).purchase_price

    def _report(self, line):
        self.env.flush_all()
        return self.env["sale.margin.report"].search([("id", "=", line.id)])

    def _update_and_cron(self, report_line):
        self.env["commission.update.purchase.price"].with_context(active_ids=report_line.ids).create({}).do_compute()
        self.env["sale.margin.report"].cron_update_purchase_price()

    def test_reversal_keeps_invoice_cost(self):
        """A reversal cancels the sale: same cost as the invoice, zero profit on the pair."""
        _so, invoice = self._invoice()
        refund_line = self._refund(invoice)
        self.assertAlmostEqual(refund_line.purchase_price, self._invoice_cost(invoice))
        self.assertAlmostEqual(refund_line.get_purchase_price(), self._invoice_cost(invoice))
        self.env.flush_all()
        lines = self.env["sale.margin.report"].search([("invoice_id", "in", (invoice | refund_line.move_id).ids)])
        self.assertAlmostEqual(sum(lines.mapped("profit_val")), 0.0)
        # the update wizard and the daily cron keep it
        self._update_and_cron(self._report(refund_line))
        self.assertAlmostEqual(refund_line.purchase_price, self._invoice_cost(invoice))

    def test_partial_reversal_keeps_unit_cost(self):
        _so, invoice = self._invoice()
        refund, refund_line = self._draft_refund(invoice)
        refund_line.quantity = 3
        refund.action_post()
        self.assertAlmostEqual(refund_line.purchase_price, self._invoice_cost(invoice))

    def test_price_reduction_has_no_cost(self):
        """A credit note on the price only: nothing comes back, the cost is 0."""
        _so, invoice = self._invoice()
        refund, refund_line = self._draft_refund(invoice)
        refund_line.price_unit = 20.0
        refund.action_post()
        self.assertEqual(refund_line.purchase_price, 0.0)
        self.assertEqual(refund_line.get_purchase_price(), 0.0)
        report_line = self._report(refund_line)
        self.assertEqual(report_line.stock_val, 0.0)
        self.assertLess(report_line.profit_val, 0.0)
        # neither the update wizard nor the daily cron bring a cost back
        self._update_and_cron(report_line)
        self.assertEqual(refund_line.purchase_price, 0.0)

    def test_discount_credit_note_has_no_cost(self):
        _so, invoice = self._invoice()
        refund, refund_line = self._draft_refund(invoice)
        refund_line.discount = 10.0
        refund.action_post()
        self.assertEqual(refund_line.purchase_price, 0.0)

    def test_wizard_resets_a_wrong_refund_cost_but_the_cron_does_not(self):
        """The wizard is an explicit action and resets the cost to 0; the cron only fills in.

        Both read the same rule (account.move.line._purchase_price_from_document); they differ on
        what they do with the 0 it gives on a credit note. The cron runs unattended over a whole
        week of invoicing, so it must not undo a cost a manager put in by hand.
        """
        _so, invoice = self._invoice()
        refund, refund_line = self._draft_refund(invoice)
        refund_line.price_unit = 20.0  # a price reduction: no cost of its own
        refund.action_post()
        self.assertEqual(refund_line._purchase_price_from_document(), 0.0)

        # a cost put in by hand, as on a return that was never recorded in stock
        refund_line.purchase_price = 75.0
        report_line = self._report(refund_line)

        self.env["sale.margin.report"].cron_update_purchase_price()
        self.assertEqual(refund_line.purchase_price, 75.0, "the cron must not undo a manual cost")

        self.env["commission.update.purchase.price"].with_context(active_ids=report_line.ids).create({}).do_compute()
        self.assertEqual(refund_line.purchase_price, 0.0, "the wizard resets the cost of a price reduction")

    def test_invoice_without_a_document_cost_keeps_its_own(self):
        """On an invoice a 0 is a missing value, not an answer: the stored cost stays."""
        _so, invoice = self._invoice()
        line = invoice.invoice_line_ids.filtered(lambda line: line.product_id == self.product_a)
        self.product_a.standard_price = 0.0
        line.sale_line_ids = [(5, 0, 0)]  # no delivery left to read a cost from
        line.purchase_price = 42.0
        self.assertIsNone(line._purchase_price_from_document())
        self._update_and_cron(self._report(line))
        self.assertEqual(line.purchase_price, 42.0)

    def test_refund_with_return_takes_returned_cost(self):
        so, invoice = self._invoice()
        delivery = so.picking_ids
        wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=delivery.id, active_model="stock.picking")
            .create({})
        )
        wizard.product_return_moves.quantity = 10
        self._validate_picking(wizard._create_return())

        refund_line = self._refund(invoice)
        self.assertAlmostEqual(refund_line.get_purchase_price(), 100.0)
        self._update_and_cron(self._report(refund_line))
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

    def _drop_unique_index(self):
        # as on a database upgraded with duplicates left: the unique index could not be created
        self.env.flush_all()
        self.env.cr.execute(
            "ALTER TABLE commission_users DROP CONSTRAINT IF EXISTS commission_users_user_journal_company_unique"
        )
        self.env.cr.execute("DROP INDEX IF EXISTS commission_users_user_journal_company_unique")

    def test_orm_refuses_duplicate_without_index(self):
        journal = self.company_data["default_journal_sale"]
        vals = {"user_id": self.env.user.id, "rate": 0.1, "journal_id": journal.id}
        self.env["commission.users"].create(vals)
        self._drop_unique_index()
        with self.assertRaises(ValidationError):
            self.env["commission.users"].create(vals)
        other = self.env["commission.users"].create(dict(vals, user_id=self.vendor_user().id))
        with self.assertRaises(ValidationError):
            other.user_id = self.env.user

    def vendor_user(self):
        return new_test_user(self.env, "commission.other", groups="sales_team.group_sale_salesman")

    def test_company_must_be_the_one_of_the_journal(self):
        """A rate filed under another company matches no invoice: the report joins on the company
        too, so the salesperson would quietly get nothing."""
        journal = self.company_data["default_journal_sale"]
        other_company = self.env["res.company"].create({"name": "Other Commission Co"})
        with self.assertRaises(ValidationError):
            self.env["commission.users"].create(
                {
                    "user_id": self.env.user.id,
                    "rate": 0.1,
                    "journal_id": journal.id,
                    "company_id": other_company.id,
                }
            )

    def test_report_not_multiplied_by_duplicate_rates(self):
        """Duplicates left in the data must not double the report: one line per invoice line,
        with the sale value of the line, and the rate of the oldest row."""
        journal = self.company_data["default_journal_sale"]
        so = self._create_and_confirm_sale(qty_a=10, qty_b=5)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        self.assertEqual(invoice.journal_id, journal)
        self.env["commission.users"].create({"user_id": self.env.user.id, "rate": 0.1, "journal_id": journal.id})
        self._drop_unique_index()
        for rate in (0.1, 0.3):  # an exact duplicate and one with a different rate
            self.env.cr.execute(
                "INSERT INTO commission_users (user_id, rate, company_id, journal_id) VALUES (%s, %s, %s, %s)",
                (self.env.user.id, rate, self.env.company.id, journal.id),
            )
        self.env.invalidate_all()
        product_lines = invoice.invoice_line_ids.filtered(lambda line: line.display_type == "product")
        lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.env.cr.execute(
            "SELECT COUNT(*), COUNT(DISTINCT id) FROM sale_margin_report WHERE invoice_id = %s", invoice.ids
        )
        self.assertEqual(self.env.cr.fetchone(), (len(product_lines), len(product_lines)))
        for line in lines:
            invoice_line = product_lines.filtered(lambda aml, line=line: aml.id == line.id)
            self.assertAlmostEqual(line.sale_val, -invoice_line.balance)
            self.assertAlmostEqual(line.commission_computed, 0.1 * line.profit_val)

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


@tagged("post_install", "-at_install")
class TestMigrationCommissionUsers(TestSaleCommissionBase):
    """pre-migration 19.0.1.6.0, run on rows written as the previous version allowed them"""

    @classmethod
    def _migration(cls):
        path = Path(__file__).parents[1] / "migrations" / "19.0.1.6.0" / "pre-migration.py"
        spec = importlib.util.spec_from_file_location("deltatech_sale_commission_pre_1_6_0", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _journal(self, company, code):
        return (
            self.env["account.journal"]
            .sudo()
            .create({"name": f"Sales {code}", "code": code, "type": "sale", "company_id": company.id})
        )

    def _insert(self, user, company, journal=None):
        self.env.cr.execute(
            "INSERT INTO commission_users (user_id, rate, company_id, journal_id) VALUES (%s, 0.1, %s, %s) RETURNING id",
            (user.id, company.id, journal.id if journal else None),
        )
        return self.env.cr.fetchone()[0]

    def _journal_of(self, row_id):
        self.env.cr.execute("SELECT journal_id FROM commission_users WHERE id = %s", (row_id,))
        return self.env.cr.fetchone()[0]

    def test_fill_journal_without_duplicates(self):
        single = self.env["res.company"].create({"name": "Single Journal Co"})
        several = self.env["res.company"].create({"name": "Several Journals Co"})
        # new companies without a chart of accounts: only the journals created here
        self.env["account.journal"].sudo().search([("company_id", "in", (single | several).ids)]).unlink()
        journal = self._journal(single, "SJ1")
        self._journal(several, "MJ1")
        self._journal(several, "MJ2")
        users = [new_test_user(self.env, f"mig.user{i}", groups="sales_team.group_sale_salesman") for i in range(5)]
        self.env.flush_all()
        # the version being upgraded had neither the NOT NULL nor the unique constraint
        self.env.cr.execute("ALTER TABLE commission_users ALTER COLUMN journal_id DROP NOT NULL")
        self.env.cr.execute(
            "ALTER TABLE commission_users DROP CONSTRAINT IF EXISTS commission_users_user_journal_company_unique"
        )
        self.env.cr.execute("DROP INDEX IF EXISTS commission_users_user_journal_company_unique")

        # a row on the journal plus a row without journal: filling it would duplicate the first one
        existing = self._insert(users[0], single, journal)
        conflict = self._insert(users[0], single)
        # two rows without journal: only the first one is filled
        first = self._insert(users[1], single)
        second = self._insert(users[1], single)
        # one row without journal
        alone = self._insert(users[2], single)
        # a company with two sales journals: nothing to choose from
        ambiguous = self._insert(users[3], several)

        # on the journal already: an exact duplicate (deleted) and one with another rate (kept)
        base = self._insert(users[4], single, journal)
        exact = self._insert(users[4], single, journal)
        different = self._insert(users[4], single, journal)
        self.env.cr.execute("UPDATE commission_users SET rate = 0.5 WHERE id = %s", (different,))

        with self.assertLogs("deltatech_sale_commission_pre_1_6_0", "WARNING") as logs:
            self._migration().migrate(self.env.cr, "19.0.1.5.2")

        self.assertEqual(self._journal_of(existing), journal.id)
        self.assertIsNone(self._journal_of(conflict))
        self.assertEqual(self._journal_of(first), journal.id)
        self.assertIsNone(self._journal_of(second))
        self.assertEqual(self._journal_of(alone), journal.id)
        self.assertIsNone(self._journal_of(ambiguous))
        # the exact copy goes, the copy with another rate stays for the user to decide
        self.env.cr.execute("SELECT id FROM commission_users WHERE id IN %s ORDER BY id", ((base, exact, different),))
        self.assertEqual([row[0] for row in self.env.cr.fetchall()], [base, different])
        self.env.cr.execute(
            """SELECT ARRAY_AGG(id ORDER BY id) FROM commission_users WHERE journal_id IS NOT NULL
                GROUP BY user_id, journal_id, company_id HAVING COUNT(*) > 1"""
        )
        self.assertEqual([row[0] for row in self.env.cr.fetchall()], [[base, different]])
        output = "\n".join(logs.output)
        self.assertIn(str(sorted([first, alone])), output)
        self.assertIn(str(sorted([conflict, second, ambiguous])), output)
        self.assertIn(f"exact duplicate rows {[exact]} deleted", output)
        self.assertIn(str([base, different]), output)

    def _company_of(self, row_id):
        self.env.cr.execute("SELECT company_id FROM commission_users WHERE id = %s", (row_id,))
        return self.env.cr.fetchone()[0]

    def test_company_realigned_on_the_journal(self):
        """The report now matches on the company too. A row filed under another company applied
        before the upgrade and would stop applying after it, so the migration moves it onto the
        company of its journal — unless that would make it a duplicate."""
        owner = self.env["res.company"].create({"name": "Journal Owner Co"})
        stranger = self.env["res.company"].create({"name": "Stranger Co"})
        self.env["account.journal"].sudo().search([("company_id", "in", (owner | stranger).ids)]).unlink()
        journal = self._journal(owner, "OWN1")
        users = [new_test_user(self.env, f"mig.comp{i}", groups="sales_team.group_sale_salesman") for i in range(2)]
        self.env.flush_all()
        self.env.cr.execute("ALTER TABLE commission_users ALTER COLUMN journal_id DROP NOT NULL")
        self.env.cr.execute(
            "ALTER TABLE commission_users DROP CONSTRAINT IF EXISTS commission_users_user_journal_company_unique"
        )
        self.env.cr.execute("DROP INDEX IF EXISTS commission_users_user_journal_company_unique")

        # filed under the wrong company, and nothing in the way: moved
        movable = self._insert(users[0], stranger, journal)
        # the right company already has a row for this salesperson and journal: left alone
        blocked = self._insert(users[1], stranger, journal)
        self._insert(users[1], owner, journal)

        with self.assertLogs("deltatech_sale_commission_pre_1_6_0", "WARNING") as logs:
            self._migration().migrate(self.env.cr, "19.0.1.5.2")

        self.assertEqual(self._company_of(movable), owner.id)
        self.assertEqual(self._company_of(blocked), stranger.id)
        output = "\n".join(logs.output)
        self.assertIn(f"rows {[movable]} moved to the company of their journal", output)
        self.assertIn(f"rows {[blocked]} are not on the company of their journal", output)
