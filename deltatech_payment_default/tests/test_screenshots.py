# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Metoda de plată implicită pe partener" — generate în
# timpul testelor, în limba RO, pe compania „Demo Plăți SRL" în RON.
#
# Seedează un jurnal de bancă „Banca Exemplu", un client și două facturi de 1.210,00 lei.
# Prima factură se plătește prin asistent cu „Banca Exemplu" și bifa „Setează ca implicit";
# la a doua, asistentul propune singur același jurnal.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_payment_default,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

PAY_BUTTON = "button[name='action_register_payment']"
WIZARD = ".modal div[name='journal_id']"
# alege jurnalul „Banca Exemplu" în asistent și bifează „Setează ca implicit", ca operatorul
SELECT_JOURNAL_AND_CHECK = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const input = document.querySelector(".modal div[name='journal_id'] input");
    input.focus();
    input.value = "Banca Exemplu";
    input.dispatchEvent(new Event("input", {bubbles: true}));
    await sleep(1200);
    const item = [...document.querySelectorAll(".o-autocomplete--dropdown-item")]
        .find((e) => e.textContent.includes("Banca Exemplu"));
    item.querySelector("a").click();
    await sleep(1200);
    document.querySelector(".modal div[name='set_as_default'] input").click();
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPaymentDefaultScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_payment_default"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Plăți SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        groups = env.ref("base.group_partner_manager") | env.ref("account.group_account_invoice")
        admin.group_ids = [Command.link(group.id) for group in groups]
        env.user.group_ids = [Command.link(group.id) for group in groups]

        cls.bank_journal = env["account.journal"].create(
            {"name": "Banca Exemplu", "code": "BEX", "type": "bank", "company_id": company.id}
        )
        cls.method_line = cls.bank_journal.inbound_payment_method_line_ids[:1]
        cls.partner = env["res.partner"].create(
            {
                "name": "Client Exemplu SRL",
                "country_id": env.ref("base.ro").id,
                "lang": "ro_RO",
            }
        )
        # numele implicit al listei de prețuri a testului e în engleză („Test Pricelist")
        if cls.partner.property_product_pricelist:
            cls.partner.property_product_pricelist.name = "Listă de prețuri RON"
        tax = company.account_sale_tax_id
        cls.product = env["product.product"].create(
            {"name": "Servicii de consultanță", "type": "service", "taxes_id": [Command.set(tax.ids)]}
        )
        cls.invoice = cls._create_invoice()
        env.flush_all()

    @classmethod
    def _create_invoice(cls):
        invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_user_id": cls.env.ref("base.user_admin").id,
                "invoice_line_ids": [Command.create({"product_id": cls.product.id, "price_unit": 1000.0})],
            }
        )
        invoice.action_post()
        return invoice

    def _pay_as_operator(self):
        """Ce face operatorul la pasul 2: Banca Exemplu, bifa, Creează plata."""
        # mesajul din istoric e scris de operator (admin), în limba lui
        env = self.env(user=self.env.ref("base.user_admin"), context=dict(self.env.context, lang="ro_RO"))
        wizard = (
            env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=self.invoice.ids)
            .create({})
        )
        wizard.journal_id = self.bank_journal
        wizard.write({"payment_method_line_id": self.method_line.id, "set_as_default": True})
        self.assertTrue(wizard.can_set_as_default)
        wizard.action_create_payments()
        partner = self.partner.with_company(self.env.company)
        self.assertEqual(partner.property_inbound_payment_method_line_id, self.method_line)
        self.env.flush_all()

    def test_capture_fise(self):
        self.assertEqual(self.invoice.amount_total, 1210.0)
        invoice_url = f"id={self.invoice.id}&model=account.move&view_type=form"
        self.capture_screenshots(
            [
                # 1. Factura validată, butonul Plătește
                {
                    "url": invoice_url,
                    "name": "01_factura_buton_plateste.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": [PAY_BUTTON],
                },
                # 2. Asistentul de plată: jurnalul ales și bifa „Setează ca implicit"
                {
                    "url": invoice_url,
                    "name": "02_asistent_seteaza_implicit.png",
                    "wait": ".o_form_view",
                    "click_btn": PAY_BUTTON,
                    "wait_after": WIZARD,
                    "eval": SELECT_JOURNAL_AND_CHECK,
                    "eval_wait": 1500,
                    "settle": 1500,
                    "highlight": [
                        ".modal div[name='journal_id']",
                        ".modal div[name='payment_method_line_id']",
                        ".modal div[name='set_as_default']",
                    ],
                },
            ]
        )
        self._pay_as_operator()
        invoice_2 = self._create_invoice()
        self.env.flush_all()
        self.capture_screenshots(
            [
                # 3. Partenerul: metoda de plată reținută și mesajul din istoric
                {
                    "url": f"id={self.partner.id}&model=res.partner&view_type=form",
                    "name": "03_partener_metoda_plata.png",
                    "wait": ".o_form_view",
                    "click_tab": "Vânzări & Achiziții",
                    "hide_chatter": False,
                    "settle": 2500,
                    "highlight": ["div[name='property_inbound_payment_method_line_id']", ".o-mail-Message"],
                },
                # 4. Factura următoare: asistentul propune singur jurnalul și metoda
                {
                    "url": f"id={invoice_2.id}&model=account.move&view_type=form",
                    "name": "04_factura_noua_propunere.png",
                    "wait": ".o_form_view",
                    "click_btn": PAY_BUTTON,
                    "wait_after": WIZARD,
                    "settle": 2000,
                    "highlight": [
                        ".modal div[name='journal_id']",
                        ".modal div[name='payment_method_line_id']",
                    ],
                },
            ]
        )
