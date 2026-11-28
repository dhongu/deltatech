# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Screenshots for the consultant sheet (RO) and readme/USAGE.md (EN): the POS setting, the badge
# with price and stock on the product cards, the warning when a product without stock is added,
# and the register that shows the available quantity (stock minus reservations).
#
# Run:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_pos_stock,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import base64
import io
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None

# Helpers run in the page: wait for an element, click it, find an element by its text.
JS_HELPERS = """
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const wait = async (sel, timeout = 20000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(sel);
            if (el) { return el; }
            await sleep(100);
        }
        throw new Error('Not found: ' + sel);
    };
    const byText = async (sel, text, timeout = 20000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = [...document.querySelectorAll(sel)].find((e) => text.test(e.textContent));
            if (el) { return el; }
            await sleep(100);
        }
        throw new Error('Not found: ' + sel + ' ' + text);
    };
    const clickText = async (sel, text) => { (await byText(sel, text)).click(); await sleep(600); };
"""

OPEN_REGISTER = """
    const openBtn = document.querySelector('.open-register-btn');
    if (openBtn) { openBtn.click(); }
    await wait('.product-screen .product-stock-tag', 40000);
    await sleep(1000);
"""

ADD_OUT_OF_STOCK = """
    await clickText('.product-screen article.product', /Zahăr/);
    await wait('.o_notification');
    await sleep(800);
"""

# name, price without VAT (89,90 lei with VAT for the coffee), quantity on hand, colour of the product picture
PRODUCTS = [
    ("Cafea boabe 1 kg", 74.30, 25, (111, 78, 55)),
    ("Ceai verde 100 g", 15.29, 8, (76, 140, 74)),
    ("Ciocolată neagră 100 g", 10.66, 3, (70, 45, 35)),
    ("Zahăr 1 kg", 5.29, 0, (96, 92, 84)),
]


