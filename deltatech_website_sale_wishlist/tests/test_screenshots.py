# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Listele de favorite ale clienților, cu stoc și reaprovizionare":
# lista de favorite, formularul unui produs favorit, butonul Reaprovizionare pe liniile selectate
# și cererea de ofertă rezultată. Aceleași shot-uri în RO pentru fișă și în EN pentru
# readme/USAGE.md.
#
# Seed: trei clienți, trei produse cu stoc diferit și cinci produse favorite; pentru ultima
# captură, cu `purchase_stock` instalat, reaprovizionarea a două linii (ruta Cumpără + furnizor).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_sale_wishlist,deltatech_doc_screenshots,purchase_stock \
#       --test-tags=/deltatech_website_sale_wishlist:TestWishlistScreenshots --stop-after-init
import unittest
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

VIEWPORT = (1440, 900)
REPLENISH_BTN = "button[name='action_launch_replenishment']"
# coloana de stoc lată cât eticheta ei, iar celulele nu mai taie ecusonul evidențierii
LIST_JS = """() => {
    const th = document.querySelector("th[data-name='qty_available']");
    if (th) { th.style.width = '200px'; th.style.minWidth = '200px'; }
    const partner = document.querySelector("th[data-name='partner_id']");
    if (partner) { partner.style.width = '260px'; }
    document.querySelectorAll('.o_list_renderer, .o_list_table, .o_list_table td, .o_list_table th')
        .forEach((el) => { el.style.overflow = 'visible'; });
}"""

# denumire, preț, stoc
PRODUCTS = [
    ("Scaun de birou ergonomic", 899.0, 12),
    ("Lampă de birou LED", 149.0, 0),
    ("Birou reglabil electric", 1890.0, 2),
]
# client -> produsele favorite (indice în PRODUCTS)
WISHES = [
    ("Ana Popescu", [0, 1]),
    ("Mihai Ionescu", [1, 2]),
    ("Elena Dumitrescu", [1]),
]


