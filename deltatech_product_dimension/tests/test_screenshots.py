# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Dimensiunile produsului și calculul volumului" —
# generate în timpul testelor, în limba RO, pe compania „RO Company" în RON.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_product_dimension,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestProductDimensionScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_product_dimension"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots / l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        # pe baze cu mai multe companii „RO Company" poate exista deja: lucrăm pe ea
        ro_company = cls.env["res.company"].search([("name", "=", "RO Company")], limit=1)
        if ro_company:
            admin = cls.env.ref("base.user_admin")
            admin.write({"company_ids": [(4, ro_company.id)], "company_id": ro_company.id})
            cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[ro_company.id]))
        cls.prepare_ro_company()
        # volumul se calculează din formular (onchange); în seed îl scriem explicit,
        # cu aceeași formulă ca modulul: lungime × lățime × înălțime / 1.000.000
        cls.box = cls.env["product.template"].create(
            {
                "name": "Cutie carton 40×30×25",
                "type": "consu",
                "product_length": 40,
                "product_width": 30,
                "product_height": 25,
                "volume": 40 * 30 * 25 / 1000000,
            }
        )

    def _shots(self):
        url = f"id={self.box.id}&model=product.template&view_type=form"
        tab = {"ro_RO": "Inventar", "en_US": "Inventory"}
        return [
            {
                "url": url,
                "name": "01_produs_dimensiuni.png",
                "wait": ".o_form_view",
                "click_tab": tab["ro_RO"],
                "highlight": ["div[name='product_length']", "div[name='product_width']", "div[name='product_height']"],
                "settle": 2000,
            },
            {
                "url": url,
                "name": "02_volum_calculat.png",
                "wait": ".o_form_view",
                "click_tab": tab["ro_RO"],
                "highlight": ["div[name='volume'] input"],
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())
