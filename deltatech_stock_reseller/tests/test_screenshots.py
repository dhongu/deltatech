# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Raport de stoc pentru revânzători" — generate în timpul testelor,
# în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: meniul Vânzări → Raportare → Locație stoc, fereastra cu locația, partenerul, lista de
# prețuri și pragurile de stoc, apoi lista rezultată (prețuri de revânzător și texte de stoc),
# grupată pe categorii.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_stock_reseller,deltatech_doc_screenshots \
#       --test-tags=/deltatech_stock_reseller:TestStockResellerScreenshots --stop-after-init
import ast
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# deschide meniul Raportare din aplicația Vânzări și, opțional, alege „Locație stoc"
OPEN_MENU_JS = """async () => {
    const until = async (selector) => {
        for (let i = 0; i < 100 && !document.querySelector(selector); i++) {
            await new Promise((resolve) => setTimeout(resolve, 100));
        }
        return document.querySelector(selector);
    };
    const toggles = [...document.querySelectorAll(".o_menu_sections .dropdown-toggle")];
    const reporting = toggles.find((el) => ["Raportare", "Reporting"].includes(el.textContent.trim()));
    reporting.click();
    const item = await until(".o-dropdown--menu [data-menu-xmlid='deltatech_stock_reseller.menu_stock_quant_report']");
    item.style.position = "relative";
    item.closest(".o-dropdown--menu").style.overflow = "visible";
    %s
}"""
CLICK_ITEM_JS = (
    'item.click(); await until(".modal-content div[name=location_id]");'
    " await new Promise((resolve) => setTimeout(resolve, 500)); document.activeElement.blur();"
)

EXPAND_GROUP_JS = """async () => {
    document.querySelector(".o_group_header").click();
    for (let i = 0; i < 50 && !document.querySelector(".o_data_row"); i++) {
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
    document.querySelectorAll(".o_list_table td, .o_list_table th").forEach((el) => {
        el.style.overflow = "visible";
    });
}"""

# celulele listei își taie conținutul; bulinele numerotate trebuie să iasă peste margine
UNCLIP_CELLS_JS = """() => document.querySelectorAll(".o_list_table td").forEach((el) => {
    el.style.overflow = "visible";
})"""