@tagged("-at_install", "post_install", "fise_screenshots")
class TestWishlistScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_sale_wishlist"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company()
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})

        website = env["website"].search([("company_id", "=", company.id)], limit=1)
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        warehouse.name = company.name
        cls.has_purchase = "purchase.order" in env and env.ref(
            "purchase_stock.route_warehouse0_buy", raise_if_not_found=False
        )
        vendor = env["res.partner"].create({"name": "Furnizor Mobilier SRL", "is_company": True})
        # TVA 21% la achiziție: baza de test nu are planul de conturi RO
        tax_group = env["account.tax.group"].create({"name": "TVA 21%", "company_id": company.id})
        purchase_tax = env["account.tax"].create(
            {
                "name": "TVA 21%",
                "amount": 21.0,
                "type_tax_use": "purchase",
                "company_id": company.id,
                "tax_group_id": tax_group.id,
            }
        )

        # liste de favorite doar cu datele seed-ului
        env["product.wishlist"].with_context(active_test=False).search([]).unlink()
        products = env["product.product"]
        for name, price, qty in PRODUCTS:
            # fără taxe implicite: baza de test nu are planul de conturi RO, iar cota generică ar induce în eroare
            vals = {
                "name": name,
                "list_price": price,
                "is_storable": True,
                "is_published": True,
                "taxes_id": [Command.clear()],
            }
            if cls.has_purchase:
                vals.update(
                    {
                        "route_ids": [Command.link(cls.has_purchase.id)],
                        "supplier_taxes_id": [Command.set(purchase_tax.ids)],
                        "seller_ids": [Command.create({"partner_id": vendor.id, "price": round(price * 0.6, 2)})],
                    }
                )
            product = env["product.product"].create(vals)
            if qty:
                env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, qty)
            products |= product

        Wishlist = env["product.wishlist"]
        cls.items = Wishlist
        for partner_name, indexes in WISHES:
            partner = env["res.partner"].create({"name": partner_name})
            for i in indexes:
                cls.items |= Wishlist.create(
                    {
                        "partner_id": partner.id,
                        "product_id": products[i].id,
                        "price": PRODUCTS[i][1],
                        "website_id": website.id,
                    }
                )

        cls.action = env.ref("deltatech_website_sale_wishlist.product_wishlist_action")
        cls.menu = env.ref("deltatech_website_sale_wishlist.menu_product_wishlist")
        cls.purchase = env["purchase.order"] if cls.has_purchase else None
        if cls.has_purchase:
            # liniile 2 și 4 din listă, bifate și în captura 03: Lampă de birou LED (Ana Popescu, stoc 0)
            # și Birou reglabil electric (Mihai Ionescu, stoc 2)
            lamp = cls.items.filtered(lambda w: w.product_id == products[1])[:1]
            desk = cls.items.filtered(lambda w: w.product_id == products[2])[:1]
            (lamp | desk).with_user(admin).with_company(company).action_launch_replenishment()
            env.flush_all()
            # câte o cerere de ofertă pentru fiecare linie reaprovizionată
            cls.purchases = env["purchase.order"].search([("partner_id", "=", vendor.id)])
            # termenul cererii azi, nu în trecut (altfel lista o arată „CdO întârziat"), iar sosirea după el
            now = fields.Datetime.now()
            cls.purchases.write({"date_order": now + timedelta(hours=2)})
            cls.purchases.order_line.write({"date_planned": now + timedelta(days=3)})
            cls.purchase = cls.purchases.filtered(lambda po: po.order_line.product_id == products[1])[:1]
        env.flush_all()

    def _list_url(self):
        return f"action={self.action.id}&menu_id={self.menu.id}&model=product.wishlist&view_type=list"

    def _shots(self):
        shots = [
            # Pasul 1 — lista produselor favorite, cu stocul fiecărui produs
            {
                "url": self._list_url(),
                "name": "01_lista_favorite.png",
                "wait": ".o_list_view .o_data_row",
                "eval": f"({LIST_JS})()",
                "highlight": [".o_main_navbar .o_menu_sections > :nth-child(2)", "td[name='qty_available']"],
                "settle": 1500,
            },
            # Pasul 2 — formularul unui produs favorit
            {
                "url": (
                    f"action={self.action.id}&menu_id={self.menu.id}"
                    f"&id={self.items[1].id}&model=product.wishlist&view_type=form"
                ),
                "name": "02_formular_favorit.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='qty_available']"],
                "settle": 1500,
            },
            # Pasul 3 — liniile selectate și butonul Reaprovizionare
            {
                "url": self._list_url(),
                "name": "03_reaprovizionare_selectie.png",
                "wait": ".o_list_view .o_data_row",
                "click_btn": ".o_data_row:nth-child(2) .o_list_record_selector input",
                "wait_after": REPLENISH_BTN,
                "eval": (
                    "document.querySelector('.o_data_row:nth-child(4) .o_list_record_selector input').click();"
                    f"setTimeout({LIST_JS}, 300)"
                ),
                "highlight": [".o_data_row_selected td[name='product_id']", REPLENISH_BTN],
                "settle": 1500,
            },
        ]
        if self.purchase:
            rfq_action = self.env.ref("purchase.purchase_rfq").id
            shots += [
                # Pasul 4 — cererile de ofertă create de reaprovizionare, câte una pe linie
                {
                    "url": f"action={rfq_action}&model=purchase.order&view_type=list",
                    "name": "04_cereri_oferta.png",
                    "wait": ".o_list_view .o_data_row",
                    "eval": f"({LIST_JS})()",
                    "highlight": ["td[name='name']"],
                    "settle": 1500,
                },
                # Pasul 5 — o cerere de ofertă: produsul favorit, cantitatea 1
                {
                    "url": f"action={rfq_action}&id={self.purchase.id}&model=purchase.order&view_type=form",
                    "name": "05_cerere_oferta.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='partner_id']", "div[name='order_line'] td[name='product_qty']"],
                    "settle": 1500,
                },
            ]
        return shots

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=VIEWPORT)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=VIEWPORT, lang="en_US")
