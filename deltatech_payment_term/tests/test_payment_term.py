from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentTerm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Rates Partner"})
        cls.term_single = cls.env["account.payment.term"].create({"name": "Single Line Term"})
        cls.term_rates = cls.env["account.payment.term"].create(
            {
                "name": "Two Rates Term",
                "line_ids": [
                    (0, 0, {"value": "percent", "value_amount": 50.0, "nb_days": 0}),
                    (0, 0, {"value": "percent", "value_amount": 50.0, "nb_days": 30}),
                ],
            }
        )

    def _wizard(self, term=None, **vals):
        ctx = {}
        if term:
            ctx = {"active_model": "account.payment.term", "active_id": term.id}
        values = {"name": "Rates", "rate": 3, "advance": 25.0, "day_of_the_month": 15, "value": "percent"}
        values.update(vals)
        return self.env["account.payment.term.rate.wizard"].with_context(**ctx).create(values)

    def test_payment_term_wizard(self):
        payment_term = self.env["account.payment.term"].create({"name": "Test Payment Term"})
        wizard = self._wizard(payment_term, name="Updated Payment Term")
        wizard.do_create_rate()

        self.assertEqual(payment_term.name, "Updated Payment Term")
        # 1 advance line + 3 rates (the last one being the balance line)
        self.assertEqual(len(payment_term.line_ids), 4)
        self.assertEqual(payment_term.line_ids.mapped("nb_days"), [0, 30, 60, 90])
        self.assertTrue(all(line.value == "percent" for line in payment_term.line_ids))
        self.assertAlmostEqual(sum(payment_term.line_ids.mapped("value_amount")), 100.0, places=4)
        self.assertAlmostEqual(payment_term.line_ids[0].value_amount, 25.0)

    def test_wizard_single_rate(self):
        payment_term = self.env["account.payment.term"].create({"name": "One Rate"})
        self._wizard(payment_term, rate=1, advance=40.0).do_create_rate()
        self.assertEqual(len(payment_term.line_ids), 2)
        self.assertAlmostEqual(payment_term.line_ids[0].value_amount, 40.0)
        self.assertAlmostEqual(payment_term.line_ids[1].value_amount, 60.0)

    def test_wizard_fixed_amount(self):
        payment_term = self.env["account.payment.term"].create({"name": "Fixed Term"})
        self._wizard(payment_term, value="fixed", advance=100.0, rate_value=200.0, rate=2).do_create_rate()
        lines = payment_term.line_ids
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines.mapped("value"), ["fixed", "fixed", "percent"])
        self.assertEqual(lines.mapped("value_amount")[:2], [100.0, 200.0])
        self.assertAlmostEqual(lines[-1].value_amount, 100.0)

    def test_wizard_new_term(self):
        terms_before = self.env["account.payment.term"].search([])
        self._wizard(name="Brand New Rates Term").do_create_rate()
        new_term = self.env["account.payment.term"].search([]) - terms_before
        self.assertEqual(len(new_term), 1)
        self.assertEqual(new_term.name, "Brand New Rates Term")
        self.assertEqual(len(new_term.line_ids), 4)

    def test_wizard_default_get(self):
        wizard_model = self.env["account.payment.term.rate.wizard"].with_context(
            active_model="account.payment.term", active_id=self.term_rates.id
        )
        defaults = wizard_model.default_get(["name", "rate", "term_id"])
        self.assertEqual(defaults["name"], "Two Rates Term")
        self.assertEqual(defaults["rate"], 1)
        self.assertEqual(defaults["term_id"], self.term_rates.id)
        wizard_form = Form(wizard_model)
        self.assertEqual(wizard_form.name, "Two Rates Term")
        self.assertEqual(wizard_form.rate, 1)

    def test_wizard_constraints(self):
        with self.assertRaises(ValidationError):
            self._wizard(rate=0)
        with self.assertRaises(ValidationError):
            self._wizard(advance=120.0)
        # fixed advance is not limited to 100
        self._wizard(value="fixed", advance=500.0)

    def test_in_rates_flags(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_payment_term_id": self.term_single.id,
            }
        )
        self.assertFalse(invoice.in_rates)
        invoice.invoice_payment_term_id = self.term_rates
        self.assertTrue(invoice.in_rates)

        order = self.env["sale.order"].create({"partner_id": self.partner.id, "payment_term_id": self.term_single.id})
        self.assertFalse(order.sale_in_rates)
        order.payment_term_id = self.term_rates
        self.assertTrue(order.sale_in_rates)

    def test_views(self):
        for model, view in [
            ("account.move", "deltatech_payment_term.invoice_form1"),
            ("res.partner", "deltatech_payment_term.view_partner_form"),
            ("sale.order", "deltatech_payment_term.view_order_form"),
            ("account.payment.term", "deltatech_payment_term.view_payment_term_form"),
        ]:
            arch = self.env[model].get_view(self.env.ref(view).inherit_id.id)["arch"]
            self.assertTrue(arch)


@tagged("post_install", "-at_install")
class TestPaymentTermRatesAction(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.term_rates = cls.env["account.payment.term"].create(
            {
                "name": "Two Rates Term",
                "line_ids": [
                    (0, 0, {"value": "percent", "value_amount": 50.0, "nb_days": 0}),
                    (0, 0, {"value": "percent", "value_amount": 50.0, "nb_days": 30}),
                ],
            }
        )
        cls.invoice = cls._create_invoice(
            "out_invoice",
            partner_id=cls.partner_a,
            invoice_date="2026-10-01",
            invoice_payment_term_id=cls.term_rates,
            invoice_line_ids=[cls._prepare_invoice_line(product_id=cls.product_a, price_unit=100.0)],
            post=True,
        )

    def test_invoice_view_rate(self):
        action = self.invoice.view_rate()
        self.assertEqual(action["res_model"], "account.move.line")
        lines = self.env["account.move.line"].search(action["domain"])
        self.assertEqual(len(lines), 2, "One journal item per rate")
        self.assertEqual(lines.mapped("move_id"), self.invoice)
        self.assertEqual(len(set(lines.mapped("date_maturity"))), 2)

    def test_partner_view_rate(self):
        action = self.partner_a.view_rate()
        lines = self.env["account.move.line"].search(action["domain"])
        self.assertEqual(len(lines & self.invoice.line_ids), 2)
        self.assertTrue(all(line.account_id.account_type == "asset_receivable" for line in lines))

    def test_rates_action_views(self):
        action = self.invoice.view_rate()
        views = self.env["account.move.line"].get_views([(action["view_id"][0], "list")])
        self.assertIn("amount_residual", views["views"]["list"]["arch"])
