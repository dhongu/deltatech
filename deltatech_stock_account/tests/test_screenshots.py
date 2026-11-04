# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Extensii la evaluarea stocului" — generate în timpul testelor,
# în limba RO (fișa) și EN (readme/USAGE.md), pe compania cu planul de conturi RO.
#
# Fluxul: valoarea transferurilor în listele Recepții și Livrări, conturile categoriei-părinte
# copiate pe subcategorii, acțiunea Propagate Accounts, setările preluate la alegerea categoriei
# superioare, refuzul modificării costului pentru un utilizator fără drept și grupul care dă dreptul.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_stock_account,deltatech_doc_screenshots,l10n_ro \
#       --test-tags=/deltatech_stock_account:TestStockAccountScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

OPERATOR = "operator_stoc"

# lista se mai redesenează după încărcare: evidențierea se pune după ce s-a stabilizat
LIST_READY_JS = "async () => new Promise((resolve) => setTimeout(resolve, 2000))"

# categoria nouă: numele și categoria superioară alese ca de operator (autocomplete)
NEW_CATEGORY_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const until = async (selector) => {
        for (let i = 0; i < 100 && !document.querySelector(selector); i++) {
            await sleep(100);
        }
        return document.querySelector(selector);
    };
    const name = document.querySelector("div[name='name'] input, input#name_0, .oe_title input");
    name.value = "Corpuri de iluminat";
    name.dispatchEvent(new Event("input", {bubbles: true}));
    name.dispatchEvent(new Event("change", {bubbles: true}));
    const parent = document.querySelector("div[name='parent_id'] input");
    parent.focus();
    parent.value = "Electrice";
    parent.dispatchEvent(new Event("input", {bubbles: true}));
    const item = await until(".o-autocomplete--dropdown-item a, .o-autocomplete--dropdown-item");
    item.click();
    await sleep(1500);
}"""

# costul nou, salvat de un utilizator fără dreptul de a-l schimba
CHANGE_COST_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const input = document.querySelector("div[name='standard_price'] input");
    input.value = "9.50";
    input.dispatchEvent(new Event("input", {bubbles: true}));
    input.dispatchEvent(new Event("change", {bubbles: true}));
    await sleep(500);
    document.querySelector(".o_form_button_save").click();
    for (let i = 0; i < 100 && !document.querySelector(".modal .modal-body"); i++) {
        await sleep(100);
    }
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestStockAccountScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_stock_account"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        company = cls.prepare_ro_company(name="Demo Distribuție SRL")
        if company.chart_template != "ro":
            env["account.chart.template"].try_loading("ro", company, install_demo=False)
        cls.company = company

        def account(code):
            # planul RO are coduri pe 6 cifre (371000)
            accounts = env["account.account"].with_company(company)
            return accounts.search([("code", "in", (code, code.ljust(6, "0")))], limit=1)

        acc_371, acc_707, acc_607 = account("371"), account("707"), account("607")

        # categoriile: Mărfuri → Electrice → Becuri; subcategoriile au la început alte setări
        # (numele categoriilor nu se traduc: rămân în română și pe capturile EN)
        categ_model = env["product.category"].with_company(company)
        cls.categ_goods = categ_model.create({"name": "Mărfuri"})
        cls.categ_electric = categ_model.create(
            {"name": "Electrice", "parent_id": cls.categ_goods.id, "property_cost_method": "fifo"}
        )
        cls.categ_bulbs = categ_model.create(
            {"name": "Becuri", "parent_id": cls.categ_electric.id, "property_cost_method": "standard"}
        )
        cls.categ_goods.write(
            {
                "property_account_income_categ_id": acc_707.id,
                "property_account_expense_categ_id": acc_607.id,
                "property_cost_method": "average",
                "property_valuation": "real_time",
            }
        )
        # contul de stoc salvat pe părinte copiază setările pe toate subcategoriile
        cls.categ_goods.write({"property_stock_valuation_account_id": acc_371.id})
        assert acc_371 and acc_707 and acc_607, (acc_371, acc_707, acc_607)
        assert cls.categ_bulbs.property_stock_valuation_account_id == acc_371, (
            cls.categ_bulbs.property_stock_valuation_account_id,
            cls.categ_goods.property_stock_valuation_account_id,
        )
        assert cls.categ_bulbs.property_cost_method == "average"

        product_model = env["product.product"].with_company(company)
        cls.bulb = product_model.create(
            {
                "name": "Bec LED 9 W E27",
                "default_code": "BEC-LED9",
                "is_storable": True,
                "categ_id": cls.categ_bulbs.id,
                "standard_price": 8.0,
                "list_price": 15.0,
            }
        )
        cls.bulb.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Bec LED 9 W E27", "en_US": "LED bulb 9 W E27"}
        )
        cls.strip = product_model.create(
            {
                "name": "Prelungitor 3 prize",
                "default_code": "PRL-3P",
                "is_storable": True,
                "categ_id": cls.categ_electric.id,
                "standard_price": 25.0,
                "list_price": 45.0,
            }
        )
        cls.strip.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Prelungitor 3 prize", "en_US": "Power strip 3 sockets"}
        )

        partner_model = env["res.partner"]
        cls.vendor = partner_model.create({"name": "Furnizor Electro SRL"})
        cls.customer = partner_model.create({"name": "Client Retail SRL"})

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.warehouse = warehouse
        supplier_loc = env.ref("stock.stock_location_suppliers")
        customer_loc = env.ref("stock.stock_location_customers")
        cls._done_picking(
            warehouse.in_type_id, cls.vendor, supplier_loc, warehouse.lot_stock_id, [(cls.bulb, 100), (cls.strip, 20)]
        )
        cls._done_picking(warehouse.in_type_id, cls.vendor, supplier_loc, warehouse.lot_stock_id, [(cls.bulb, 50)])
        cls._done_picking(
            warehouse.out_type_id, cls.customer, warehouse.lot_stock_id, customer_loc, [(cls.bulb, 30), (cls.strip, 5)]
        )
        cls._done_picking(warehouse.out_type_id, cls.customer, warehouse.lot_stock_id, customer_loc, [(cls.bulb, 40)])
        # fără comandă de achiziție, recepția se evaluează la costul produsului (8,00 / 25,00)
        # o recepție încă neprimită: valoarea ei e zero până la validare
        cls._picking(
            warehouse.in_type_id, cls.vendor, supplier_loc, warehouse.lot_stock_id, [(cls.strip, 10)]
        ).action_confirm()

        # utilizatorul de magazie, fără grupul Change Product Price
        cls.operator = env["res.users"].create(
            {
                "name": "Ana Popescu (magazie)",
                "login": OPERATOR,
                "password": OPERATOR,
                "company_id": company.id,
                "company_ids": [Command.set(company.ids)],
                "group_ids": [
                    Command.set(
                        [
                            env.ref("base.group_user").id,
                            env.ref("stock.group_stock_manager").id,
                            env.ref("product.group_product_manager").id,
                        ]
                    )
                ],
            }
        )
        cls.group_price = env.ref("deltatech_stock_account.group_change_product_price")
        cls.group_price.user_ids = [Command.link(env.ref("base.user_admin").id)]
        env.flush_all()

    @classmethod
    def _picking(cls, picking_type, partner, location, location_dest, lines):
        return cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": partner.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "uom_id": product.uom_id.id,
                            "location_id": location.id,
                            "location_dest_id": location_dest.id,
                        }
                    )
                    for product, qty in lines
                ],
            }
        )

    @classmethod
    def _done_picking(cls, picking_type, partner, location, location_dest, lines):
        picking = cls._picking(picking_type, partner, location, location_dest, lines)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking._action_done()
        assert picking.state == "done"
        return picking

    def _shots_admin(self):
        categ_form = "model=product.category&view_type=form"
        return [
            # 1. lista Recepții: coloana valorii și totalul
            {
                "url": "action=stock.action_picking_tree_incoming&view_type=list",
                "name": "01_receptii_valoare.png",
                "wait": ".o_list_view",
                "eval": LIST_READY_JS,
                "highlight": ["td.o_data_cell[name='amount']", "tfoot td.o_list_number"],
            },
            # 2. lista Livrări: valoarea la cost a mărfii ieșite
            {
                "url": "action=stock.action_picking_tree_outgoing&view_type=list",
                "name": "02_livrari_valoare.png",
                "wait": ".o_list_view",
                "eval": LIST_READY_JS,
                "highlight": ["td.o_data_cell[name='amount']", "tfoot td.o_list_number"],
            },
            # 3. categoria-părinte: contul de stoc și setările contabile
            {
                "url": f"id={self.categ_goods.id}&{categ_form}",
                "name": "03_categorie_parinte_conturi.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='property_stock_valuation_account_id']",
                    "div[name='property_account_income_categ_id']",
                    "div[name='property_cost_method']",
                ],
            },
            # 4. subcategoria de pe nivelul al doilea: aceleași setări, copiate
            {
                "url": f"id={self.categ_bulbs.id}&{categ_form}",
                "name": "04_subcategorie_conturi_copiate.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='parent_id']",
                    "div[name='property_stock_valuation_account_id']",
                    "div[name='property_cost_method']",
                ],
            },
            # 5. acțiunea Propagate Accounts (mod dezvoltator), din meniul Acțiuni
            {
                "path": f"/web?debug=1#id={self.categ_goods.id}&{categ_form}",
                "name": "05_actiune_propagare_conturi.png",
                "wait": ".o_form_view",
                "click_btn": ".o_cp_action_menus button.dropdown-toggle",
                "wait_after": ".o-dropdown--menu",
                "highlight": [".o-dropdown--menu .o-dropdown-item:has-text('Propagate Accounts')"],
            },
            # 6. categorie nouă: alegerea categoriei superioare aduce setările ei
            {
                "url": categ_form,
                "name": "06_categorie_noua_setari_parinte.png",
                "wait": ".o_form_view",
                "eval": NEW_CATEGORY_JS,
                "eval_wait": 1500,
                "highlight": [
                    "div[name='parent_id']",
                    "div[name='property_stock_valuation_account_id']",
                    "div[name='property_cost_method']",
                ],
            },
        ]

    def _shots_operator(self):
        return [
            # 7. costul schimbat de un utilizator fără drept: eroare de acces
            {
                "url": f"id={self.bulb.product_tmpl_id.id}&model=product.template&view_type=form",
                "name": "07_cost_refuzat_fara_drept.png",
                "wait": ".o_form_view",
                "eval": CHANGE_COST_JS,
                "eval_wait": 1500,
                "highlight": [".modal .modal-content"],
            },
        ]

    def _shots_group(self):
        return [
            # 8. grupul Change Product Price și utilizatorii lui
            {
                "path": f"/web?debug=1#id={self.group_price.id}&model=res.groups&view_type=form",
                "name": "08_grup_modificare_cost.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='name']", "div[name='user_ids'] .o_data_row"],
            },
        ]

    def _capture(self, **kwargs):
        self.capture_screenshots(self._shots_admin(), hide_systray=True, **kwargs)
        self.capture_screenshots(self._shots_operator(), login=OPERATOR, hide_systray=True, **kwargs)
        self.capture_screenshots(self._shots_group(), hide_systray=True, **kwargs)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
