# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Procesarea rapidă a cozii de joburi", în RO (fișa) și EN
# (readme/USAGE.md).
#
# Seedează o cheie API demonstrativă și câteva joburi în stările vizibile implicit în listă
# (în așteptare, în coadă, eșuat). Butonul „Procesează în fundal" nu este apăsat: pornește
# un fir de execuție pe altă conexiune, care nu vede datele tranzacției de test. Apelul
# extern de la pasul 2 este ilustrat cu răspunsul real al adresei de statistici, care nu
# modifică joburile (adresa de procesare le-ar rula și ar schimba lista din pașii următori).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_queue_job,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import html
import json
import unittest
import uuid
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

DEMO_API_KEY = "demo-cheie-api-pentru-documentatie-0123456789"

JOBS = [
    ("Sincronizare stoc marketplace", "product.product", "pending", 10),
    ("Actualizare prețuri produse", "product.template", "pending", 10),
    ("Trimitere factură e-Factura", "account.move", "enqueued", 5),
    ("Import comenzi magazin online", "sale.order", "failed", 10),
]

ROW_SELECTOR = "tr.o_data_row:first-child .o_list_record_selector"

API_LABELS = {
    "ro_RO": ("Cererea trimisă de serviciul extern", "Răspunsul Odoo", "cheia API"),
    "en_US": ("Request sent by the external service", "Odoo response", "API key"),
}

API_PAGE = """<html><head><meta charset="utf-8"><style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; color: #212529; }}
h3 {{ font-size: 16px; margin: 0 0 8px; color: #714b67; }}
pre {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px;
       font-size: 13px; margin: 0 0 20px; width: 760px; white-space: pre-wrap; }}
</style></head><body>
<h3>{request_label}</h3><pre>{request}</pre>
<h3>{response_label}</h3><pre>{response}</pre>
</body></html>"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestQueueJobScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_queue_job"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.activate_ro_lang()
        cls.force_light_theme()
        cls.env["ir.config_parameter"].sudo().set_param("queue_job_processor.api_key", DEMO_API_KEY)
        # lista arată implicit doar joburile active; ștergem ce a rămas din alte teste
        cls.env["queue.job"].search([]).unlink()  # pylint: disable=no-search-all
        for minutes, (name, model, state, priority) in enumerate(JOBS, start=1):
            cls.env["queue.job"].create(
                {
                    "uuid": str(uuid.uuid4()),
                    "name": name,
                    "model_name": model,
                    "method_name": "write",
                    "state": state,
                    "priority": priority,
                    "channel": "root",
                    "date_created": fields.Datetime.now() - timedelta(minutes=minutes),
                }
            )
        cls.settings_action = cls.env.ref("deltatech_queue_job.action_queue_job_config").id
        cls.jobs_action = cls.env.ref("queue_job.action_queue_job").id

    def _api_shot(self):
        """Cererea și răspunsul real al adresei de statistici, ca pagină HTML, per limbă."""
        body = {"jsonrpc": "2.0", "params": {"api_key": DEMO_API_KEY}}
        response = self.url_open("/api/v1/queue/stats", json=body).json()
        response["result"]["result"]["stats"]["timestamp"] = "2026-11-01 04:40:00"
        pages = {}
        for lang, (request_label, response_label, key_label) in API_LABELS.items():
            shown = {"jsonrpc": "2.0", "params": {"api_key": f"<{key_label}>"}}
            request = "POST https://<odoo>/api/v1/queue/stats\nContent-Type: application/json\n\n" + json.dumps(
                shown, indent=2
            )
            pages[lang] = API_PAGE.format(
                request_label=request_label,
                request=html.escape(request),
                response_label=response_label,
                response=html.escape(json.dumps(response, indent=2)),
            )
        return {"html": pages, "name": "02_raspuns_api.png", "full": True}

    def _shots(self):
        return [
            {
                "url": f"action={self.settings_action}",
                "name": "01_setari_procesor_extern.png",
                "wait": "div[name='queue_job_processor_batch_size']",
                "timeout": 60000,
                "eval": "document.querySelector(\"[name='queue_job_processor']\").scrollIntoView({block: 'start'})",
                "highlight": [
                    "button[name='action_generate_queue_job_processor_api_key']",
                    "div[name='queue_job_processor_batch_size']",
                    "div[name='queue_job_processor_max_seconds']",
                ],
                "settle": 2000,
            },
            self._api_shot(),
            {
                "url": f"action={self.jobs_action}&view_type=list",
                "name": "03_lista_joburi.png",
                "wait": ".o_list_view .o_data_row",
                "click_btn": ROW_SELECTOR,
                "wait_after": "button[name='process_jobs']",
                "highlight": [
                    "button[name='start_cron_trigger']",
                    "button[name='action_process_api_thread']",
                    "button[name='process_jobs']",
                ],
            },
            {
                "url": f"action={self.jobs_action}&view_type=list",
                "name": "04_declansare_cron.png",
                "wait": ".o_list_view .o_data_row",
                "click_btn": "button[name='start_cron_trigger']",
                "wait_after": ".o_notification",
                "highlight": [".o_notification"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