def _picture(colour):
    from PIL import Image  # noqa: PLC0415

    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), colour).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue())


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPosStockScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_pos_stock"

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
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id, "name": "Ana Popescu"})
        pos_manager = env.ref("point_of_sale.group_pos_manager")
        stock_manager = env.ref("stock.group_stock_manager")
        admin.group_ids = [Command.link(pos_manager.id), Command.link(stock_manager.id)]
        env.user.sudo().group_ids = [Command.link(pos_manager.id), Command.link(stock_manager.id)]

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        stock_location = warehouse.lot_stock_id
        tax = cls.company_data["default_tax_sale"]
        cls.products = env["product.product"]
        for name, price, qty, colour in PRODUCTS:
            product = env["product.product"].create(
                {
                    "name": name,
                    "list_price": price,
                    "type": "consu",
                    "is_storable": True,
                    "available_in_pos": True,
                    "company_id": company.id,
                    "taxes_id": [Command.set(tax.ids)],
                    "image_1920": _picture(colour),
                }
            )
            if qty:
                env["stock.quant"]._update_available_quantity(product, stock_location, qty)
            cls.products |= product
        cls.bag = env["product.product"].create(
            {
                "name": "Pungă hârtie",
                "list_price": 0.41,
                "type": "consu",
                "available_in_pos": True,
                "company_id": company.id,
                "taxes_id": [Command.set(tax.ids)],
                "image_1920": _picture((214, 190, 150)),
            }
        )

        # 5 kg of coffee reserved for a delivery that has not left the warehouse yet
        coffee = cls.products[0]
        customer = env["res.partner"].create({"name": "Bistro Central SRL"})
        delivery = env["stock.picking"].create(
            {
                "picking_type_id": warehouse.out_type_id.id,
                "partner_id": customer.id,
                "location_id": stock_location.id,
                "location_dest_id": env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": coffee.id,
                            "product_uom_qty": 5,
                            "location_id": stock_location.id,
                            "location_dest_id": env.ref("stock.stock_location_customers").id,
                        }
                    )
                ],
            }
        )
        delivery.action_confirm()
        delivery.action_assign()

        # a card method: a cash method cannot be shared by the two registers
        card = env["pos.payment.method"].create(
            {"name": "Card", "journal_id": cls.company_data["default_journal_bank"].id}
        )
        common = {
            "payment_method_ids": [Command.set(card.ids)],
            "iface_tax_included": "total",
            "warehouse_id": warehouse.id,
            "display_stock": True,
            "display_price": True,
        }
        cls.config_available = env["pos.config"].create(
            {"name": "Showroom", "stock_badge_quantity": "available", **common}
        )
        # created last, so the settings page opens on it
        cls.config = env["pos.config"].create({"name": "Magazin Centru", "stock_badge_quantity": "on_hand", **common})
        for config in cls.config | cls.config_available:
            config.open_ui()
            config.current_session_id.set_opening_control(0, "")

    def _pos(self, config, name, body="", highlight=None):
        shot = {
            "path": f"/pos/ui/{config.id}",
            "name": name,
            "wait": ".open-register-btn, .product-screen",
            "timeout": 60000,
            "eval": "async () => {" + JS_HELPERS + OPEN_REGISTER + body + "}",
            "eval_wait": 500,
            "settle": 800,
        }
        if highlight:
            shot["highlight"] = highlight
        return shot

    def _card(self, product, part):
        return f"article[data-product-id='{product.product_tmpl_id.id}'] {part}"

    def _shots(self):
        settings = self.env.ref("point_of_sale.action_pos_configuration").id
        pos_menu = self.env.ref("point_of_sale.menu_point_root").id
        return [
            {
                "url": f"action={settings}&menu_id={pos_menu}&model=res.config.settings&view_type=form",
                "name": "01_setari_stoc.png",
                "wait": ".o_form_view div[name='pos_display_stock']",
                "timeout": 60000,
                "eval": "document.querySelector(\"div[name='pos_display_stock']\").scrollIntoView({block: 'center'})",
                "highlight": [
                    "div:has(> div[name='pos_display_stock'])",
                    "div:has(> div[name='pos_display_price'])",
                    "div:has(> div[name='pos_stock_badge_quantity'])",
                ],
                "settle": 2500,
            },
            self._pos(
                self.config,
                "02_pos_badge_stoc_pret.png",
                highlight=[self._card(self.products[0], ".product-stock-tag")],
            ),
            self._pos(
                self.config,
                "03_pos_avertizare_fara_stoc.png",
                ADD_OUT_OF_STOCK,
                highlight=[".o_notification"],
            ),
            self._pos(
                self.config_available,
                "04_pos_cantitate_disponibila.png",
                highlight=[self._card(self.products[0], ".product-qty")],
            ),
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1280, 720), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1280, 720), hide_systray=True, lang="en_US")

    def _gif_steps(self):
        coffee, _tea, _chocolate, sugar = self.products
        return [
            {
                "path": f"/pos/ui/{self.config.id}",
                "wait": ".open-register-btn, .product-screen",
                "timeout": 60000,
            },
            {"click": ".open-register-btn", "wait_after": ".product-screen .product-stock-tag"},
            {
                "caption": "Every product card shows its price and stock",
                "move": self._card(coffee, ".product-name"),
                "hold": 2200,
            },
            {
                "caption": "Products with nothing left are shown in red",
                "move": self._card(sugar, ".product-name"),
                "hold": 2000,
            },
            {
                "caption": "Selling one still works, with a warning",
                "click": f"article[data-product-id='{sugar.product_tmpl_id.id}']",
                "wait_after": ".o_notification",
                "hold": 2500,
            },
            {
                "caption": "The badge follows every stock move, live",
                "move": self._card(coffee, ".product-name"),
                "hold": 2200,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # deltatech has only the EN page on the Apps Store: static/description/en/demo.gif
        self.capture_gif(self._gif_steps(), lang="en_US")