# textele de nivel de stoc, în limba capturii
THRESHOLD_TEXTS = {
    "ro_RO": ("Stoc redus", "Stoc limitat", "În stoc"),
    "en_US": ("Low stock", "Limited stock", "In stock"),
}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestStockResellerScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_stock_reseller"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        company = cls.env.company
        # meniul Raportare din Vânzări este vizibil doar administratorilor de vânzări
        cls.env.ref("base.user_admin").group_ids = [Command.link(cls.env.ref("sales_team.group_sale_manager").id)]
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id

        # doar produsele demo au stoc în locație, ca lista să fie scurtă și lizibilă
        cls.env["stock.quant"].search([("location_id", "child_of", cls.location.id)]).sudo().unlink()

        # numele categoriei nu e traductibil: îl scriem în limba capturii, în ``_capture``
        laptops = cls.env["product.category"].create({"name": "Laptopuri"})
        accessories = cls.env["product.category"].create({"name": "Accesorii"})
        cls.category_names = {
            laptops: {"ro_RO": "Laptopuri", "en_US": "Laptops"},
            accessories: {"ro_RO": "Accesorii", "en_US": "Accessories"},
        }
        products = [
            ('Laptop 15,6" i5 16 GB', 'Laptop 15.6" i5 16 GB', "LPT-156", laptops, 3899.0, 3),
            ('Laptop 14" i7 32 GB', 'Laptop 14" i7 32 GB', "LPT-140", laptops, 5499.0, 14),
            ("Mouse wireless", "Wireless mouse", "ACC-MOU", accessories, 79.0, 120),
            ('Geantă laptop 15,6"', 'Laptop bag 15.6"', "ACC-GNT", accessories, 149.0, 18),
            ("Stație de andocare USB-C", "USB-C docking station", "ACC-DOC", accessories, 699.0, 4),
        ]
        for name_ro, name_en, code, categ, price, qty in products:
            product = cls.env["product.product"].create(
                {
                    "name": name_ro,
                    "default_code": code,
                    "is_storable": True,
                    "categ_id": categ.id,
                    "list_price": price,
                }
            )
            product.product_tmpl_id.update_field_translations("name", {"ro_RO": name_ro, "en_US": name_en})
            cls.env["stock.quant"].with_context(inventory_mode=True).create(
                {"product_id": product.id, "location_id": cls.location.id, "inventory_quantity": qty}
            ).action_apply_inventory()

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Revânzători -15%",
                "currency_id": company.currency_id.id,
                "item_ids": [
                    Command.create({"compute_price": "formula", "base": "list_price", "price_discount": 15.0}),
                ],
            }
        )
        cls.pricelist.update_field_translations("name", {"ro_RO": "Revânzători -15%", "en_US": "Resellers -15%"})
        cls.partner = cls.env["res.partner"].create(
            {"name": "Distribuitor IT Demo SRL", "property_product_pricelist": cls.pricelist.id}
        )

        # o ofertă reală a adminului, ca lista Oferte din spatele meniului să nu arate date de exemplu
        cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "user_id": cls.env.ref("base.user_admin").id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.env["product.product"]
                            .search([("default_code", "=", "ACC-MOU")], limit=1)
                            .id,
                            "product_uom_qty": 10,
                        }
                    )
                ],
            }
        )
        cls.wizard_action = cls.env.ref("deltatech_stock_reseller.action_stock_quant_report")
        cls.result_action = cls.env.ref("deltatech_stock_reseller.action_stock_quant_report_value")
        cls.sales_menu = cls.env.ref("sale.sale_menu_root")

    def _shots_wizard(self):
        return [
            # 1. meniul Vânzări → Raportare → Locație stoc
            {
                "path": "/odoo/sales",
                "name": "01_meniu_locatie_stoc.png",
                "wait": ".o_menu_sections .dropdown-toggle",
                "timeout": 40000,
                "eval": OPEN_MENU_JS % "",
                "eval_wait": 1000,
                "highlight": ["[data-menu-xmlid='deltatech_stock_reseller.menu_stock_quant_report']"],
            },
            # 2. fereastra cu locația, partenerul, lista de prețuri și pragurile
            {
                "path": "/odoo/sales",
                "name": "02_fereastra_raport_stoc.png",
                "wait": ".o_menu_sections .dropdown-toggle",
                "timeout": 40000,
                "eval": OPEN_MENU_JS % CLICK_ITEM_JS,
                "eval_wait": 2000,
                "highlight": [
                    ".modal-content div[name='location_id']",
                    ".modal-content div[name='partner_id']",
                    ".modal-content div[name='pricelist_id']",
                    ".modal-content div[name='show_thresholds']",
                    ".modal-content div[name='refresh_report']",
                    ".modal-footer button[name='do_execute']",
                ],
            },
        ]

    def _shots_report(self):
        report_url = f"action={self.result_action.id}&menu_id={self.sales_menu.id}&view_type=list"
        return [
            # 3. lista rezultată: cantitate, text de stoc, preț revânzător și preț de listă
            {
                "url": report_url,
                "name": "03_raport_stoc_revanzator.png",
                "wait": ".o_list_view .o_data_row",
                # pe celulele primului rând: bulinele de pe antetul listei ar fi tăiate de marginea lui
                "eval": UNCLIP_CELLS_JS,
                "highlight": [
                    ".o_data_row:first-child td[name='qty']",
                    ".o_data_row:first-child td[name='qty_text']",
                    ".o_data_row:first-child td[name='price_reseller']",
                    ".o_data_row:first-child td[name='list_price']",
                ],
            },
        ]

    def _shots_grouped(self):
        report_url = f"action={self.result_action.id}&menu_id={self.sales_menu.id}&view_type=list"
        return [
            # 4. aceeași listă, grupată pe Categorie produs (filtrul din căutare)
            {
                "url": report_url,
                "name": "04_raport_grupat_categorie.png",
                "wait": ".o_list_view .o_group_header",
                # primul grup desfășurat, ca să se vadă produsele lui
                "eval": EXPAND_GROUP_JS,
                "eval_wait": 1500,
                "highlight": [".o_searchview_facet"],
            },
        ]

    def _set_wizard_values(self, lang):
        """Valorile din fereastră, ca după completarea lor de către operator."""
        texts = THRESHOLD_TEXTS[lang]
        self.wizard_action.context = str(
            {
                "default_location_id": self.location.id,
                "default_partner_id": self.partner.id,
                "default_pricelist_id": self.pricelist.id,
                "default_show_thresholds": True,
                "default_stock_threshold_1": 5,
                "default_stock_threshold_1_text": texts[0],
                "default_stock_threshold_2": 20,
                "default_stock_threshold_2_text": texts[1],
                "default_stock_no_threshold_text": texts[2],
            }
        )
        self.env.flush_all()

    def _capture(self, lang="ro_RO"):
        options = {"viewport": (1600, 900), "hide_systray": True, "lang": lang}
        self._set_wizard_values(lang)
        for categ, names in self.category_names.items():
            categ.name = names[lang]
        self.capture_screenshots(self._shots_wizard(), **options)
        # raportul generat cu valorile din fereastră (butonul Aplică)
        wizard = self.env["stock.quant.report"].with_context(**ast.literal_eval(self.wizard_action.context)).create({})
        wizard.do_execute()
        self.assertEqual(len(wizard.lines_ids), 5)
        self.env.flush_all()
        self.capture_screenshots(self._shots_report(), **options)
        self.result_action.context = "{'search_default_category': 1}"
        self.env.flush_all()
        try:
            self.capture_screenshots(self._shots_grouped(), **options)
        finally:
            self.result_action.context = "{}"

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
