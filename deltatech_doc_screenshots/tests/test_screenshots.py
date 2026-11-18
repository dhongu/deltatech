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

    def _gif_steps(self):
        action = self.env.ref("base.action_partner_form")
        return [
            {"goto": f"action={action.id}&model=res.partner&view_type=form", "wait": ".o_form_view"},
            {
                "caption": {
                    "ro_RO": "Un partener nou începe cu denumirea",
                    "en_US": "A new partner starts with the name",
                }
            },
            {"type": "Ferma Verde SRL", "into": "name", "hold": 500},
            {"caption": {"ro_RO": "Apoi codul fiscal", "en_US": "Then the tax ID"}},
            {"type": "RO99999143", "into": "vat", "hold": 500},
            {
                "caption": {
                    "ro_RO": "La salvare, partenerul e gata de lucru",
                    "en_US": "Once saved, the partner is ready",
                }
            },
            {"click": ".o_form_button_save", "wait_after": ".o_form_saved", "hold": 2200},
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        """GIF-ul demo al uneltei (pilot pentru ``capture_gif``), în RO și EN."""
        # banner.json e în engleză: slide-ul RO primește textele lui
        intro_ro = {
            "title": "Capturi pentru documentație",
            "summary": "Capturile și demo-urile fișei generate din teste",
            "features": ["Capturi generate din teste", "Pași evidențiați", "GIF-uri demo"],
        }
        self.capture_gif(self._gif_steps(), name="demo.gif", intro=intro_ro)
        self.capture_gif(self._gif_steps(), name="demo.gif", lang="en_US")
