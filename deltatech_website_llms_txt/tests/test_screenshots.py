# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Rezumatul site-ului pentru asistenții AI (llms.txt)": setarea
# din Website, tabul llms.txt al website-ului și fișierul /llms.txt generat. Aceleași shot-uri
# în RO pentru fișă și în EN pentru readme/USAGE.md; textele sunt scrise în limba capturii.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_llms_txt,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

SETTING = "#llms_txt_setting"

SCROLL_TO_SETTING = """() => {
    document.querySelector('#llms_txt_setting').scrollIntoView({block: 'center'});
}"""

TEXTS = {
    "ro_RO": {
        "summary": "Magazin online de unelte de grădină, cu livrare în toată România.",
        "details": "## Livrare\n\nComenzile plecate până la ora 14 ajung în 24–48 de ore.",
        "page": "Livrare și retur",
        "home": "Unelte de grădină pentru casă și fermă.",
        "contact": "Telefonul, emailul și programul magazinului.",
        "description": "Costurile și termenele de livrare, plus returul în 14 zile.",
    },
    "en_US": {
        "summary": "Online shop for garden tools, with delivery all over Romania.",
        "details": "## Delivery\n\nOrders placed before 2 PM arrive in 24–48 hours.",
        "page": "Delivery and returns",
        "home": "Garden tools for home and farm.",
        "contact": "The phone, email and opening hours of the shop.",
        "description": "Delivery costs and times, plus returns within 14 days.",
    },
}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestLlmsTxtScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_llms_txt"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        cls.website = cls.env["website"].get_current_website()
        cls.website.write({"name": "Grădina Demo", "domain": "https://www.gradina-demo.ro"})
        cls.settings_action = cls.env.ref("website.action_website_configuration")

    def _prepare(self, lang):
        texts = TEXTS[lang]
        # fișierul e în limba implicită a website-ului: română pentru fișă, engleză pentru USAGE.md
        site_lang = self.env["res.lang"]._activate_lang(lang)
        self.website.write(
            {
                "language_ids": [(4, site_lang.id)],
                "default_lang_id": site_lang.id,
                "llms_txt_summary": texts["summary"],
                "llms_txt_details": texts["details"],
            }
        )
        pages = self.env["website.page"].search([("website_id", "in", (False, self.website.id))])
        for url, key in (("/", "home"), ("/contactus", "contact")):
            pages.filtered(lambda page, url=url: page.url == url).website_meta_description = texts[key]
        # o pagină ca în temă: descrierea e în șablon, nu în setările SEO ale paginii
        view = self.env["ir.ui.view"].create(
            {
                "name": texts["page"],
                "type": "qweb",
                "arch": f'<t><t t-set="website_meta_description">{texts["description"]}</t><div/></t>',
            }
        )
        self.env["website.page"].create(
            {
                "url": "/delivery-returns",
                "view_id": view.id,
                "website_id": self.website.id,
                "is_published": True,
            }
        )
        self.env.flush_all()

    def _shots(self):
        return [
            # 1. Setarea llms.txt din Website → Configurare → Setări
            {
                "url": f"action={self.settings_action.id}",
                "name": "01_setare_llms_txt.png",
                "wait": SETTING,
                "timeout": 60000,
                "settle": 2000,
                "eval": SCROLL_TO_SETTING,
                "highlight": [
                    "div[name='llms_txt_enabled']",
                    "button[name='action_open_llms_txt']",
                    f"{SETTING} div[name='llms_txt_url']",
                ],
            },
            # 2. Tabul llms.txt de pe formularul website-ului
            {
                "url": f"id={self.website.id}&model=website&view_type=form",
                "name": "02_tab_llms_txt.png",
                "wait": ".o_form_view",
                "click_tab": "llms.txt",
                "settle": 2000,
                "highlight": [
                    "div[name='llms_txt_summary']",
                    "div[name='llms_txt_details']",
                    "div[name='llms_txt_url']",
                ],
            },
            # 3. Fișierul /llms.txt generat
            {"path": "/llms.txt", "name": "03_fisier_llms_txt.png", "wait": "body", "full": True},
        ]

    def test_capture_fise(self):
        self._prepare("ro_RO")
        self.capture_screenshots(self._shots(), viewport=(1280, 800))

    def test_capture_usage(self):
        self._prepare("en_US")
        self.capture_screenshots(self._shots(), viewport=(1280, 800), lang="en_US")
