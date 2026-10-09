# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCustomRateServer(AccountTestInvoicingCommon):
    """CUSTOMRATE-001: the custom rate is applied on create/write, not only in the onchange."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        # official rate: 1 RON = 2 EUR, i.e. 100 EUR = 50 RON
        cls.eur = cls.setup_other_currency("EUR")
        cls.tax = cls.env["account.tax"].create({"name": "TVA 21% test", "amount": 21.0, "type_tax_use": "sale"})

    def _invoice(self, taxes=None):
        return self.init_invoice(
            "out_invoice", amounts=[100.0], currency=self.eur, taxes=taxes or [], invoice_date="2026-10-01"
        )

    def _assert_balances(self, invoice, product, tax, receivable):
        lines = invoice.line_ids
        self.assertAlmostEqual(sum(lines.filtered(lambda l: l.display_type == "product").mapped("balance")), product)
        self.assertAlmostEqual(sum(lines.filtered(lambda l: l.display_type == "tax").mapped("balance")), tax)
        self.assertAlmostEqual(
            sum(lines.filtered(lambda l: l.display_type == "payment_term").mapped("balance")), receivable
        )
        self.assertAlmostEqual(sum(lines.mapped("debit")), sum(lines.mapped("credit")))

    def test_write_custom_rate_recomputes_balances(self):
        invoice = self._invoice(taxes=self.tax)
        self._assert_balances(invoice, -50.0, -10.5, 60.5)
        # line rates already read in this environment must not stay stale
        self.assertAlmostEqual(invoice.invoice_line_ids.currency_rate, 2.0)

        invoice.write({"currency_rate_custom": 5.0})

        self.assertAlmostEqual(invoice.invoice_currency_rate, 0.2)
        self.assertAlmostEqual(invoice.invoice_line_ids.currency_rate, 0.2)
        # 100 EUR + 21 EUR VAT at 5 RON/EUR, foreign amounts unchanged
        self.assertAlmostEqual(invoice.invoice_line_ids.amount_currency, -100.0)
        self._assert_balances(invoice, -500.0, -105.0, 605.0)
        self.assertAlmostEqual(invoice.amount_total_signed, 605.0)

    def test_create_with_custom_rate(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-10-01",
                "currency_id": self.eur.id,
                "currency_rate_custom": 5.0,
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0, "tax_ids": [(6, 0, [])]})
                ],
            }
        )
        self._assert_balances(invoice, -500.0, 0.0, 500.0)

    def test_clear_custom_rate_restores_official_rate(self):
        invoice = self._invoice()
        invoice.currency_rate_custom = 5.0
        self._assert_balances(invoice, -500.0, 0.0, 500.0)
        invoice.currency_rate_custom = 0.0
        self.assertAlmostEqual(invoice.invoice_currency_rate, 2.0)
        self._assert_balances(invoice, -50.0, 0.0, 50.0)

    def test_form_edit_same_as_write(self):
        invoice = self._invoice(taxes=self.tax)
        with Form(invoice) as move_form:
            move_form.currency_rate_custom = 5.0
        self._assert_balances(invoice, -500.0, -105.0, 605.0)

    def test_posted_invoice_custom_rate_locked(self):
        invoice = self._invoice()
        invoice.currency_rate_custom = 5.0
        invoice.action_post()
        with self.assertRaises(UserError):
            invoice.write({"currency_rate_custom": 4.0})
        # writing the same value is allowed (e.g. a form save) and changes nothing
        invoice.write({"currency_rate_custom": 5.0})
        self._assert_balances(invoice, -500.0, 0.0, 500.0)
