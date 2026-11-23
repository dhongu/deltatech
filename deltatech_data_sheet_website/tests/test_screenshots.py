# © 2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Fișa tehnică și fișa de securitate pe pagina produsului din magazin".
#
# Seedează o companie RO cu site-ul aliniat la ea, un produs cu ambele fișe și un produs cu un
# document standard și fișa tehnică, apoi pozează formularul produsului și paginile din magazin.
#
# Rulare — RESTRÂNSĂ LA CLASĂ, altfel se rescriu capturile tuturor modulelor cu test de fișe:
#   FISE_SCREENSHOTS=1 ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_data_sheet_website,deltatech_doc_screenshots \
#       --test-tags=/deltatech_data_sheet_website:TestDataSheetWebsiteScreenshots --stop-after-init
import base64
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

PDF = base64.b64encode(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF")

# bara de editare a site-ului, vizibilă doar pentru utilizatorul autentificat: nu o vede vizitatorul
HIDE_EDITOR = (
    "const st = document.createElement('style');"
    "st.textContent = '#oe_main_menu_navbar, .o_frontend_to_backend_nav, header#top { display: none !important; }';"
    "document.head.appendChild(st);"
    "document.querySelector('#product_documents')?.scrollIntoView({block: 'center'})"
)


@tagged("-at_install", "post_install", "fise_screenshots")
class TestDataSheetWebsiteScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_data_sheet_website"

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

        def attachment(name):
            return env["ir.attachment"].create(
                {"name": name, "datas": PDF, "mimetype": "application/pdf", "public": True}
            )

        cls.product = env["product.template"].create(
            {
                "name": "Vopsea epoxidică bicomponentă 5 kg",
                "type": "consu",
                "list_price": 289.0,
                "sale_ok": True,
                "website_published": True,
                "company_id": cls.company.id,
                "data_sheet_id": attachment("Fișă tehnică.pdf").id,
                "safety_data_sheet_id": attachment("Fișă securitate.pdf").id,
            }
        )
        cls.product_docs = env["product.template"].create(
            {
                "name": "Diluant pentru vopsea epoxidică 1 l",
                "type": "consu",
                "list_price": 45.0,
                "sale_ok": True,
                "website_published": True,
                "company_id": cls.company.id,
                "data_sheet_id": attachment("Fișă tehnică diluant.pdf").id,
            }
        )
        env["product.document"].create(
            {
                "ir_attachment_id": attachment("Instrucțiuni de utilizare diluant.pdf").id,
                "res_model": "product.template",
                "res_id": cls.product_docs.id,
                "shown_on_product_page": True,
            }
        )
        cls.product_action = env.ref("sale.product_template_action")

    def _prefix(self):
        return {"ro_RO": "", "en_US": "/en"}

    def _shots(self):
        pre = self._prefix()
        return [
            {
                "url": (f"action={self.product_action.id}&id={self.product.id}&model=product.template&view_type=form"),
                "name": "01_formular_produs_fise.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Vânzări", "en_US": "Sales"},
                "highlight": ["div[name='data_sheet_id']", "div[name='safety_data_sheet_id']"],
                "eval": "document.querySelector(\"div[name='data_sheet_id']\")?.scrollIntoView({block:'center'})",
                "settle": 2500,
            },
            {
                "path": {k: f"{v}/shop/{self.product.id}" for k, v in pre.items()},
                "name": "02_pagina_produs_fise.png",
                "wait": "#product_documents",
                "eval": HIDE_EDITOR,
                "highlight": ["#product_documents"],
                "settle": 2500,
            },
            {
                "path": {k: f"{v}/shop/{self.product_docs.id}" for k, v in pre.items()},
                "name": "03_pagina_produs_documente.png",
                "wait": "#product_documents",
                "eval": HIDE_EDITOR,
                "highlight": ["#product_documents"],
                "settle": 2500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
