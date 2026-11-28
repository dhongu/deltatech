# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Screenshots for the consultant sheet (RO) and readme/USAGE.md (EN): the Managers included
# option under Price Control, the register where the Price key stays disabled for a manager,
# and the product form where a wrong price is corrected.
#
# Run:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_pos_price_lock,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import io
import unittest

from odoo import Command
from odoo.tests import tagged
from odoo.tools import BinaryBytes

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None

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
"""

# Open the register and put one product on the order, so the numpad is active.
OPEN_WITH_LINE = """
    const openBtn = document.querySelector('.open-register-btn');
    if (openBtn) { openBtn.click(); }
    await wait('.product-screen article.product', 40000);
    await sleep(800);
    document.querySelector('.product-screen article.product').click();
    await wait('.order-container .orderline');
    await sleep(800);
"""


def _picture(colour):
    from PIL import Image  # noqa: PLC0415

    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), colour).save(buffer, format="PNG")
    return BinaryBytes(buffer.getvalue())


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPosPriceLockScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_pos_price_lock"

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
        admin.group_ids = [Command.link(pos_manager.id)]
        env.user.sudo().group_ids = [Command.link(pos_manager.id)]

        tax = cls.company_data["default_tax_sale"]
        cls.product = env["product.product"].create(
            {
                "name": "Cafea boabe 1 kg",
                "list_price": 74.30,
                "type": "consu",
                "available_in_pos": True,
                "company_id": company.id,
                "taxes_id": [Command.set(tax.ids)],
                "image_1920": _picture((111, 78, 55)),
            }
        )
        cash_journal = env["account.journal"].search(
            [*env["account.journal"]._check_company_domain(company), ("type", "=", "cash")], limit=1
        )
        cash = env["pos.payment.method"].create({"name": "Cash", "journal_id": cash_journal.id})
        cls.config = env["pos.config"].create(
            {
                "name": "Magazin Centru",
                "payment_method_ids": [Command.set(cash.ids)],
                "restrict_price_control": True,
                "lock_price_for_managers": True,
            }
        )
        cls.config.open_ui()
        cls.config.current_session_id.set_opening_control(0, "")

    def _pos(self, name, highlight):
        return {
            "path": f"/pos/ui/{self.config.id}",
            "name": name,
            "wait": ".open-register-btn, .product-screen",
            "timeout": 60000,
            "eval": "async () => {" + JS_HELPERS + OPEN_WITH_LINE + "}",
            "eval_wait": 500,
            "settle": 800,
            "highlight": highlight,
        }

    def _shots(self):
        settings = self.env.ref("point_of_sale.action_pos_configuration").id
        products = self.env.ref("point_of_sale.product_template_action_pos_product").id
        pos_menu = self.env.ref("point_of_sale.menu_point_root").id
        template = self.product.product_tmpl_id
        return [
            {
                "url": f"action={settings}&menu_id={pos_menu}&model=res.config.settings&view_type=form",
                "name": "01_setari_blocare_pret.png",
                "wait": ".o_form_view div[name='pos_lock_price_for_managers']",
                "timeout": 60000,
                "eval": "document.querySelector(\"div[name='pos_lock_price_for_managers']\")"
                ".scrollIntoView({block: 'center'})",
                "highlight": [
                    "div[name='pos_restrict_price_control']",
                    "div[name='pos_lock_price_for_managers']",
                ],
                "settle": 2500,
            },
            self._pos("02_pos_tasta_pret_blocata.png", [".numpad-price", ".order-container .orderline .price"]),
            {
                "url": f"action={products}&menu_id={pos_menu}&id={template.id}&model=product.template&view_type=form",
                "name": "03_corectie_pret_produs.png",
                "wait": ".o_form_view div[name='list_price']",
                "highlight": ["div[name='list_price']"],
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1280, 720), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1280, 720), hide_systray=True, lang="en_US")

    def _gif_steps(self):
        return [
            {
                "path": f"/pos/ui/{self.config.id}",
                "wait": ".open-register-btn, .product-screen",
                "timeout": 60000,
            },
            {"click": ".open-register-btn", "wait_after": ".product-screen article.product"},
            {
                "caption": "The manager adds a product to the order",
                "click": ".product-screen article.product",
                "wait_after": ".order-container .orderline",
                "hold": 1200,
            },
            {
                "caption": "Quantity and discount stay at hand",
                "move": ".numpad button:has-text('%')",
                "hold": 1500,
            },
            {
                "caption": "The Price key is locked, for managers too",
                "move": ".numpad-price",
                "hold": 2500,
            },
            {
                "caption": "Prices are corrected on the product instead",
                "move": ".order-container .orderline .price",
                "hold": 2500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # deltatech has only the EN page on the Apps Store: static/description/en/demo.gif
        self.capture_gif(self._gif_steps(), lang="en_US")
