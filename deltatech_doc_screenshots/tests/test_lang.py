# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Teste pentru alegerea limbii în ``ScreenshotCase``, fără server Odoo și fără browser."""

import os
from types import SimpleNamespace

from odoo.tests import BaseCase, tagged

from .screenshot_case import ScreenshotCase, _for_lang


@tagged("post_install", "-at_install")
class TestScreenshotLang(BaseCase):
    def test_lang_map_picks_language(self):
        value = {"ro_RO": "button:has-text('Confirmă')", "en_US": "button:has-text('Confirm')"}
        self.assertEqual(_for_lang(value, "ro_RO"), "button:has-text('Confirmă')")
        self.assertEqual(_for_lang(value, "en_US"), "button:has-text('Confirm')")

    def test_lang_map_fallback(self):
        # limba lipsă ia varianta en_US, apoi prima
        self.assertEqual(_for_lang({"ro_RO": "ro", "en_US": "en"}, "de_DE"), "en")
        self.assertEqual(_for_lang({"ro_RO": "ro", "fr_FR": "fr"}, "de_DE"), "ro")

    def test_list_of_selectors(self):
        value = [{"ro_RO": "a:has-text('Salvează')", "en_US": "a:has-text('Save')"}, "div[name='partner_id']"]
        self.assertEqual(_for_lang(value, "en_US"), ["a:has-text('Save')", "div[name='partner_id']"])

    def test_plain_values_untouched(self):
        # un dict care nu e hartă de limbă (ex. contextul raportului) rămâne neatins
        context = {"allowed_company_ids": [1], "lang": "ro_RO"}
        self.assertIs(_for_lang(context, "en_US"), context)
        self.assertEqual(_for_lang({}, "en_US"), {})
        self.assertEqual(_for_lang(".o_form_view", "en_US"), ".o_form_view")
        self.assertTrue(_for_lang(True, "en_US"))

    def test_report_shot_follows_capture_lang(self):
        shot = ScreenshotCase.report_shot("account.report_invoice", 7, "05_factura.png", companies=False)
        self.assertNotIn("path", shot)
        self.assertEqual(shot["report_path"], "/report/html/account.report_invoice/7")
        # o limbă explicită rămâne fixă, în cale
        shot = ScreenshotCase.report_shot("account.report_invoice", 7, "05_factura.png", lang="ro_RO", companies=False)
        self.assertIn("%22lang%22%3A%20%22ro_RO%22", shot["path"])

    def test_screenshots_dir_per_lang(self):
        holder = SimpleNamespace(screenshots_module="deltatech_doc_screenshots")
        ro = ScreenshotCase.screenshots_dir(holder)
        en = ScreenshotCase.screenshots_dir(holder, "en_US")
        self.assertTrue(ro.endswith(os.path.join("static", "description")))
        self.assertEqual(en, os.path.join(ro, "en"))
