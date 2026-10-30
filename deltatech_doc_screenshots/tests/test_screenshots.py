# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Capturile fișei consultant a uneltei: același ecran în RO (fișa) și în EN (USAGE.md)."""

from odoo.tests import tagged

from .screenshot_case import ScreenshotCase


@tagged("-at_install", "post_install", "fise_screenshots")
class TestDocScreenshotsScreenshots(ScreenshotCase):
    screenshots_module = "deltatech_doc_screenshots"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.prepare_ro_company()

    def _shots(self):
        action = self.env.ref("base.action_res_company_form")
        return [
            # formularul companiei demo, cu câmpurile evidențiate ①②
            {
                "url": f"action={action.id}&id={self.company.id}&model=res.company&view_type=form",
                "name": "01_formular_companie.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='name']", "div[name='vat']"],
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")
