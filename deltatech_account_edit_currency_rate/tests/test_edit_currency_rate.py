# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestEditCurrencyRate(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        # valută străină față de moneda companiei (RON), cu curs oficial
        cls.foreign_currency = cls.setup_other_currency("EUR")

    def test_convert_uses_context_rate(self):
        """`res.currency._convert` cu context `currency_rate` folosește rata dată,
        nu cursul oficial din baza de date."""
        company = self.company_data["company"]
        company_currency = company.currency_id

        converted = self.foreign_currency.with_context(currency_rate=5.0)._convert(
            100.0, company_currency, company, fields.Date.from_string("2025-01-01")
        )
        # 100 (EUR) * 5.0 = 500 (RON), independent de cursul oficial
        self.assertEqual(converted, 500.0)

    def test_convert_falls_back_to_official_rate(self):
        """Fără context `currency_rate`, conversia rămâne cea standard."""
        company = self.company_data["company"]
        company_currency = company.currency_id

        with_context = self.foreign_currency.with_context(currency_rate=5.0)._convert(
            100.0, company_currency, company, fields.Date.from_string("2025-01-01")
        )
        without_context = self.foreign_currency._convert(
            100.0, company_currency, company, fields.Date.from_string("2025-01-01")
        )
        self.assertNotEqual(with_context, without_context)

    def test_invoice_custom_rate_overrides_balance(self):
        """Cursul custom pe factură suprascrie cursul de pe linii: `currency_rate`
        devine 1/custom, iar `balance` se recalculează cu rata custom."""
        invoice = self.init_invoice(
            "out_invoice",
            amounts=[100.0],
            currency=self.foreign_currency,
            taxes=[],
        )

        custom_rate = 5.0  # 5 RON pentru 1 EUR
        invoice.currency_rate_custom = custom_rate
        invoice.onchange_currency_rate_custome()

        product_lines = invoice.invoice_line_ids
        self.assertTrue(product_lines)
        for line in product_lines:
            self.assertAlmostEqual(line.currency_rate, 1 / custom_rate, places=6)
            # |amount_currency| = 100 EUR -> |balance| = 100 * 5 = 500 RON
            self.assertAlmostEqual(abs(line.balance), abs(line.amount_currency) * custom_rate, places=2)
