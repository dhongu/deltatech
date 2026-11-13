# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Prețul fără TVA pe pagina produsului din magazin" —
# RO pentru fișă (static/description/) și EN (static/description/en/) pentru USAGE.md.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_website_price_without_tax,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# fără bara de administrare a site-ului, ca pagina să arate ca pentru vizitator
HIDE_ADMIN_BAR = """
    document.querySelectorAll('#oe_main_menu_navbar, .o_main_navbar, .o_frontend_to_backend_nav, #website_cookies_bar')
        .forEach((e) => { e.style.display = 'none'; });
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPriceWithoutTaxScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_website_price_without_tax"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Magazin Demo SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        cls.website = env["website"].search([], limit=1)
        cls.website.company_id = company
        cls.website.sudo().show_line_subtotals_tax_selection = "tax_included"
        # site-ul în română (pagina produsului vine în limba site-ului, nu a utilizatorului)
        ro = env["res.lang"].with_context(active_test=False).search([("code", "=", "ro_RO")])
        cls.website.sudo().write({"language_ids": [Command.link(ro.id)], "default_lang_id": ro.id})

        tax = env["account.tax"].create(
            {
                "name": "TVA 21%",
                "type_tax_use": "sale",
                "amount": 21,
                "price_include_override": "tax_excluded",
                "company_id": company.id,
            }
        )
        categ = env["product.public.category"].create({"name": "Mobilier"})
        cls.product = env["product.template"].create(
            {
                "name": "Birou de lucru stejar",
                "type": "consu",
                "list_price": 100.0,
                "sale_ok": True,
                "is_published": True,
                "website_id": False,
                "taxes_id": [Command.set(tax.ids)],
                "public_categ_ids": [Command.set(categ.ids)],
                "company_id": company.id,
            }
        )
        cls.view = env.ref("deltatech_website_price_without_tax.product_price_without_tax")
        env.flush_all()

    def _price_shot(self, name, lang_url=""):
        return {
            "path": (f"/{lang_url}" if lang_url else "") + self.product.website_url,
            "name": name,
            "wait": "#product_details",
            "eval": HIDE_ADMIN_BAR,
            "highlight": [".oe_price_without_tax"],
            "settle": 2500,
        }

    def _capture(self, lang):
        kwargs = {"lang": lang, "hide_systray": True}
        url_lang = "en" if lang == "en_US" else ""
        # Pasul 1: prețurile afișate cu TVA
        self.website.sudo().show_line_subtotals_tax_selection = "tax_included"
        self.env.flush_all()
        self.capture_screenshots([self._price_shot("01_pret_cu_tva.png", url_lang)], viewport=(1920, 520), **kwargs)
        # Pasul 2: prețurile afișate fără TVA
        self.website.sudo().show_line_subtotals_tax_selection = "tax_excluded"
        self.env.flush_all()
        self.capture_screenshots([self._price_shot("02_pret_fara_tva.png", url_lang)], viewport=(1920, 520), **kwargs)
        # Pasul 3: vizualizarea opțională, în Setări → Tehnic → Vizualizări
        self.capture_screenshots(
            [
                {
                    "path": f"/odoo/ir.ui.view/{self.view.id}?debug=1",
                    "name": "03_vizualizare_activa.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='active']", "div[name='name']"],
                    "settle": 2000,
                }
            ],
            **kwargs,
        )

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
