# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Partener generic pentru clienți neidentificați", în RO (fișa) și EN
# (readme/USAGE.md), pe planul de conturi românesc (`setup_country("ro")`).
#
# Seed: partenerul generic „Client neidentificat", declarat și protejat pe companie; jurnalele
# „Casierie magazin" (numerar), „Bancă BT" (bancă) și „Bancă încasări firme" (bancă, cu Restricție
# generic); factura ciornă pentru partenerul generic, refuzată la validare, și plata ciornă a lui;
# operatoarea „Ana Popescu", fără drept de modificare a partenerului generic.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,sale_management,deltatech_partner_generic,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command, fields
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

OPERATOR = "ana.popescu"

JS_SCROLL_SETTING = """
(async () => {
    document.querySelector("div[name='generic_partner_id']").scrollIntoView({block: 'center'});
    await new Promise((r) => setTimeout(r, 800));
})()
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPartnerGenericScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_partner_generic"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        cls.prepare_ro_company()
        company = env.company
        groups = [
            env.ref(xmlid).id
            for xmlid in (
                "sales_team.group_sale_manager",
                "account.group_account_manager",
                "base.group_system",
            )
        ]
        # utilizatorul testului face seed-ul, admin face capturile
        env.user.group_ids = [Command.link(group) for group in groups]
        env.ref("base.user_admin").write(
            {
                "company_ids": [Command.link(company.id)],
                "company_id": company.id,
                "name": "Maria Ionescu",
                "group_ids": [Command.link(group) for group in groups],
            }
        )
        # operatoarea nu e administrator: vede partenerul generic protejat
        cls.operator = new_test_user(
            env,
            login=OPERATOR,
            name="Ana Popescu",
            groups="base.group_partner_manager,sales_team.group_sale_salesman_all_leads,account.group_account_invoice",
            company_id=company.id,
            company_ids=[Command.set(company.ids)],
        )

        cls.generic = env.ref("deltatech_partner_generic.partner_generic")
        cls.generic.write({"name": "Client neidentificat", "company_id": False})
        company.write({"generic_partner_id": cls.generic.id, "lock_generic_partner": True})

        journal_vals = {"company_id": company.id}
        cls.cash = env["account.journal"].create(
            {"name": "Casierie magazin", "type": "cash", "code": "CSM", **journal_vals}
        )
        cls.bank = env["account.journal"].create({"name": "Bancă BT", "type": "bank", "code": "BBT", **journal_vals})
        cls.bank_restricted = env["account.journal"].create(
            {
                "name": "Bancă încasări firme",
                "type": "bank",
                "code": "BIF",
                "restriction": True,
                **journal_vals,
            }
        )
        # jurnalele implicite ale companiei de test intră și ele în listă; le dăm restricția,
        # ca lista de la plată să arate doar jurnalele create aici
        (
            env["account.journal"].search([("company_id", "=", company.id), ("type", "in", ("bank", "cash"))])
            - cls.cash
            - cls.bank
        ).restriction = True

        tax = env["account.tax"].search(
            [("type_tax_use", "=", "sale"), ("amount", "=", 21.0), ("company_id", "=", company.id)], limit=1
        )
        product = env["product.product"].create(
            {"name": "Scaun ergonomic Nova", "list_price": 450.0, "taxes_id": [Command.set(tax.ids)]}
        )
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.generic.id,
                "invoice_date": fields.Date.context_today(cls.generic),
                "invoice_line_ids": [Command.create({"product_id": product.id, "quantity": 2.0})],
            }
        )
        cls.payment = env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": cls.generic.id,
                "amount": 1089.0,
            }
        )
        env.flush_all()

    def _shots_admin(self):
        settings = self.env.ref("sale.action_sale_config_settings")
        journals = self.env.ref("account.action_account_journal_form")
        menu = self.env.ref("account.menu_finance")
        return [
            {
                "url": f"action={settings.id}",
                "name": "01_setari_partener_generic.png",
                "timeout": 60000,
                # setările Vânzări cer aplicația sale_management (context module)
                "wait": "div[name='generic_partner_id']",
                "eval": JS_SCROLL_SETTING,
                "eval_wait": 1500,
                "highlight": ["div[name='generic_partner_id']", "div[name='lock_generic_partner']"],
                "settle": 2000,
            },
            {
                "url": f"action={journals.id}&menu_id={menu.id}&id={self.bank_restricted.id}"
                "&model=account.journal&view_type=form",
                "name": "02_jurnal_restrictie_generic.png",
                "wait": ".o_form_view div[name='restriction']",
                "highlight": ["div[name='restriction']"],
            },
        ]

    def _shots_operator(self):
        partner_url = f"id={self.generic.id}&model=res.partner&view_type=form"
        return [
            {
                "url": partner_url,
                "name": "03_partener_generic_protejat.png",
                "wait": ".o_form_view .alert-info",
                "highlight": [".o_form_view .alert-info"],
            },
            {
                "url": partner_url,
                "name": "04_modificare_refuzata.png",
                "wait": ".o_form_view div[name='phone'] input",
                "eval": "(async () => {"
                "const input = document.querySelector(\"div[name='phone'] input\");"
                "input.value = '0722 000 000';"
                "input.dispatchEvent(new Event('input', {bubbles: true}));"
                "input.dispatchEvent(new Event('change', {bubbles: true}));"
                "await new Promise((r) => setTimeout(r, 500));"
                "document.querySelector('.o_form_button_save').click();"
                "})()",
                "eval_wait": 2500,
                "highlight": [".modal .modal-body"],
            },
        ]

    def _shots_invoice(self):
        return [
            {
                "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                "name": "05_factura_validare_refuzata.png",
                "wait": ".o_form_view button[name='action_post']",
                "click_btn": "button[name='action_post']",
                "wait_after": ".modal",
                "settle": 2000,
                "highlight": [".modal .modal-body"],
            },
            {
                "url": f"id={self.payment.id}&model=account.payment&view_type=form",
                "name": "06_plata_jurnale_permise.png",
                "wait": ".o_form_view div[name='journal_id'] input",
                "click_btn": "div[name='journal_id'] input",
                "wait_after": ".o-autocomplete--dropdown-menu",
                "settle": 1500,
                "highlight": ["div[name='partner_id']", ".o-autocomplete--dropdown-menu"],
            },
        ]

    def _capture(self, lang):
        self.capture_screenshots(self._shots_admin(), lang=lang, hide_systray=True)
        self.capture_screenshots(self._shots_operator(), login=OPERATOR, lang=lang, hide_systray=True)
        self.capture_screenshots(self._shots_invoice(), lang=lang, hide_systray=True)
        # capturile nu au schimbat nimic: partenerul, factura și plata rămân ca în seed
        self.assertEqual(self.invoice.state, "draft")
        self.assertFalse(self.generic.phone)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")

    def _gif_steps(self):
        return [
            {
                "goto": f"id={self.invoice.id}&model=account.move&view_type=form",
                "wait": ".o_form_view button[name='action_post']",
            },
            {
                "caption": {
                    "ro_RO": "Factura are ca client partenerul generic",
                    "en_US": "The invoice is addressed to the generic partner",
                },
                "move": "div[name='partner_id']",
                "hold": 1200,
            },
            {
                "caption": {
                    "ro_RO": "La validare, Odoo cere clientul real",
                    "en_US": "On validation, Odoo asks for the real customer",
                },
                "click": "button[name='action_post']",
                "wait_after": ".modal",
                "hold": 2500,
            },
            {"click": ".modal-footer .btn-primary", "hold": 600},
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        """GIF-ul demo: factura pentru partenerul generic nu se poate valida, în RO și EN."""
        # banner.json e în engleză: slide-ul RO primește textele lui
        intro_ro = {
            "title": "Partener generic",
            "summary": "Partenerul generic pentru clienții neidentificați, cu restricții contabile",
            "features": ["Fără factură validată", "Jurnale de plată restricționate", "Partener protejat"],
        }
        self.capture_gif(self._gif_steps(), name="demo.gif", intro=intro_ro)
        self.capture_gif(self._gif_steps(), name="demo.gif", lang="en_US")
