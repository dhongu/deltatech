# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Liste de produse definite prin filtru" — generate
# în timpul testelor, în limba RO, pe compania „RO Company" în RON.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_product_list,deltatech_doc_screenshots \
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
class TestProductListScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_product_list"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots / l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_demo_company()
        env = cls.env
        categ = env["product.category"].create({"name": "Electrocasnice"})
        names = ["Fierbător electric 1,7 l", "Prăjitor de pâine", "Mixer vertical", "Cafetieră", "Storcător"]
        for name in names:
            env["product.product"].create({"name": name, "categ_id": categ.id, "sale_ok": True, "list_price": 150.0})
        env["product.product"].create(
            {"name": "Piesă de schimb mixer", "categ_id": categ.id, "sale_ok": False, "list_price": 25.0}
        )
        domain = f"[('sale_ok', '=', True), ('categ_id', '=', {categ.id})]"
        cls.product_list = env["product.list"].create(
            {"name": "Electrocasnice — feed eMAG", "products_domain": domain, "limit": 80, "company_id": company.id}
        )
        cls.archived_list = env["product.list"].create(
            {
                "name": "Catalog campanie vară",
                "products_domain": domain,
                "limit": 80,
                "active": False,
                "company_id": company.id,
            }
        )
        env["product.list"].create({"name": "Toate produsele vandabile", "limit": 500, "company_id": company.id})
        cls.action = env.ref("deltatech_product_list.action_product_list").id
        env.flush_all()

    def _shots(self):
        return [
            {
                "url": f"action={self.action}&view_type=list",
                "name": "01_liste_produse.png",
                "wait": ".o_list_view",
                "highlight": [".o-list-button-add, button.o_list_button_add"],
            },
            {
                "url": f"action={self.action}&id={self.product_list.id}&model=product.list&view_type=form",
                "name": "02_lista_formular_filtru.png",
                "wait": ".o_form_view",
                "settle": 3000,
                "highlight": ["div[name='name']", "div[name='products_domain']", "div[name='limit']"],
            },
            {
                "url": f"action={self.action}&id={self.archived_list.id}&model=product.list&view_type=form",
                "name": "03_lista_arhivata.png",
                "wait": ".o_form_view",
                "settle": 3000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())
