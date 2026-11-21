# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Curs valutar propriu pe factură" — generate în timpul
# testelor, în limba RO (fișa) și EN (readme/USAGE.md), pe compania „RO Company" în RON.
#
# Seedează moneda EUR la cursul oficial 4,97 lei/EUR, un client și facturi de 100 EUR + TVA:
# una în ciornă la cursul oficial, una în ciornă cu cursul propriu 5,0000, una confirmată cu
# același curs și nota ei de credit.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_account_edit_currency_rate,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

OFFICIAL_RATE = 4.97  # lei pentru 1 EUR
CUSTOM_RATE = 5.0
CUSTOM_RATE_FIELD = "div[name='currency_rate_custom']"
# bulina numerotată a evidențierii stă peste începutul câmpului: împingem valoarea spre dreapta,
# ca 5,0000 să rămână lizibil
SHIFT_CUSTOM_RATE_VALUE = """() => {
    document.querySelectorAll("div[name='currency_rate_custom'] input, div[name='currency_rate_custom'] span")
        .forEach((e) => { e.style.paddingLeft = "28px"; });
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestEditCurrencyRateScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_account_edit_currency_rate"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="RO Company")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        admin.group_ids = [Command.link(env.ref("base.group_multi_currency").id)]

        # cursul oficial: 1 RON = 1 / 4,97 EUR
        cls.eur = cls.setup_other_currency("EUR", rates=[("1900-01-01", 1.0), ("2026-01-01", 1 / OFFICIAL_RATE)])
        cls.partner = env["res.partner"].create(
            {
                "name": "Client Exemplu SRL",
                "country_id": env.ref("base.ro").id,
                "is_company": True,
                "lang": "ro_RO",
            }
        )
        if cls.partner.property_product_pricelist:
            cls.partner.property_product_pricelist.name = "Listă de prețuri"
        tax = company.account_sale_tax_id
        # serviciile prestate se înregistrează pe 704, nu pe 707 (mărfuri)
        income_704 = env["account.account"].search(
            [*env["account.account"]._check_company_domain(company), ("code", "=like", "704%")], limit=1
        )
        cls.product = env["product.product"].create(
            {
                "name": "Servicii de consultanță",
                "type": "service",
                "taxes_id": [Command.set(tax.ids)],
                **({"property_account_income_id": income_704.id} if income_704 else {}),
            }
        )

        # Date diferite pe facturi: altfel Odoo le marchează ca posibile duplicate (banner în capturi).
        # Pasul 1: factura în ciornă, la cursul oficial
        cls.invoice_draft = cls._create_invoice("2026-10-01")
        # Pașii 2–3: o factură în ciornă, cu cursul propriu
        cls.invoice_custom = cls._create_invoice("2026-10-02", currency_rate_custom=CUSTOM_RATE)
        # Pasul 4: factura confirmată cu cursul propriu
        cls.invoice_posted = cls._create_invoice("2026-10-05", currency_rate_custom=CUSTOM_RATE)
        cls.invoice_posted.action_post()
        # Pasul 5: nota de credit, prin butonul „Notă credit" (asistentul de stornare), pe o factură
        # separată, ca factura de la Pasul 4 să nu apară cu panglica „Inversat"
        cls.invoice_reversed = cls._create_invoice("2026-10-06", currency_rate_custom=CUSTOM_RATE)
        cls.invoice_reversed.action_post()
        reversal = (
            env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=cls.invoice_reversed.ids)
            .create({"journal_id": cls.invoice_reversed.journal_id.id, "date": "2026-10-20"})
        )
        cls.credit_note = env["account.move"].browse(reversal.refund_moves()["res_id"])
        cls.credit_note.action_post()
        env.flush_all()

    @classmethod
    def _create_invoice(cls, invoice_date, **extra):
        return cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": invoice_date,
                "currency_id": cls.eur.id,
                "invoice_user_id": cls.env.ref("base.user_admin").id,
                "invoice_line_ids": [Command.create({"product_id": cls.product.id, "price_unit": 100.0})],
                **extra,
            }
        )

    def _invoice_url(self, move):
        action = self.env.ref("account.action_move_out_invoice_type")
        return f"action={action.id}&id={move.id}&model=account.move&view_type=form"

    def _shots(self):
        return [
            # 1. Factura în ciornă, în EUR, la cursul oficial
            {
                "url": self._invoice_url(self.invoice_draft),
                "name": "01_factura_ciorna.png",
                "wait": ".o_form_view",
                "settle": 2000,
            },
            # 2. Tabul Alte informații, cu cursul propriu completat
            {
                "url": self._invoice_url(self.invoice_custom),
                "name": "02_curs_propriu.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "highlight": CUSTOM_RATE_FIELD,
                "eval": SHIFT_CUSTOM_RATE_VALUE,
                "settle": 2000,
            },
            # 3. Elementele de jurnal la cursul propriu
            {
                "url": self._invoice_url(self.invoice_custom),
                "name": "03_elemente_jurnal.png",
                "wait": ".o_form_view",
                "click_tab": "Journal Items",
                "full": True,
                "settle": 2000,
            },
            # 4. Factura confirmată: cursul propriu needitabil
            {
                "url": self._invoice_url(self.invoice_posted),
                "name": "04_factura_confirmata.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "highlight": CUSTOM_RATE_FIELD,
                "eval": SHIFT_CUSTOM_RATE_VALUE,
                "settle": 2000,
            },
            # 5. Nota de credit: păstrează cursul propriu al facturii
            {
                "url": self._invoice_url(self.credit_note),
                "name": "05_nota_credit.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "highlight": CUSTOM_RATE_FIELD,
                "eval": SHIFT_CUSTOM_RATE_VALUE,
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.assertAlmostEqual(self.invoice_custom.amount_total_signed, 605.0)
        self.assertAlmostEqual(self.credit_note.currency_rate_custom, CUSTOM_RATE)
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
