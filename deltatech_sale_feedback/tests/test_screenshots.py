# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Cerere de feedback după factură" — generate în timpul testelor,
# în limba RO (fișa) și EN (USAGE.md), pe compania „Demo Distribuție SRL" în RON.
#
# Seed: opțiunea „Email feedback after sale" bifată pe companie, o factură de client postată cu o
# secțiune și două produse, pentru care s-a trimis cererea de feedback, și acțiunea programată
# activă.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_feedback,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_sale_feedback:TestSaleFeedbackScreenshots --stop-after-init
import logging
import unittest

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

_logger = logging.getLogger(__name__)

# Selectează toate rândurile listei și deschide „Acțiuni" (⚙), fără să aleagă nicio intrare.
JS_OPEN_ACTIONS = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector('thead .o_list_record_selector input').click();
    await sleep(1000);
    const toggle = [...document.querySelectorAll('.o_control_panel button')]
        .find((b) => /Acțiuni|Actions/.test(b.textContent));
    toggle.click();
    await sleep(1500);
}
"""

JS_SCROLL_SETTING = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const el = document.querySelector('#sale_feedback_email');
    if (el) {
        el.scrollIntoView({block: 'center'});
    }
    await sleep(800);
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleFeedbackScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_feedback"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Distribuție SRL")
        company = cls.company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in ("sales_team.group_sale_manager", "account.group_account_manager"):
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        company.sale_feedback = True
        env.flush_all()

        categ = env["product.category"].create({"name": "Scule și echipamente"})
        cls.drill = env["product.product"].create(
            {"name": "Mașină de găurit 750 W", "type": "consu", "categ_id": categ.id, "list_price": 450.0}
        )
        cls.saw = env["product.product"].create(
            {"name": "Fierăstrău circular 1200 W", "type": "consu", "categ_id": categ.id, "list_price": 620.0}
        )
        ro = env.ref("base.ro")
        cls.customer = env["res.partner"].create(
            {
                "name": "Construct Total SRL",
                "vat": "RO18547290",
                "email": "achizitii@constructtotal.example",
                "country_id": ro.id,
                "city": "București",
                "street": "Bd. Unirii nr. 20",
                "lang": "ro_RO",
            }
        )
        today = fields.Date.context_today(env["res.partner"])
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.customer.id,
                "invoice_date": today,
                "company_id": company.id,
                "invoice_line_ids": [
                    Command.create({"display_type": "line_section", "name": "Scule electrice"}),
                    Command.create(
                        {"product_id": cls.drill.id, "quantity": 2.0, "price_unit": 450.0, "tax_ids": [Command.clear()]}
                    ),
                    Command.create(
                        {"product_id": cls.saw.id, "quantity": 1.0, "price_unit": 620.0, "tax_ids": [Command.clear()]}
                    ),
                ],
            }
        )
        cls.invoice.action_post()
        # cererea de feedback, ca în chatter să apară e-mailul trimis
        cls.invoice.request_feedback()
        # pagina de evaluare se deschide doar clientului evaluării sau cuiva din aceeași companie;
        # pentru captură, evaluarea aparține utilizatorului cu care se face poza
        rating = env["rating.rating"].create(
            {
                "res_model_id": env["ir.model"]._get_id("product.template"),
                "res_id": cls.drill.product_tmpl_id.id,
                "partner_id": admin.partner_id.id,
                "is_internal": False,
            }
        )
        cls.rating_token = rating.access_token

        # acțiunea programată vine dezactivată; o activăm ca să se vadă cum arată după configurare
        cls.cron = env.ref("deltatech_sale_feedback.ir_cron_feedback")
        cls.cron.active = True
        env.flush_all()

    def _shots(self):
        settings_action = self.env.ref("sale.action_sale_config_settings").id
        list_action = self.env.ref("account.action_move_out_invoice_type").id
        return [
            {
                "url": f"action={settings_action}",
                "name": "01_setari_feedback.png",
                "wait": ".o_form_view",
                "timeout": 60000,
                "eval": JS_SCROLL_SETTING,
                "highlight": ["#sale_feedback_email"],
                "settle": 2500,
            },
            {
                "url": f"action={list_action}&view_type=list",
                "name": "02_actiune_request_feedback.png",
                "wait": ".o_list_view",
                "eval": JS_OPEN_ACTIONS,
                "highlight": {
                    "ro_RO": ".o-dropdown-item:has-text('Solicitare feedback')",
                    "en_US": ".o-dropdown-item:has-text('Request feedback')",
                },
                "settle": 2000,
            },
            {
                "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                "name": "03_email_feedback.png",
                "wait": ".o_form_view",
                "hide_chatter": False,
                "full": True,
                "settle": 3000,
            },
            {
                "url": f"id={self.cron.id}&model=ir.cron&view_type=form",
                "name": "04_actiune_programata.png",
                "wait": ".o_form_view",
                "settle": 2000,
            },
            {
                "path": f"/rate/{self.rating_token}/5",
                "name": "05_pagina_rating.png",
                "wait": "body",
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
