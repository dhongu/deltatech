# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Protecția prețului de cost în magazinul online" — generate în
# timpul testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: setările magazinului (vânzarea blocată sub cost + marja minimă), produsul cu prețul de
# vânzare și costul, apoi magazinul: produsul sub prag fără „Adaugă în coș", produsul peste prag
# vândut normal.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_website_sale_cost_price,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_sale_cost_price:TestCostPriceScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Setările: aduce în ecran secțiunea cu „Evită vânzarea produsului cu preț zero"
SCROLL_SETTING_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const el = document.querySelector("#hide_add_to_cart_setting");
    el.scrollIntoView({block: "start"});
    const scroller = el.closest(".o_content, .settings");
    if (scroller) { scroller.scrollTop -= 120; }
    await sleep(800);
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestCostPriceScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_sale_cost_price"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company()
        # 20.0: ``website.get_current_website()`` nu mai există; prepare_ro_company aliniază
        # site-urile la compania capturilor
        cls.website = cls.env["website"].search([("company_id", "=", company.id)], limit=1)
        lang_ro = cls.env.ref("base.lang_ro")
        lang_en = cls.env.ref("base.lang_en")
        # magazinul în română, cu engleza ca a doua limbă (capturile EN pentru USAGE.md);
        # vânzarea sub cost blocată, cu o marjă minimă de 10% peste cost
        cls.website.write(
            {
                "name": "Magazin Demo Electro",
                "language_ids": [Command.set((lang_ro | lang_en).ids)],
                "default_lang_id": lang_ro.id,
                # prețurile din magazin afișate fără TVA (implicit), ca prețul și costul să se compare
                # la fel pe pagina produsului, în listă și la adăugarea în coș
                "show_line_subtotals_tax_selection": "tax_excluded",
                # butonul de coș vizibil pe fiecare produs din listă, nu doar la trecerea mouse-ului;
                # fără butonul de favorite, care fără hover își arată eticheta trunchiată
                "shop_opt_products_design_classes": cls.env["website"]
                ._fields["shop_opt_products_design_classes"]
                .default(cls.website)
                .replace("o_wsale_products_opt_actions_onhover", "")
                .replace("o_wsale_products_opt_has_wishlist", "")
                .replace("o_wsale_products_opt_wishlist_fixed", ""),
                "prevent_sale": True,
                "prevent_sale_for": "zero_price",
                "cost_price_include_tax": False,
                "cost_price_margin_percentage": 10.0,
            }
        )
        cls.tax = cls.env["account.tax"].create(
            {"name": "TVA 21%", "amount": 21.0, "amount_type": "percent", "type_tax_use": "sale"}
        )
        cls.category = cls.env["product.public.category"].create({"name": "Cabluri"})
        cls.category.update_field_translations("name", {"ro_RO": "Cabluri", "en_US": "Cables"})
        # 42 < 40 × 1,10 = 44 → vânzarea blocată
        cls.product_blocked = cls._create_product("Cablu HDMI 2 m", "HDMI cable 2 m", "CBL-HDMI2", 42.0, 40.0)
        # 79 > 60 × 1,10 = 66 → se vinde normal
        cls.product_allowed = cls._create_product("Cablu HDMI 5 m", "HDMI cable 5 m", "CBL-HDMI5", 79.0, 60.0)

    @classmethod
    def _create_product(cls, name_ro, name_en, code, price, cost):
        product = cls.env["product.template"].create(
            {
                "name": name_ro,
                "default_code": code,
                "type": "consu",
                "list_price": price,
                "standard_price": cost,
                "sale_ok": True,
                "is_published": True,
                "website_id": cls.website.id,
                "public_categ_ids": [Command.set(cls.category.ids)],
                "taxes_id": [Command.set(cls.tax.ids)],
            }
        )
        product.update_field_translations("name", {"ro_RO": name_ro, "en_US": name_en})
        return product

    def _shots(self):
        product_form = f"id={self.product_blocked.id}&model=product.template&view_type=form"
        category_path = f"/shop/category/{self.env['ir.http']._slug(self.category)}"
        blocked_url = self.product_blocked.website_url
        allowed_url = self.product_allowed.website_url
        return [
            # 1. setările magazinului: vânzarea blocată sub cost, costul fără TVA, marja minimă
            {
                "url": "action=website.action_website_configuration",
                "name": "01_setari_pret_cost.png",
                "wait": "#hide_add_to_cart_setting",
                "timeout": 40000,
                "eval": SCROLL_SETTING_JS,
                "eval_wait": 1000,
                "highlight": [
                    "#hide_add_to_cart_setting div[name='prevent_sale']",
                    "#cost_price_sale_setting div[name='cost_price_include_tax']",
                    "#cost_price_sale_setting div[name='cost_price_margin_percentage']",
                ],
            },
            # 2. produsul: prețul de vânzare sub costul plus marja
            {
                "url": product_form,
                "name": "02_produs_pret_cost.png",
                "wait": ".o_form_view",
                "hide_fields": ["supplier_taxes_id"],
                "highlight": ["div[name='list_price']", "div[name='standard_price']"],
            },
            # 3. lista din magazin: produsul sub prag nu are coș, celălalt da
            {
                "path": {"ro_RO": category_path, "en_US": f"/en{category_path}"},
                "name": "03_magazin_lista_produse.png",
                "wait": "#products_grid",
                "settle": 2500,
                "highlight": {
                    "ro_RO": [
                        ".oe_product:has-text('Cablu HDMI 2 m')",
                        ".oe_product:has-text('Cablu HDMI 5 m')",
                    ],
                    "en_US": [
                        ".oe_product:has-text('HDMI cable 2 m')",
                        ".oe_product:has-text('HDMI cable 5 m')",
                    ],
                },
            },
            # 4. pagina produsului sub prag: fără preț și fără „Adaugă în coș", doar „Contactați-ne"
            {
                "path": {"ro_RO": blocked_url, "en_US": f"/en{blocked_url}"},
                "name": "04_produs_blocat_magazin.png",
                "wait": "#product_detail",
                "settle": 2500,
                "highlight": ["#contact_us_wrapper a"],
            },
            # 5. pagina produsului peste prag: prețul și „Adaugă în coș"
            {
                "path": {"ro_RO": allowed_url, "en_US": f"/en{allowed_url}"},
                "name": "05_produs_permis_magazin.png",
                "wait": "#product_detail",
                "settle": 2500,
                # spațiu în stânga prețului, ca bulina ① să nu acopere prima cifră
                "eval": "document.querySelector('#product_details .product_price').style.paddingLeft = '14px'",
                "highlight": ["#product_details .product_price", "#add_to_cart_wrap button[name='add_to_cart']"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1100), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1100), hide_systray=True, lang="en_US")
