# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Stocul pe depozite pe pagina produsului din magazin" —
# generate în timpul testelor, cu interfața și site-ul în RO, pe compania „Demo Magazin SRL".
#
# Seed: trei depozite afișate pe site și un produs publicat, cu stocul:
#   - Depozit București: 50 buc. (peste pragul de 10 -> „Disponibil");
#   - Depozit Cluj: 4 buc. (sub prag -> cantitatea exactă);
#   - Depozit Iași: 0 buc. („Stoc epuizat" / „La comandă").
# Depozitul „Showroom" există, dar nu e afișat pe site.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_warehouse_stock,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_warehouse_stock:TestWarehouseStockScreenshots --stop-after-init
import unittest
from urllib.parse import quote

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

VIEWPORT = (1920, 1080)
# aduce blocul stocului pe depozite în mijlocul ecranului
SCROLL_BLOCK_JS = "document.querySelector('.o_wh_stock').scrollIntoView({block: 'center'})"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestWarehouseStockScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_warehouse_stock"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        admin.group_ids = [Command.link(env.ref("stock.group_stock_manager").id)]

        # site-ul în română: limba implicită, fără prefix în adresă
        cls.website = env["website"].search([("company_id", "=", company.id)], limit=1)
        ro = env["res.lang"].search([("code", "=", "ro_RO")], limit=1)
        cls.website.write({"language_ids": [Command.link(ro.id)], "default_lang_id": ro.id})

        Warehouse = env["stock.warehouse"]
        warehouses = Warehouse.search([("company_id", "=", company.id)])
        cls.wh_bucuresti = warehouses[0]
        cls.wh_bucuresti.name = "Depozit București"
        (warehouses - cls.wh_bucuresti).website_stock_display = False
        cls.wh_cluj = Warehouse.create({"name": "Depozit Cluj", "code": "CJ", "company_id": company.id})
        cls.wh_iasi = Warehouse.create({"name": "Depozit Iași", "code": "IS", "company_id": company.id})
        cls.wh_showroom = Warehouse.create(
            {"name": "Showroom", "code": "SHW", "company_id": company.id, "website_stock_display": False}
        )

        cls.product = env["product.product"].create(
            {
                "name": "Mașină de găurit cu acumulator 18V",
                "default_code": "MG-18V",
                "is_storable": True,
                "list_price": 549.0,
                "is_published": True,
                "website_id": False,
            }
        )
        quant = env["stock.quant"].sudo()
        quant._update_available_quantity(cls.product, cls.wh_bucuresti.lot_stock_id, 50)
        quant._update_available_quantity(cls.product, cls.wh_cluj.lot_stock_id, 4)
        quant._update_available_quantity(cls.product, cls.wh_showroom.lot_stock_id, 2)

        cls.settings_action = env.ref("website.action_website_configuration")
        cls.warehouse_action = env.ref("stock.action_warehouse_form")
        env.flush_all()

    def _set_design(self, **vals):
        self.website.write({f"warehouse_stock_{key}": value for key, value in vals.items()})
        self.env.flush_all()

    def _product_shot(self, name, highlight=".o_wh_stock", **kw):
        shot = {
            "path": self.product.product_tmpl_id.website_url,
            "name": name,
            "wait": ".o_wh_stock",
            "eval": SCROLL_BLOCK_JS,
            "highlight": highlight,
            "settle": 2000,
        }
        shot.update(kw)
        return shot

    def test_capture_fise(self):
        # Pasul 1 — depozitul, cu bifa „Afișare pe site"; Pasul 2 — setările site-ului
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.warehouse_action.id}&id={self.wh_cluj.id}"
                    "&model=stock.warehouse&view_type=form",
                    "name": "01_depozit_afisare_site.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='website_stock_display']"],
                },
                {
                    "url": f"action={self.settings_action.id}",
                    "name": "02_setari_stoc_depozite.png",
                    "wait": "#warehouse_stock_design_setting",
                    "timeout": 60000,
                    "eval": "document.querySelector('#warehouse_stock_design_setting')"
                    ".scrollIntoView({block: 'center'})",
                    "highlight": ["#warehouse_stock_threshold_setting", "#warehouse_stock_design_setting"],
                    "settle": 2500,
                },
                # Pasul 3 — pagina produsului, stilul implicit (etichete)
                self._product_shot("03_pagina_produs_etichete.png"),
            ],
            viewport=VIEWPORT,
        )

        # Pasul 4 — listă cu pictograme, „La comandă" cu notă
        self._set_design(style="list", zero_message="on_order", zero_note="Livrare în 3-5 zile")
        self.capture_screenshots([self._product_shot("04_stil_lista_la_comanda.png")], viewport=VIEWPORT)

        # Pasul 5 — card, pe culorile temei
        self._set_design(style="card", theme_colors=True)
        self.capture_screenshots([self._product_shot("05_stil_card.png")], viewport=VIEWPORT)

        # Pasul 6 — selectorul de depozit: clientul alege Cluj și apasă „Verifică stocul"
        self._set_design(style="selector", theme_colors=False)
        select_js = (
            SCROLL_BLOCK_JS + ";"
            "const sel = document.querySelector('.o_wh_stock_select');"
            "sel.value = [...sel.options].find((o) => o.text.includes('Cluj')).value;"
            "document.querySelector('.o_wh_stock_check').click();"
        )
        self.capture_screenshots(
            [
                self._product_shot(
                    "06_stil_selector.png",
                    highlight=[".o_wh_stock_select", ".o_wh_stock_check", ".o_wh_stock_result"],
                    eval=select_js,
                ),
            ],
            viewport=VIEWPORT,
        )

        # Pasul 7 — după preț, doar starea
        self._set_design(position="after_price", style="badges", zero_message="out_of_stock", qty_display="status_only")
        self.capture_screenshots(
            [
                self._product_shot(
                    "07_dupa_pret_doar_starea.png",
                ),
            ],
            viewport=VIEWPORT,
        )

        # Pasul 8 — opțiunile blocului în editorul de website
        self._set_design(position="details", qty_display="exact")
        path = quote(self.product.product_tmpl_id.website_url, safe="")
        self.capture_screenshots(
            [
                {
                    "path": f"/odoo/action-website.website_preview?path={path}&enable_editor=1",
                    "name": "08_editor_optiuni.png",
                    "wait": ".o_builder_sidebar_open .o-snippets-tabs",
                    "timeout": 40000,
                    # click real în iframe: editorul selectează blocul la evenimentele browserului
                    "click_btn": "iframe >> internal:control=enter-frame >> .o_wh_stock",
                    "wait_after": ".o_customize_tab [data-container-title]",
                    "highlight": [".o_customize_tab .options-container:has-text('Stoc pe depozite')"],
                    "settle": 2500,
                },
            ],
            viewport=VIEWPORT,
        )
