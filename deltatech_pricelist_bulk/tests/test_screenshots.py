# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Reguli de preț în masă" — generate în timpul testelor, în limba RO
# (fișa) și EN (readme/USAGE.md).
#
# Fluxul: butoanele din formularul listei de prețuri, asistentul Adaugă reguli completat, regulile
# adăugate, acțiunea Adaugă în lista de prețuri din lista de produse, asistentul Aplică formula și
# regulile după aplicarea formulei.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> --without-demo=all \
#       -i deltatech_pricelist_bulk,deltatech_doc_screenshots,sale_management,l10n_ro \
#       --test-tags=/deltatech_pricelist_bulk:TestPricelistBulkScreenshots --stop-after-init
import json
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

HELPERS_JS = """
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const until = async (selector) => {
        for (let i = 0; i < 100 && !document.querySelector(selector); i++) {
            await sleep(100);
        }
        return document.querySelector(selector);
    };
    // scrie o valoare într-un câmp numeric al dialogului, ca la tastarea operatorului
    const type = async (name, value) => {
        const input = await until(`.modal div[name='${name}'] input`);
        input.focus();
        input.value = value;
        input.dispatchEvent(new Event("input", {bubbles: true}));
        input.dispatchEvent(new Event("change", {bubbles: true}));
        await sleep(400);
    };
    const radio = async (name, value) => {
        (await until(`.modal div[name='${name}'] input[data-value='${value}']`)).click();
        await sleep(500);
    };
    // câmpurile de selecție sunt SelectMenu: deschidem lista și alegem a N-a opțiune
    const select = async (name, index) => {
        (await until(`.modal div[name='${name}'] .o_select_menu_toggler`)).click();
        await until(".o_select_menu_menu .o_select_menu_item");
        document.querySelectorAll(".o_select_menu_menu .o_select_menu_item")[index].click();
        await sleep(600);
    };
"""

# asistentul Adaugă reguli, deschis cu produsele categoriei Periferice deja alese și completat cu
# formula: 10% reducere din prețul de vânzare, rotunjit la 1 leu, minus 0,01 (prețuri în ,99)
ADD_WIZARD_JS = """
    const action = odoo.__WOWL_DEBUG__.root.env.services.action;
    await action.doAction("deltatech_pricelist_bulk.action_pricelist_bulk_add", {
        additionalContext: %(context)s,
    });
    await until(".modal div[name='product_tmpl_ids'] .o_data_row");
    await radio("compute_price", "formula");
    await type("price_discount", "10");
    await type("price_round", "1");
    await type("price_surcharge", "-0{DEC}01");
"""

APPLY_JS = """
    (await until(".modal button[name='action_apply']")).click();
    for (let i = 0; i < 100 && document.querySelector(".modal"); i++) {
        await sleep(100);
    }
    await sleep(800);
"""

# asistentul Aplică formula, deschis din butonul formularului: adaos 35% pe cost, rotunjit la
# 1 leu, minus 0,01
FORMULA_WIZARD_JS = """
    (await until("button[name='action_pricelist_bulk_formula']")).click();
    await until(".modal div[name='item_ids'] .o_data_row");
    await radio("compute_price", "formula");
    await select("base", 1);  // Cost
    await type("price_markup", "35");
    await type("price_round", "1");
    await type("price_surcharge", "-0{DEC}01");
"""

# lista de produse: bifăm produsele categoriei Periferice și deschidem meniul Acțiuni
PRODUCT_ACTIONS_JS = """
    await until(".o_list_view .o_data_row");
    const rows = [...document.querySelectorAll(".o_list_view .o_data_row")];
    // primele trei produse din categoria Periferice (codurile A-...)
    const peripherals = rows.filter((row) => row.textContent.includes("A-"));
    for (const row of peripherals.slice(0, 3)) {
        row.querySelector(".o_list_record_selector input").click();
        await sleep(200);
    }
    (await until(".o_cp_action_menus button.dropdown-toggle")).click();
    await until(".o-dropdown--menu .o-dropdown-item");
"""


