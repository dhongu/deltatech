# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Ultimul preț de achiziție și adaosul comercial” — generate în
# timpul testelor, pe compania „Demo Magazin SRL” în RON: RO pentru fișă (static/description/),
# EN pentru readme/USAGE.md (static/description/en/).
#
# Scenariul din fișă: „Vopsea lavabilă albă 15 l” are ultimul preț de achiziție 100,00 lei și
# adaosul 30% (preț de vânzare 130,00 lei); recepția unei comenzi la 110,00 lei duce prețul de
# vânzare la 143,00 lei. „Pensulă 50 mm” are prețul de vânzare 13,00 lei; fără actualizarea
# automată, corectarea prețului de achiziție la 12,50 lei recalculează doar adaosul (4%).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_purchase_price,sale,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_purchase_price:TestPurchasePriceScreenshots --stop-after-init
import unittest

from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

OPEN_MARKUP_WIZARD = """
(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const waitFor = async (selector) => {
        for (let i = 0; i < 50 && !document.querySelector(selector); i++) {
            await sleep(200);
        }
        return document.querySelector(selector);
    };
    await waitFor('.o_data_row');
    await sleep(500);
    (await waitFor('thead .o_list_record_selector input')).click();
    await sleep(1000);
    // Odoo 20: the Actions button carries the "settings" icon (fa-cog before)
    (await waitFor('.o_cp_action_menus [data-icon="settings"], .o_cp_action_menus .fa-cog')).closest('button').click();
    let item;
    for (let i = 0; i < 50 && !item; i++) {
        await sleep(200);
        item = [...document.querySelectorAll('.o-dropdown-item, .dropdown-item')].find(
            (e) => e.textContent.includes('%s')
        );
    }
    item.click();
    (await waitFor('.modal div[name="selected_line"] input')).click();
    await sleep(500);
    const input = document.querySelector('.modal div[name="trade_markup"] input');
    input.value = '30';
    input.dispatchEvent(new Event('input', {bubbles: true}));
    input.dispatchEvent(new Event('change', {bubbles: true}));
    input.blur();
    await sleep(800);
})()
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPurchasePriceScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_purchase_price"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, company.id)], "company_id": company.id})
        for xmlid in ("purchase.group_purchase_manager", "stock.group_stock_manager", "sales_team.group_sale_manager"):
            group = env.ref(xmlid)
            env.user.group_ids = [(4, group.id)]
            admin.group_ids = [(4, group.id)]
        env.flush_all()
        env.user.name = "Ioana Marin"

        set_str = env["ir.config_parameter"].sudo().set_str
        set_str("purchase.update_product_price", "True")
        set_str("purchase.update_list_price", "True")
        set_str("purchase.add_supplier_to_product", "True")

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        warehouse.write({"name": "Magazin Centru", "code": "MAG"})
        warehouse.in_type_id.name = "Recepții"
        cls.vendor = env["res.partner"].create({"name": "Distribuitor Vopsele SRL"})
        tax_sale = cls.company_data["default_tax_sale"]
        tax_purchase = cls.company_data["default_tax_purchase"]

        def product(name, code, last_price, markup, price):
            tmpl = env["product.template"].create(
                {
                    "name": name,
                    "default_code": code,
                    "type": "consu",
                    "is_storable": True,
                    "list_price": price,
                    "standard_price": last_price,
                    "taxes_id": [(6, 0, tax_sale.ids)],
                    "supplier_taxes_id": [(6, 0, tax_purchase.ids)],
                    "company_id": company.id,
                    "seller_ids": [(0, 0, {"partner_id": cls.vendor.id, "price": last_price})],
                }
            )
            tmpl.write({"last_purchase_price": last_price, "trade_markup": markup})
            tmpl.list_price = price
            return tmpl

        # lista de produse din captura wizardului arată doar produsele scenariului
        env["product.template"].search([("company_id", "!=", company.id)]).active = False
        cls.vopsea = product("Vopsea lavabilă albă 15 l", "VOP-015", 100.0, 30.0, 130.0)
        cls.pensula = product("Pensulă 50 mm", "PEN-050", 10.0, 30.0, 13.0)
        cls.act_product = env.ref("sale.product_template_action").id

    def _product_shot(self, product, name, **extra):
        shot = {
            "url": f"action={self.act_product}&id={product.id}&model=product.template&view_type=form",
            "name": name,
            "wait": ".o_form_view",
        }
        shot.update(extra)
        return shot

    def _receive(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (0, 0, {"product_id": self.vopsea.product_variant_id.id, "product_qty": 20, "price_unit": 110.0})
                ],
            }
        )
        order.button_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 20
        picking.move_ids.picked = True
        picking.button_validate()
        return picking

    def _correct_pensula(self):
        self.env["ir.config_parameter"].sudo().set_str("purchase.update_list_price", "False")
        form = Form(self.pensula)
        form.last_purchase_price = 12.5
        form.save()

    def _run(self, lang="ro_RO"):
        wizard_label = {"ro_RO": "Aplică adaosul comercial", "en_US": "Set Trade Markup"}[lang]
        markup_fields = ["div[name='last_purchase_price']", "div[name='trade_markup']", "div[name='list_price']"]
        self.capture_screenshots(
            [
                {
                    "path": "/odoo/settings#purchase",
                    "name": "01_setari_achizitii.png",
                    "wait": "#purchase_update_list_price",
                    "timeout": 60000,
                    "eval": "document.querySelector('#purchase_update_product_price').scrollIntoView({block: 'start'})",
                    "highlight": ["#purchase_update_product_price", "#purchase_update_list_price"],
                },
                self._product_shot(self.vopsea, "02_produs_adaos.png", highlight=markup_fields),
                {
                    "url": f"action={self.act_product}&view_type=list",
                    "name": "03_wizard_adaos.png",
                    "wait": ".o_list_view",
                    "eval": OPEN_MARKUP_WIZARD % wizard_label,
                    "eval_wait": 1500,
                    "highlight": [
                        ".modal div[name='selected_line']",
                        ".modal div[name='trade_markup']",
                        ".modal button[name='do_set_trade_markup']",
                    ],
                },
            ],
            hide_systray=True,
            lang=lang,
        )
        picking = self._receive()
        self._correct_pensula()
        self.capture_screenshots(
            [
                {
                    "url": f"action=stock.action_picking_tree_all&id={picking.id}&model=stock.picking&view_type=form",
                    "name": "04_receptie_validata.png",
                    "wait": ".o_form_view",
                },
                self._product_shot(self.vopsea, "05_produs_dupa_receptie.png", highlight=markup_fields),
                self._product_shot(self.pensula, "06_adaos_recalculat.png", highlight=markup_fields),
            ],
            hide_systray=True,
            lang=lang,
        )

    def test_capture_fise(self):
        self._run()

    def test_capture_usage(self):
        self._run(lang="en_US")
