# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Coduri alternative ale produselor" — generate în timpul
# testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: codurile alternative pe produs (tabul Alternative), câmpul combinat Cod alternativ,
# lista produselor, setările căutării, căutarea produsului după cod pe o comandă de vânzare,
# coloana Cod alternativ pe comanda de vânzare și pe transfer, acțiunea planificată de
# separare a codurilor.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_alternative,deltatech_doc_screenshots \
#       --test-tags=/deltatech_alternative:TestAlternativeScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

ALTERNATIVE_TAB = {"ro_RO": "Alternative", "en_US": "Alternative"}
ALTERNATIVE_CODE = {"ro_RO": "Cod alternativ", "en_US": "Alternative Code"}

# insignele numerotate ale evidențierilor ies din celule și din lista de alegere: nu le mai tăiem
SHOW_BADGES_JS = (
    "() => document.head.insertAdjacentHTML('beforeend', "
    "'<style>td.o_data_cell, th, .o_list_renderer, .table-responsive, .o-autocomplete--dropdown-menu"
    "{overflow:visible!important}</style>')"
)

# lista produselor filtrată după un cod alternativ (opțiunea „Alternative" din căutare)
FILTER_BY_CODE = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const input = document.querySelector('.o_searchview_input');
    input.focus();
    input.value = '366';
    input.dispatchEvent(new Event('input', {bubbles: true}));
    let item = null;
    for (let i = 0; i < 30 && !item; i++) {
        await sleep(200);
        item = [...document.querySelectorAll('.o_searchview_autocomplete .o-dropdown-item')]
            .find((li) => /Alternative/.test(li.textContent));
    }
    if (item) item.click();
    await sleep(1500);
    document.head.insertAdjacentHTML(
        'beforeend', '<style>td.o_data_cell{overflow:visible!important}</style>'
    );
}"""

# coloana „Cod alternativ" e opțională și ascunsă implicit: o afișăm din meniul coloanelor
SHOW_OPTIONAL_COLUMN = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const toggle = () => document
        .querySelector("div[name='%(field)s'] .o_optional_columns_dropdown_toggle")
        .closest('button, .dropdown-toggle, span');
    toggle().click();
    await sleep(800);
    const input = [...document.querySelectorAll('.o-dropdown--menu input[type=checkbox]')]
        .find((i) => i.closest('.dropdown-item, .o-dropdown-item, label, span').textContent.includes('%(label)s'));
    if (input && !input.checked) input.click();
    await sleep(800);
    if (document.querySelector('.o-dropdown--menu')) toggle().click();
    await sleep(800);
    document.head.insertAdjacentHTML(
        'beforeend', '<style>td.o_data_cell{overflow:visible!important}</style>'
    );
}"""