def _js(*parts):
    """Codul JS al unui shot, pe limbi: valorile zecimale se tastează cu separatorul limbii."""
    code = "async () => {" + HELPERS_JS + "".join(parts) + "}"
    return {"ro_RO": code.replace("{DEC}", ","), "en_US": code.replace("{DEC}", ".")}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPricelistBulkScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_pricelist_bulk"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        # o bază instalată doar în română are engleza inactivă: capturile EN ar ieși tot în RO
        cls.env.ref("base.lang_en").active = True
        # setarea Liste de prețuri: meniul și butoanele de pe formularul listei
        cls.env["res.config.settings"].create({"group_product_pricelist": True}).execute()
        currency = cls.env.ref("base.RON")
        currency.active = True

        categ = cls.env["product.category"].create({"name": "Periferice"})
        laptops = cls.env["product.category"].create({"name": "Laptopuri"})

        def product(name_ro, name_en, code, price, cost, category):
            tmpl = cls.env["product.template"].create(
                {
                    "name": name_ro,
                    "default_code": code,
                    "list_price": price,
                    "standard_price": cost,
                    "categ_id": category.id,
                    "sale_ok": True,
                }
            )
            tmpl.update_field_translations("name", {"ro_RO": name_ro, "en_US": name_en})
            return tmpl

        # codurile încep cu A/B..., ca lista de produse să le arate primele, în ordinea asta
        cls.peripherals = (
            product("Căști cu microfon", "Headset with microphone", "A-CAS", 189.0, 110.0, categ)
            | product("Mouse wireless", "Wireless mouse", "A-MOU", 89.0, 48.0, categ)
            | product("Tastatură mecanică", "Mechanical keyboard", "A-TAS", 349.0, 205.0, categ)
            | product("Cameră web Full HD", "Full HD webcam", "A-WEB", 259.0, 150.0, categ)
            | product("Hub USB-C 7 porturi", "7-port USB-C hub", "A-HUB", 145.0, 82.0, categ)
        )
        laptop = product('Laptop 15,6" Pro', 'Laptop 15.6" Pro', "B-LAP", 4200.0, 3300.0, laptops)

        cls.pricelist = cls.env["product.pricelist"].create({"name": "Distribuitori 2026", "currency_id": currency.id})
        cls.pricelist.update_field_translations("name", {"ro_RO": "Distribuitori 2026", "en_US": "Resellers 2026"})
        cls.env["product.pricelist.item"].create(
            [
                {
                    "pricelist_id": cls.pricelist.id,
                    "applied_on": "1_product",
                    "product_tmpl_id": laptop.id,
                    "min_quantity": qty,
                    "compute_price": "fixed",
                    "fixed_price": price,
                }
                for qty, price in ((1, 3950.0), (10, 3790.0))
            ]
        )
        cls.env.flush_all()

    def _shots(self):
        form = f"id={self.pricelist.id}&model=product.pricelist&view_type=form"
        add_context = json.dumps(
            {
                "default_pricelist_id": self.pricelist.id,
                "default_product_tmpl_ids": self.peripherals.ids,
                "default_compute_price": "formula",
            }
        )
        add_js = ADD_WIZARD_JS % {"context": add_context}
        wizard_highlight = [
            ".modal div[name='applied_on']",
            ".modal div[name='product_tmpl_ids']",
            ".modal div[name='compute_price']",
            ".modal div[name='existing_policy']",
        ]
        return [
            # 1. formularul listei de prețuri, cu butoanele Adaugă reguli și Aplică formula
            {
                "url": form,
                "name": "01_formular_lista_preturi.png",
                "wait": ".o_form_view",
                "highlight": [
                    "button[name='action_pricelist_bulk_add']",
                    "button[name='action_pricelist_bulk_formula']",
                ],
            },
            # 2. asistentul Adaugă reguli, completat pentru produsele categoriei Periferice
            {
                "url": form,
                "name": "02_asistent_adauga_reguli.png",
                "wait": ".o_form_view",
                "eval": _js(add_js),
                "eval_wait": 1000,
                "highlight": wizard_highlight,
            },
            # 3. regulile adăugate: mesajul cu numărul lor și lista regulilor
            {
                "url": form,
                "name": "03_reguli_adaugate.png",
                "wait": ".o_form_view",
                "eval": _js(add_js, APPLY_JS, 'await until(".o_list_view .o_data_row");'),
                "eval_wait": 1000,
                "settle": 300,
                "highlight": [".o_notification", ".o_list_table"],
            },
            # 4. lista de produse cu trei produse bifate și acțiunea Adaugă în lista de prețuri
            {
                "url": "action=sale.product_template_action&view_type=list",
                "name": "04_actiune_din_produse.png",
                "wait": ".o_list_view",
                "hide_fields": ["taxes_id"],
                "eval": _js(PRODUCT_ACTIONS_JS),
                "eval_wait": 800,
                "highlight": {
                    "ro_RO": [".o-dropdown-item:has-text('Adaugă în lista de prețuri')"],
                    "en_US": [".o-dropdown-item:has-text('Add to Pricelist')"],
                },
            },
            # 5. asistentul Aplică formula pe toate regulile listei: adaos 35% pe cost
            {
                "url": form,
                "name": "05_asistent_aplica_formula.png",
                "wait": ".o_form_view",
                "eval": _js(FORMULA_WIZARD_JS),
                "eval_wait": 1000,
                "highlight": [
                    ".modal div[name='change_price']",
                    ".modal div[name='base']",
                    ".modal div[name='item_ids']",
                ],
            },
            # 6. regulile listei după aplicarea formulei
            {
                "url": form,
                "name": "06_reguli_dupa_formula.png",
                "wait": ".o_form_view",
                "eval": _js(FORMULA_WIZARD_JS, APPLY_JS),
                "eval_wait": 1500,
                "settle": 300,
                "highlight": [".o_notification", ".o_form_view .o_field_widget[name='item_ids'] .o_list_renderer"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1600, 950), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1600, 950), hide_systray=True, lang="en_US")
