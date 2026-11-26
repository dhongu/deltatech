# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Sortarea produselor din magazin după vânzări, vizite, recenzii
# și stoc": lista Sortare după, magazinul sortat după vânzări, sortarea implicită din editor și
# acțiunea planificată. Aceleași shot-uri în RO pentru fișă și în EN pentru readme/USAGE.md.
#
# Seed: cinci produse publicate și comenzi confirmate cu cantități diferite, apoi calculul
# statisticilor, ca ordinea „Cele mai bune vânzări" să fie cea din fișă.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_sale_sort,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_sale_sort:TestWebsiteSaleSortScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

VIEWPORT = (1440, 900)
SORT_TOGGLE = ".o_sortby_dropdown .dropdown-toggle"
# ecusonul evidențierii stă în stânga elementului: părinții care taie conținutul îl ascundeau
UNCLIP_JS = """(sel) => {
    for (const start of document.querySelectorAll(sel)) {
        for (let el = start; el && el !== document.body; el = el.parentElement) {
            el.style.overflow = "visible";
        }
    }
}"""
NEW_SORT_ITEMS = ", ".join(
    f".o_sortby_dropdown a.dropdown-item[href*='{field}']"
    for field in ("sales_count2", "visit_count", "rating_count2", "rating_avg2", "in_stock")
)

# denumire, preț, cantitate vândută
PRODUCTS = [
    ("Suport monitor dublu", 289.0, 0),
    ("Lampă de birou LED", 149.0, 4),
    ("Scaun de birou ergonomic", 899.0, 12),
    ("Covoraș pentru scaun", 119.0, 2),
    ("Birou reglabil electric", 1890.0, 7),
]


@tagged("-at_install", "post_install", "fise_screenshots")
class TestWebsiteSaleSortScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_sale_sort"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company()
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})

        # site-ul în română; capturile USAGE.md trec limba implicită pe engleză
        cls.website = env["website"].search([("company_id", "=", company.id)], limit=1)
        langs = env["res.lang"].search([("code", "in", ("ro_RO", "en_US"))])
        ro = langs.filtered(lambda lang: lang.code == "ro_RO")
        cls.website.write({"language_ids": [Command.set(langs.ids)], "default_lang_id": ro.id})

        # doar produsele seed-ului în magazin
        env["product.template"].search([("is_published", "=", True)]).is_published = False
        Template = env["product.template"]
        templates = Template
        for name, price, _qty in PRODUCTS:
            templates |= Template.create(
                {
                    "name": name,
                    "list_price": price,
                    "is_storable": True,
                    "is_published": True,
                    "website_id": False,
                }
            )

        partner = env["res.partner"].create({"name": "Client Demo SRL"})
        lines = [
            Command.create({"product_id": tmpl.product_variant_id.id, "product_uom_qty": qty})
            for tmpl, (_name, _price, qty) in zip(templates, PRODUCTS, strict=True)
            if qty
        ]
        order = env["sale.order"].create({"partner_id": partner.id, "order_line": lines})
        order.action_confirm()
        env.flush_all()
        templates._update_statistics()

        cls.cron = env.ref("deltatech_website_sale_sort.ir_cron_product_sale_scheduled")
        cls.cron_action = env.ref("base.ir_cron_act")
        env.flush_all()

    def _shots(self):
        return [
            # Pasul 1 — lista Sortare după deschisă, cu cele cinci criterii noi
            {
                "path": "/shop",
                "name": "01_optiuni_sortare.png",
                "wait": ".o_sortby_dropdown",
                "click_btn": SORT_TOGGLE,
                "wait_after": ".o_sortby_dropdown .dropdown-menu.show",
                "eval": f'({UNCLIP_JS})(".o_sortby_dropdown .dropdown-menu")',
                "highlight": [SORT_TOGGLE, NEW_SORT_ITEMS],
                "settle": 1500,
            },
            # Pasul 2 — magazinul sortat după Cele mai bune vânzări
            {
                "path": "/shop?order=sales_count2+desc",
                "name": "02_magazin_cele_mai_vandute.png",
                "wait": ".oe_product",
                "highlight": [SORT_TOGGLE, ".oe_product:nth-child(-n+3)"],
                "settle": 1500,
            },
            # Pasul 3 — sortarea implicită, din editorul de site
            {
                "path": "/odoo/action-website.website_preview?path=%2Fshop&enable_editor=1",
                "name": "03_sortare_implicita_editor.png",
                "wait": ".o_builder_sidebar_open .o-snippets-tabs",
                "timeout": 40000,
                # click real în iframe: editorul selectează grila la evenimentele browserului
                "click_btn": "iframe >> internal:control=enter-frame >> #o_wsale_container",
                "wait_after": ".o_customize_tab .hb-row[data-label]",
                "eval": f'({UNCLIP_JS})(".o_customize_tab .hb-row[data-label] .o-hb-select-toggle")',
                "highlight": {
                    "ro_RO": ".o_customize_tab .hb-row[data-label='Sortare Implicită'] .o-hb-select-toggle",
                    "en_US": ".o_customize_tab .hb-row[data-label='Default Sort'] .o-hb-select-toggle",
                },
                "settle": 2500,
            },
            # Pasul 4 — acțiunea planificată care recalculează cifrele
            {
                "url": f"action={self.cron_action.id}&id={self.cron.id}&model=ir.cron&view_type=form",
                "name": "04_actiune_planificata.png",
                "wait": ".o_form_view",
                "highlight": [
                    "label[for^='interval_number'], div[name='interval_number']",
                    "button[name='method_direct_trigger']",
                ],
                "settle": 1500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=VIEWPORT)

    def test_capture_usage(self):
        # editorul deschide în modul traducere o pagină în altă limbă decât cea implicită
        self.website.default_lang_id = self.env.ref("base.lang_en")
        self.env.flush_all()
        self.capture_screenshots(self._shots(), viewport=VIEWPORT, lang="en_US")
