# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Curățarea programată a bazei de date" — generate în
# timpul testelor, în limba RO, pe compania „RO Company" în RON.
#
# Seedează trei PDF-uri de factură mai vechi de 90 de zile. Pe ele se face întâi o
# rulare de test (nu șterge nimic), apoi rularea reală, după activarea curățării.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_actions,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# caseta setării „Curățare PDF-uri de factură", folosită în pașii 2–4
INVOICE_BOX = ".o_setting_box:has(div[name='dt_actions_invoice_pdf_active'])"
AUTOVACUUM_BOX = ".o_setting_box:has(div[name='dt_actions_autovacuum'])"

# aduce în vedere titlul secțiunii „Curățare bază de date"
SCROLL_TO_SECTION = """() => {
    const title = [...document.querySelectorAll('.o_setting_container h2, .app_settings_block h2')]
        .find((h) => h.textContent.includes('Curățare bază de date') || h.textContent.includes('Database Cleanup'));
    if (title) { title.scrollIntoView({block: 'start'}); }
}"""

SCROLL_TO_INVOICE_BOX = """() => {
    const box = document.querySelector("div[name='dt_actions_invoice_pdf_active']").closest('.o_setting_box');
    box.scrollIntoView({block: 'center'});
}"""

# așteaptă un element în pagină (dialogul de confirmare, notificarea, formularul reîncărcat)
WAIT_FOR = """const waitFor = async (selector, ms = 15000) => {
        for (let t = 0; t < ms; t += 200) {
            const el = document.querySelector(selector);
            if (el) { return el; }
            await new Promise((r) => setTimeout(r, 200));
        }
        return null;
    };"""

# „Rulează acum" pe curățarea PDF-urilor de factură: butonul, apoi confirmarea din dialog.
# Rezultatul e o notificare care se închide singură după câteva secunde, așa că scriptul
# se întoarce imediat ce apare, iar captura se face fără pauză lungă.
RUN_NOW_BODY = """
    document.querySelector("button[name='action_dt_actions_run_invoice_pdf']").click();
    // confirmă dialogurile care apar până la notificare: salvarea modificărilor (dacă
    // setările au fost schimbate) și confirmarea rulării
    for (let t = 0; t < 20000 && !document.querySelector('.o_notification'); t += 300) {
        const ok = document.querySelector('.modal .btn-primary');
        if (ok) { ok.click(); }
        await new Promise((r) => setTimeout(r, 300));
    }
    document.querySelector("div[name='dt_actions_invoice_pdf_active']").closest('.o_setting_box')
        .scrollIntoView({block: 'center'});
"""
RUN_NOW = "async () => {\n    " + WAIT_FOR + RUN_NOW_BODY + "}"

SCROLL_TO_AUTOVACUUM = """() => {
    document.querySelector("div[name='dt_actions_autovacuum']").closest('.o_setting_box')
        .scrollIntoView({block: 'center'});
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestActionsScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_actions"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        icp = env["ir.config_parameter"].sudo()
        icp.set_param("deltatech_actions.invoice_pdf_dry_run", "True")
        icp.set_param("deltatech_actions.invoice_pdf_limit", "500")
        icp.set_param("deltatech_actions.invoice_pdf_max_date_days", "90")
        icp.set_param("deltatech_actions.invoice_pdf_pattern", "")
        env.ref("deltatech_actions.ir_cron_delete_pdf_attachments_invoice").active = False

        # trei PDF-uri de factură vechi de 200 de zile, de câte 200 KB
        past = datetime.now() - relativedelta(days=200)
        for number in range(1, 4):
            att = env["ir.attachment"].create(
                {
                    "name": f"Factura FCT{number:05d}.pdf",
                    "res_model": "account.move",
                    "type": "binary",
                    "raw": b"%PDF-1.4 " + b"0" * 200 * 1024,
                    "mimetype": "application/pdf",
                }
            )
            env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past, att.id))

        # acțiunea server din pasul 6, așa cum o creează administratorul
        cls.force_cancel_action = env["ir.actions.server"].create(
            {
                "name": "Anulare forțată comandă",
                "model_id": env.ref("sale.model_sale_order").id,
                "state": "code",
                "code": "record.force_cancel_order_and_moves()",
            }
        )
        env.flush_all()
        cls.settings_action = env.ref("base.res_config_setting_act_window")

    def test_capture_fise(self):
        settings = {
            "url": f"action={self.settings_action.id}",
            "wait": "div[name='dt_actions_invoice_pdf_active']",
            "timeout": 60000,
            "settle": 2000,
        }
        self.capture_screenshots(
            [
                # 1. Secțiunea Curățare bază de date din Setări generale
                {
                    **settings,
                    "name": "01_sectiune_curatare.png",
                    "eval": SCROLL_TO_SECTION,
                    "highlight": [INVOICE_BOX],
                },
                # 2. Parametrii curățării PDF-urilor de factură
                {
                    **settings,
                    "name": "02_parametri.png",
                    "eval": SCROLL_TO_INVOICE_BOX,
                    "highlight": [
                        "div[name='dt_actions_invoice_pdf_dry_run']",
                        "div[name='dt_actions_invoice_pdf_limit']",
                        "div[name='dt_actions_invoice_pdf_max_date_days']",
                        "div[name='dt_actions_invoice_pdf_pattern']",
                    ],
                },
                # 3. Rulează acum, în rulare de test: notificarea cu ce s-ar șterge
                {
                    **settings,
                    "name": "03_rulare_test.png",
                    "eval": RUN_NOW,
                    "eval_wait": 100,
                    "settle": 300,
                    "highlight": [".o_notification", "button[name='action_dt_actions_run_invoice_pdf']"],
                },
            ]
        )
        # 4. Curățarea activată și rularea de test debifată, ca la trecerea în producție.
        # Bifa din titlul setării cere salvarea și reîncarcă Setările, așa că starea se
        # pregătește aici, iar captura arată rezultatul și rularea reală.
        self.env.ref("deltatech_actions.ir_cron_delete_pdf_attachments_invoice").active = True
        self.env["ir.config_parameter"].sudo().set_param("deltatech_actions.invoice_pdf_dry_run", "False")
        self.env.flush_all()
        self.capture_screenshots(
            [
                # 4. Activarea, rularea de test debifată și rularea reală
                {
                    **settings,
                    "name": "04_activare_rulare.png",
                    "eval": RUN_NOW,
                    "eval_wait": 100,
                    "settle": 300,
                    "highlight": [
                        "div[name='dt_actions_invoice_pdf_active']",
                        "div[name='dt_actions_invoice_pdf_dry_run']",
                        "div[name='dt_actions_invoice_pdf_nextcall']",
                        ".o_notification",
                    ],
                },
                # 5. Copii restaurate: curățările rulate și din auto-vacuum
                {
                    **settings,
                    "name": "05_copie_staging.png",
                    "eval": SCROLL_TO_AUTOVACUUM,
                    "highlight": ["div[name='dt_actions_autovacuum']"],
                },
                # 6. Acțiunea server pentru anularea forțată
                {
                    "url": f"id={self.force_cancel_action.id}&model=ir.actions.server&view_type=form",
                    "name": "06_anulare_fortata.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "highlight": ["div[name='model_id']", "div[name='state']", "div[name='code']"],
                },
            ]
        )
