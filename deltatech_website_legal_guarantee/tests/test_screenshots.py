# © 2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Notificarea UE privind garanția legală pe site".
#
# Seedează o companie RO cu site-ul aliniat la ea și un produs publicat, apoi pozează setările
# Website, pagina /garantie, linkul din footer, linkul și fereastra de pe pagina produsului.
#
# Rulare — RESTRÂNSĂ LA CLASĂ, altfel se rescriu capturile tuturor modulelor cu test de fișe:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_legal_guarantee,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_legal_guarantee:TestLegalGuaranteeScreenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestLegalGuaranteeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_legal_guarantee"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        cls.company = cls.prepare_ro_company(name="Magazin Demo SRL")
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, cls.company.id)], "company_id": cls.company.id})
        cls.align_website_company(cls.company)
        cls.website = env["website"].search([("company_id", "=", cls.company.id)], limit=1)
        # site bilingv: RO pentru fișă, EN pentru USAGE.md
        cls.activate_ro_lang()
        ro = env["res.lang"].with_context(active_test=False).search([("code", "=", "ro_RO")])
        en = env["res.lang"].with_context(active_test=False).search([("code", "=", "en_US")])
        (ro | en).active = True
        langs = (ro | en) - cls.website.language_ids
        if langs:
            cls.website.language_ids = [(4, lang.id) for lang in langs]
        cls.website.default_lang_id = ro or en
        cls.website.write(
            {
                "legal_guarantee_footer": True,
                "legal_guarantee_product": True,
                "legal_guarantee_checkout": True,
            }
        )
        cls.product = env["product.template"].create(
            {
                "name": "Aspirator robot X200",
                "type": "consu",
                "list_price": 1299.0,
                "sale_ok": True,
                "website_published": True,
            }
        )
        cls.settings_action = env.ref("website.action_website_configuration")

    def _prefix(self):
        return {"ro_RO": "", "en_US": "/en"}

    def _shots(self):
        pre = self._prefix()
        return [
            {
                "url": f"action={self.settings_action.id}&view_type=form",
                "name": "01_setari_website.png",
                "wait": ".o_form_view",
                "timeout": 60000,
                "highlight": ["div[name='legal_guarantee_footer'], #legal_guarantee_setting"],
                "eval": "document.querySelector('#legal_guarantee_setting')?.scrollIntoView({block:'center'})",
                "settle": 2500,
            },
            {
                "path": {k: f"{v}/garantie" for k, v in pre.items()},
                "name": "02_pagina_garantie.png",
                "wait": ".o_legal_guarantee_page",
                "full": True,
                "settle": 2500,
            },
            {
                "path": {k: f"{v}/garantie" for k, v in pre.items()},
                "name": "03_footer_link.png",
                "wait": ".o_footer_legal_guarantee",
                "highlight": [".o_footer_legal_guarantee a"],
                "eval": "document.querySelector('footer')?.scrollIntoView({block:'end'})",
                "settle": 2500,
            },
            {
                "path": {k: f"{v}/shop/{self.product.id}" for k, v in pre.items()},
                "name": "04_pagina_produs_link.png",
                "wait": ".o_legal_guarantee_link",
                "highlight": [".o_legal_guarantee_link"],
                "settle": 2500,
            },
            {
                "path": {k: f"{v}/shop/{self.product.id}" for k, v in pre.items()},
                "name": "05_fereastra_notificare.png",
                "wait": ".o_legal_guarantee_link",
                "click_btn": ".o_legal_guarantee_link",
                "wait_after": "#o_legal_guarantee_modal.show img",
                "settle": 3000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
