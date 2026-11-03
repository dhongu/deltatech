# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Partener generic pentru clienți anonimi": același flux în RO
# (fișa) și în EN (USAGE.md).
#
# Seed: partenerul generic al modulului setat pe companie și protejat, jurnalul de bancă
# bifat cu restricție, o factură de client în ciornă și o plată în ciornă pe partenerul
# generic, plus un vânzător fără dreptul de a modifica partenerul generic.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_partner_generic,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots/deltatech_partner_generic --stop-after-init --without-demo=True
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

SETTING_BOX = ".o_setting_box:has(div[name='generic_partner_id'])"

SCROLL_TO_SETTING = """() => {
    document.querySelector("div[name='generic_partner_id']").closest('.o_setting_box')
        .scrollIntoView({block: 'center'});
}"""

# Golește câmpul Jurnal al plății, ca lista să arate toate jurnalele propuse.
OPEN_JOURNALS = """async () => {
    const input = document.querySelector("div[name='journal_id'] input");
    input.focus();
    input.click();
    input.value = '';
    input.dispatchEvent(new Event('input', {bubbles: true}));
}"""

# Redenumește partenerul și salvează: salvarea e refuzată cu mesajul de protecție.
RENAME_AND_SAVE = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const input = document.querySelector("div[name='name'] input, div[name='name'] textarea");
    input.focus();
    input.value = 'Ionescu Andrei';
    input.dispatchEvent(new Event('input', {bubbles: true}));
    input.dispatchEvent(new Event('change', {bubbles: true}));
    input.blur();
    await sleep(800);
    document.querySelector('.o_form_button_save').click();
    for (let t = 0; t < 15000 && !document.querySelector('.modal-dialog'); t += 200) {
        await sleep(200);
    }
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPartnerGenericScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_partner_generic"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        # planul RO aduce conturile 707/5121/5311 și TVA 21%; o bază fără țară RO are planul generic
        if company.chart_template != "ro":
            env["account.chart.template"].try_loading("ro", company, install_demo=False)
        admin = env.ref("base.user_admin")
        admin.group_ids = [Command.link(env.ref("sales_team.group_sale_manager").id)]

        cls.generic = env.ref("deltatech_partner_generic.partner_generic")
        cls.generic.lang = "ro_RO"
        company.write({"generic_partner_id": cls.generic.id, "lock_generic_partner": True})

        # banca nu se propune pentru clienții anonimi: ei plătesc doar numerar
        cls.bank_journal = env["account.journal"].search(
            [("company_id", "=", company.id), ("type", "=", "bank")], limit=1
        )
        cls.bank_journal.restriction = True
        # diferențele de casă: conturi RO în locul celor 999xxx generate de nucleu
        accounts = env["account.account"].with_company(company)
        profit = accounts.search([("code", "=like", "7588%")], limit=1)
        loss = accounts.search([("code", "=like", "6588%")], limit=1)
        if profit and loss:
            cls.bank_journal.write({"profit_account_id": profit.id, "loss_account_id": loss.id})

        vat_21 = env["account.tax"].search(
            [("company_id", "=", company.id), ("type_tax_use", "=", "sale"), ("amount", "=", 21.0)], limit=1
        )
        product = env["product.product"].create(
            {"name": "Set pensule pictură", "list_price": 45.0, "taxes_id": [Command.set(vat_21.ids)]}
        )
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.generic.id,
                "invoice_line_ids": [Command.create({"product_id": product.id, "quantity": 2, "price_unit": 45.0})],
            }
        )
        # banca e restricționată, deci plata primește implicit jurnalul de numerar
        cash_journal = env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "cash")], limit=1)
        if not cash_journal:
            cash_journal = env["account.journal"].create(
                {"name": "Numerar", "type": "cash", "code": "CSH1", "company_id": company.id}
            )
        cls.payment = env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": cls.generic.id,
                "amount": 108.9,
            }
        )

        cls.seller = env["res.users"].create(
            {
                "name": "Popescu Maria",
                "login": "vanzator_generic",
                "password": "vanzator_generic",
                "lang": "ro_RO",
                "company_id": company.id,
                "company_ids": [Command.set(company.ids)],
                "group_ids": [
                    Command.set(
                        [
                            env.ref("base.group_user").id,
                            env.ref("base.group_partner_manager").id,
                            env.ref("sales_team.group_sale_salesman").id,
                        ]
                    )
                ],
            }
        )
        env.flush_all()
        cls.settings_action = env.ref("account.action_account_config")
        cls.journal_action = env.ref("account.action_account_journal_form")
        cls.invoice_action = env.ref("account.action_move_out_invoice_type")
        cls.payment_action = env.ref("account.action_account_payments")
        cls.partner_action = env.ref("base.action_partner_form")
        cls.sale_menu = env.ref("sale.sale_menu_root")

    def _admin_shots(self):
        return [
            # 1. Setări → Facturare: partenerul generic și protecția lui
            {
                "url": f"action={self.settings_action.id}",
                "name": "01_setari_partener_generic.png",
                "wait": "div[name='generic_partner_id']",
                "timeout": 60000,
                "eval": SCROLL_TO_SETTING,
                "highlight": ["div[name='generic_partner_id']", "div[name='lock_generic_partner']"],
                "settle": 2000,
            },
            # 2. jurnalul de bancă bifat cu Restricție generică
            {
                "url": (
                    f"action={self.journal_action.id}&id={self.bank_journal.id}&model=account.journal&view_type=form"
                ),
                "name": "02_jurnal_restrictie.png",
                "wait": "div[name='restriction']",
                "highlight": ["div[name='restriction']"],
                "settle": 2000,
            },
            # 3. factura de client în ciornă, emisă pe partenerul generic
            {
                "url": (f"action={self.invoice_action.id}&id={self.invoice.id}&model=account.move&view_type=form"),
                "name": "03_factura_ciorna_generic.png",
                "wait": "div[name='partner_id']",
                "highlight": ["div[name='partner_id']", "button[name='action_post']"],
                "settle": 2000,
            },
            # 4. validarea refuzată: mesajul spune ce câmp trebuie schimbat
            {
                "url": (f"action={self.invoice_action.id}&id={self.invoice.id}&model=account.move&view_type=form"),
                "name": "04_eroare_validare_factura.png",
                "wait": "button[name='action_post']",
                "click_btn": "button[name='action_post']",
                "wait_after": ".modal-dialog",
                "highlight": [".modal-body"],
                "settle": 2000,
            },
            # 5. plata clientului anonim: în lista jurnalelor lipsește banca restricționată
            {
                "url": (f"action={self.payment_action.id}&id={self.payment.id}&model=account.payment&view_type=form"),
                "name": "05_plata_jurnale_permise.png",
                "wait": "div[name='journal_id'] input",
                "eval": OPEN_JOURNALS,
                "eval_wait": 2000,
                "highlight": ["div[name='partner_id']", "div[name='journal_id']"],
                "settle": 2000,
            },
        ]

    def _seller_shots(self):
        partner_url = (
            f"action={self.partner_action.id}&menu_id={self.sale_menu.id}"
            f"&id={self.generic.id}&model=res.partner&view_type=form"
        )
        return [
            # 6. partenerul generic deschis de un vânzător: banner de protecție
            {
                "url": partner_url,
                "name": "06_partener_protejat.png",
                "wait": ".o_form_view .alert-info",
                "highlight": [".o_form_view .alert-info"],
                "settle": 2000,
            },
            # 7. modificarea e refuzată la salvare
            {
                "url": partner_url,
                "name": "07_eroare_modificare_partener.png",
                "wait": ".o_form_view .alert-info",
                "eval": RENAME_AND_SAVE,
                "eval_wait": 1500,
                "highlight": [".modal-body"],
                "settle": 2000,
            },
        ]

    def _capture(self, lang):
        self.capture_screenshots(self._admin_shots(), hide_systray=True, lang=lang)
        self.capture_screenshots(self._seller_shots(), login="vanzator_generic", hide_systray=True, lang=lang)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
