# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Solicitare feedback după factură", în RO (fișa) și EN (USAGE.md).
#
# Seedează o factură client postată, cu două produse, setarea de feedback bifată și parametrul
# ``sale.days_request_feedback`` = 3. Pasul 5 apasă „Solicitare feedback": pe 19.0 trimiterea
# pică (API-uri Odoo care nu mai există), iar captura arată dialogul de eroare.
#
# Rulare:
#   python3 odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_feedback,deltatech_doc_screenshots,sale_management,l10n_ro \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Deschide meniul „Acțiuni" (rotița) din formularul facturii.
OPEN_ACTION_MENU = """
    [...document.querySelectorAll('.o_cp_action_menus button')]
        .find((b) => b.querySelector('.fa-cog')).click();
"""

# Deschide meniul „Acțiuni" și apasă intrarea „Solicitare feedback" (eticheta e în limba capturii).
# Detaliile tehnice ale erorii rămân închise: traceback-ul conține căile locale ale serverului.
RUN_REQUEST_FEEDBACK = """
    new Promise((resolve) => {
        [...document.querySelectorAll('.o_cp_action_menus button')]
            .find((b) => b.querySelector('.fa-cog')).click();
        setTimeout(() => {
            [...document.querySelectorAll('.o-dropdown--menu .dropdown-item')]
                .find((i) => i.textContent.includes('%(label)s')).click();
            resolve();
        }, 800);
    })
"""

FEEDBACK_LABEL = {"ro_RO": "Solicitare feedback", "en_US": "Request feedback"}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleFeedbackScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_feedback"

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
        sale_manager = env.ref("sales_team.group_sale_manager")
        admin.group_ids = [Command.link(sale_manager.id), Command.link(env.ref("base.group_system").id)]

        company.sale_feedback = True
        company.website = "https://www.exemplu.ro"
        cls.param = env["ir.config_parameter"].sudo()
        cls.param.set_param("sale.days_request_feedback", "3")
        cls.param_rec = cls.param.search([("key", "=", "sale.days_request_feedback")])
        cls.cron = env.ref("deltatech_sale_feedback.ir_cron_feedback")
        cls.template = env.ref("deltatech_sale_feedback.mail_template_sale_feedback")
        cls.settings_action = env.ref("sale.action_sale_config_settings")

        partner = env["res.partner"].create(
            {"name": "Magazin Exemplu SRL", "email": "comenzi@magazin-exemplu.ro", "country_id": env.ref("base.ro").id}
        )
        cafea = env["product.product"].create({"name": "Cafea boabe 1 kg", "list_price": 85.0})
        filtru = env["product.product"].create({"name": "Filtre hârtie (100 buc.)", "list_price": 12.0})
        cls.invoice = cls._create_invoice(
            partner_id=partner.id,
            invoice_line_ids=[
                Command.create({"product_id": cafea.id, "quantity": 2, "price_unit": 85.0}),
                Command.create({"product_id": filtru.id, "quantity": 5, "price_unit": 12.0}),
            ],
            post=True,
        )
        env.flush_all()

    def _shots(self):
        invoice_url = f"id={self.invoice.id}&model=account.move&view_type=form"
        return [
            {
                "url": f"action={self.settings_action.id}",
                "name": "01_setari_feedback.png",
                "wait": "div[name='sale_feedback']",
                "settle": 2500,
                "eval": "document.querySelector(\"div[name='sale_feedback']\").scrollIntoView({block: 'center'})",
                "highlight": ".o_setting_box:has(div[name='sale_feedback'])",
            },
            {
                "url": f"id={self.param_rec.id}&model=ir.config_parameter&view_type=form",
                "name": "02_parametru_zile.png",
                "wait": ".o_form_view",
                "highlight": ".o_inner_group:has(div[name='value'])",
            },
            {
                "url": f"id={self.cron.id}&model=ir.cron&view_type=form",
                "name": "03_actiune_programata.png",
                "wait": ".o_form_view",
                "settle": 2000,
                "full": True,
                "highlight": ["div[name='active']", "div[name='code']"],
            },
            {
                "url": invoice_url,
                "name": "04_meniu_actiuni_factura.png",
                "wait": ".o_form_view",
                "settle": 2000,
                "eval": OPEN_ACTION_MENU,
                "highlight": {
                    lang: f".o-dropdown--menu .dropdown-item:has-text('{label}')"
                    for lang, label in FEEDBACK_LABEL.items()
                },
            },
            {
                "url": invoice_url,
                "name": "05_eroare_trimitere.png",
                "wait": ".o_form_view",
                "eval": {lang: RUN_REQUEST_FEEDBACK % {"label": label} for lang, label in FEEDBACK_LABEL.items()},
                "eval_wait": 2500,
                "settle": 3000,
            },
            {
                "url": f"id={self.template.id}&model=mail.template&view_type=form",
                "name": "06_sablon_email.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "full": True,
            },
        ]

    # pasul 5 provoacă intenționat eroarea de server a trimiterii pe 19.0
    @mute_logger("odoo.http")
    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    @mute_logger("odoo.http")
    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
