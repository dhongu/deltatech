# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved


from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentForecastBugs(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids = [(4, cls.env.ref("deltatech_payment_forecast.payment_forecast_manager").id)]
        cls.company_a = cls.company_data["company"]
        cls.company_data_2 = cls.setup_other_company()
        cls.company_b = cls.company_data_2["company"]
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company_a.id, cls.company_b.id]))
        cls.foreign_currency = cls.setup_other_currency("EUR")
        cls.today = fields.Date.today()

    @classmethod
    def _create_invoice(cls, company, amount, invoice_date=None, currency=None):
        invoice_date = invoice_date or cls.today
        vals = {
            "move_type": "out_invoice",
            "partner_id": cls.partner_a.id,
            "invoice_date": invoice_date,
            "invoice_date_due": invoice_date,
            "invoice_line_ids": [Command.create({"name": "Test", "quantity": 1, "price_unit": amount, "tax_ids": []})],
        }
        if currency:
            vals["currency_id"] = currency.id
        invoice = cls.env["account.move"].with_company(company).create(vals)
        invoice.action_post()
        return invoice

    def _run_wizard(self, company):
        wizard = self.env["payment.forecast.wizard"].create({"date_to": self.today, "company_id": company.id})
        wizard.get_forecast_lines()
        return self.env["payment.forecast"].search([("days", "=", "Custom")])

    def test_forecast_001_company_currency_label(self):
        """Signed amounts are in company currency, so the line currency must be the company currency"""
        invoice = self._create_invoice(self.company_a, 300, currency=self.foreign_currency)
        line = self._run_wizard(self.company_a).filtered(lambda r: r.move_id == invoice)
        self.assertEqual(line.currency_id, self.company_a.currency_id)
        self.assertAlmostEqual(line.move_amount, invoice.amount_total_signed)
        self.assertAlmostEqual(line.move_amount, 150.0)  # 300 EUR at rate 2

    def test_forecast_002_recompute_keeps_other_company(self):
        """Recomputing the forecast of a company does not delete the snapshot of another company"""
        self._create_invoice(self.company_a, 100)
        self._create_invoice(self.company_b, 200)
        lines_a = self._run_wizard(self.company_a)
        self.assertTrue(lines_a)
        self._run_wizard(self.company_b)
        self.assertEqual(lines_a.exists(), lines_a)
        self.assertEqual(set(lines_a.mapped("company_id").ids), {self.company_a.id})

    def test_forecast_002_rule_hides_other_company(self):
        self._create_invoice(self.company_a, 100)
        self._create_invoice(self.company_b, 200)
        self._run_wizard(self.company_a)
        self._run_wizard(self.company_b)
        forecast = self.env["payment.forecast"].with_context(allowed_company_ids=[self.company_b.id])
        self.assertEqual(set(forecast.search([]).mapped("company_id").ids), {self.company_b.id})

    def test_forecast_002_cron_per_company(self):
        invoice_a = self._create_invoice(self.company_a, 100)
        invoice_b = self._create_invoice(self.company_b, 200)
        self.env["payment.forecast.wizard"].get_forecast_cron(days=30)
        self.env["payment.forecast.wizard"].get_forecast_cron(days=30)
        lines = self.env["payment.forecast"].search([("days", "=", "30")])
        self.assertEqual(lines.filtered(lambda r: r.move_id == invoice_a).company_id, self.company_a)
        self.assertEqual(lines.filtered(lambda r: r.move_id == invoice_b).company_id, self.company_b)
        self.assertEqual(len(lines.filtered(lambda r: r.move_id == invoice_a)), 1)

    def test_forecast_003_invoices_of_selected_company(self):
        invoice_a = self._create_invoice(self.company_a, 100)
        invoice_b = self._create_invoice(self.company_b, 200)
        lines = self._run_wizard(self.company_a)
        self.assertIn(invoice_a, lines.move_id)
        self.assertNotIn(invoice_b, lines.move_id)

    def test_forecast_003_payment_history_of_selected_company(self):
        """The payment history of another company must not delay the forecast"""
        # receivable account shared by both companies, with a 4111 code
        receivable = self.company_data["default_account_receivable"]
        receivable.code = "411100"
        receivable.with_company(self.company_b).code = "411100"
        receivable.company_ids = [Command.link(self.company_b.id)]
        self.partner_a.with_company(self.company_b).property_account_receivable_id = receivable
        # company B: invoice paid after 100 days
        old_date = self.today - relativedelta(days=150)
        old_invoice = self._create_invoice(self.company_b, 50, invoice_date=old_date)
        self.assertEqual(old_invoice.line_ids.filtered("debit").account_id, receivable)
        self.env["account.payment.register"].with_company(self.company_b).with_context(
            active_model="account.move", active_ids=old_invoice.ids
        ).create({"payment_date": old_date + relativedelta(days=100)}).action_create_payments()
        self.assertEqual(old_invoice.payment_state, self.env["account.move"]._get_invoice_in_payment_state())
        self.env.flush_all()
        # company A: invoice due today, without own payment history
        invoice = self._create_invoice(self.company_a, 100)
        line = self._run_wizard(self.company_a).filtered(lambda r: r.move_id == invoice)
        self.assertAlmostEqual(line.payment_amount_forecasted, 100.0)
