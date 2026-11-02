# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Anunțarea paginilor noi prin IndexNow": setarea din Website,
# fișierul cheii și rezultatul trimiterii. Aceleași shot-uri în RO pentru fișă și în EN pentru
# readme/USAGE.md. Trimiterea către api.indexnow.org e simulată: capturile nu ies din test.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_indexnow,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from unittest.mock import MagicMock, patch

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

POST = "odoo.addons.deltatech_website_indexnow.models.website.requests.post"
KEY = "9c42dc26ca5946e4b661082db126af42"
SETTING = "#indexnow_setting"

# titlul secțiunii Urmărire și SEO sus, cu setarea IndexNow în cadru
SCROLL_TO_SETTING = """() => {
    const block = document.querySelector('#indexnow_setting').closest('.o_settings_container');
    (block.previousElementSibling || block).scrollIntoView({block: 'start'});
}"""

# fișierul cheii, cu adresa lui deasupra: răspunsul real al serverului, într-o fereastră de browser
KEY_FILE_HTML = """<div style="font-family: system-ui, sans-serif; width: 760px; margin: 16px;
    border: 1px solid #d0d4da; border-radius: 8px; overflow: hidden; background: #fff">
  <div style="background: #f1f3f4; padding: 10px 14px; border-bottom: 1px solid #d0d4da">
    <div style="background: #fff; border-radius: 16px; padding: 6px 14px; font-size: 14px;
        color: #202124">{url}</div>
  </div>
  <pre style="margin: 0; padding: 16px 14px 40px; font-size: 14px">{content}</pre>
</div>"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestIndexNowScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_indexnow"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        cls.website = cls.env["website"].get_current_website()
        cls.website.write(
            {
                "name": "Grădina Demo",
                "domain": "https://www.gradina-demo.ro",
                "indexnow_enabled": True,
                "indexnow_key": KEY,
            }
        )
        cls.settings_action = cls.env.ref("website.action_website_configuration")

    def _shots(self):
        return [
            # 1. Setarea IndexNow din Website → Configurare → Setări
            {
                "url": f"action={self.settings_action.id}",
                "name": "01_setare_indexnow.png",
                "wait": SETTING,
                "timeout": 60000,
                "settle": 2000,
                "eval": SCROLL_TO_SETTING,
                "highlight": [
                    "div[name='indexnow_enabled']",
                    "div[name='indexnow_key']",
                    f"{SETTING} div[name='indexnow_key_url']",
                ],
            },
            # 2. Fișierul cheii, servit la /<cheie>.txt
            {
                "html": KEY_FILE_HTML.format(
                    url=self.website.indexnow_key_url, content=self.url_open(f"/{KEY}.txt").text
                ),
                "name": "02_fisier_cheie.png",
            },
            # 3. Trimite acum toate paginile: notificarea cu numărul de adrese trimise
            {
                "url": f"action={self.settings_action.id}",
                "name": "03_trimitere_pagini.png",
                "wait": SETTING,
                "timeout": 60000,
                "eval": SCROLL_TO_SETTING,
                "click_btn": "button[name='action_indexnow_submit_all']",
                "wait_after": ".o_notification",
                "settle": 1500,
                "highlight": ["button[name='action_indexnow_submit_all']", ".o_notification"],
            },
        ]

    def _capture(self, lang):
        self.website.indexnow_last_result = False
        with patch(POST, return_value=MagicMock(status_code=202)):
            self.capture_screenshots(self._shots(), viewport=(1280, 800), lang=lang)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