# pe o comandă nouă: „Adăugați un produs" și o parte din codul alternativ în câmpul produsului
SEARCH_BY_CODE = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const add = document.querySelector('div[name=order_line] .o_field_x2many_list_row_add a');
    add.click();
    for (let t = 0; t < 10000 && !document.querySelector("div[name=order_line] td[name=product_id] input,"
        + " div[name=order_line] td[name=product_template_id] input"); t += 200) {
        await sleep(200);
    }
    const input = document.querySelector("div[name=order_line] td[name=product_id] input,"
        + " div[name=order_line] td[name=product_template_id] input");
    input.focus();
    input.value = '366 200';
    input.dispatchEvent(new Event('input', {bubbles: true}));
    for (let t = 0; t < 10000 && !document.querySelector('.o-autocomplete--dropdown-item'); t += 200) {
        await sleep(200);
    }
    await sleep(800);
    document.head.insertAdjacentHTML(
        'beforeend', '<style>td.o_data_cell{overflow:visible!important}</style>'
    );
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestAlternativeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_alternative"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        get_param = env["ir.config_parameter"].sudo()
        get_param.set_param("alternative.search_name", "True")
        get_param.set_param("alternative.limit", "10")
        get_param.set_param("alternative.length_min", "3")

        cls.product_tmpl = env["product.template"].create(
            {
                "name": "Filtru ulei motor",
                "default_code": "FU-1001",
                "type": "consu",
                "is_storable": True,
                "list_price": 45.0,
                "used_for": "Diesel 2.0 TDI",
                "alternative_ids": [
                    Command.create({"name": "366 200 05 01", "sequence": 1}),
                    Command.create({"name": "FLT-2041", "sequence": 2}),
                    Command.create({"name": "OLD-0457", "sequence": 3, "hide": True}),
                ],
            }
        )
        cls.product_tmpl.update_field_translations("name", {"ro_RO": "Filtru ulei motor", "en_US": "Engine oil filter"})
        cls.product = cls.product_tmpl.product_variant_id

        cls.partner = env["res.partner"].create({"name": "Client Exemplu SRL", "is_company": True, "lang": "ro_RO"})
        # comanda cu produsul, pentru coloana „Cod alternativ" de pe linii
        cls.order = env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [Command.create({"product_id": cls.product.id, "product_uom_qty": 4})],
            }
        )
        # comanda nouă, goală, pe care se caută produsul după codul alternativ
        cls.order_new = env["sale.order"].create({"partner_id": cls.partner.id})

        warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
        warehouse.name = "RO Company"
        customer = env.ref("stock.stock_location_customers")
        cls.picking = env["stock.picking"].create(
            {
                "picking_type_id": warehouse.out_type_id.id,
                "partner_id": cls.partner.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": customer.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 4,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": warehouse.lot_stock_id.id,
                            "location_dest_id": customer.id,
                        }
                    )
                ],
            }
        )
        cls.picking.action_confirm()
        cls.cron = env.ref("deltatech_alternative.ir_cron_split_alternative_codes")
        cls.settings_action = env.ref("purchase.action_purchase_configuration")
        env.flush_all()

    def _form(self, record, action, menu):
        return f"action={action}&model={record._name}&id={record.id}&view_type=form&menu_id={self.env.ref(menu).id}"

    def _shots(self):
        product_form = self._form(self.product_tmpl, "sale.product_template_action", "sale.sale_menu_root")
        scroll_setting = (
            "document.querySelector(\"[name='alternative_search']\")"
            ".closest('.o_setting_box, .o_setting_container, .row').scrollIntoView({block: 'center'})"
        )
        return [
            # 1. codurile alternative ale produsului, tabul Alternative
            {
                "url": product_form,
                "name": "01_tab_coduri_alternative.png",
                "wait": ".o_form_view",
                "click_tab": ALTERNATIVE_TAB,
                "eval": SHOW_BADGES_JS,
                "highlight": [
                    "div[name='alternative_ids'] th[data-name='name']",
                    "div[name='alternative_ids'] tr:has(td:has-text('OLD-0457')) td[name='hide']",
                ],
            },
            # 2. câmpul combinat Cod alternativ și Utilizat la, pe tabul Informații generale
            {
                "url": product_form,
                "name": "02_produs_cod_alternativ.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='alternative_code']", "div[name='used_for']"],
            },
            # 3. lista produselor, cu coloanele Cod alternativ și Utilizat la
            {
                "url": "action=sale.product_template_action&view_type=list"
                f"&menu_id={self.env.ref('sale.sale_menu_root').id}",
                "name": "03_lista_produse.png",
                "wait": ".o_list_view",
                "eval": FILTER_BY_CODE,
                "eval_wait": 1500,
                "highlight": [
                    ".o_searchview_facet:has-text('366')",
                    "td[name='alternative_code']",
                    "td[name='used_for']",
                ],
            },
            # 4. setările căutării după cod alternativ (Setări → Achiziții, blocul Produse)
            {
                "url": f"action={self.settings_action.id}",
                "name": "04_setari_cautare.png",
                "wait": "[name='alternative_search']",
                "timeout": 40000,
                "eval": scroll_setting,
                "settle": 3000,
                "highlight": [
                    "#alternative_search",
                    "#alternative_dropdown_code_first",
                    "#alternative_dropdown_show_qty",
                ],
            },
            # 5. căutarea produsului după o parte din codul alternativ, pe o comandă nouă
            {
                "url": self._form(self.order_new, "sale.action_quotations_with_onboarding", "sale.sale_menu_root"),
                "name": "05_cautare_comanda.png",
                "wait": ".o_form_view",
                "eval": SEARCH_BY_CODE,
                "eval_wait": 1000,
                "highlight": [".o-autocomplete--dropdown-menu"],
            },
            # 6. coloana Cod alternativ pe liniile comenzii de vânzare
            {
                "url": self._form(self.order, "sale.action_quotations_with_onboarding", "sale.sale_menu_root"),
                "name": "06_comanda_coloana_cod.png",
                "wait": ".o_form_view",
                "eval": {
                    lang: SHOW_OPTIONAL_COLUMN % {"field": "order_line", "label": label}
                    for lang, label in ALTERNATIVE_CODE.items()
                },
                "highlight": ["div[name='order_line'] td[name='alternative_code']"],
            },
            # 7. coloana Cod alternativ pe transferul de livrare
            {
                "url": self._form(self.picking, "stock.action_picking_tree_all", "stock.menu_stock_root"),
                "name": "07_transfer_coloana_cod.png",
                "wait": ".o_form_view",
                "eval": {
                    lang: SHOW_OPTIONAL_COLUMN % {"field": "move_ids", "label": label}
                    for lang, label in ALTERNATIVE_CODE.items()
                },
                "highlight": ["div[name='move_ids'] td[name='alternative_code']"],
            },
            # 8. acțiunea planificată care separă codurile scrise pe un singur rând
            {
                "url": self._form(self.cron, "base.ir_cron_act", "base.menu_administration"),
                "name": "08_actiune_planificata.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='code']"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1000), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1000), hide_systray=True, lang="en_US")
