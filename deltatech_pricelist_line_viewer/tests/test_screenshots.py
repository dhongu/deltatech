# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Vizualizarea liniilor listei de prețuri" — generate în timpul
# testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: butonul Linii Listă de Prețuri din formularul listei de prețuri, lista regulilor,
# căutarea după produs, deschiderea unei reguli și grupul Permite editarea listei de prețuri.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_pricelist_line_viewer,deltatech_doc_screenshots \
#       --test-tags=/deltatech_pricelist_line_viewer:TestPricelistLineViewerScreenshots --stop-after-init
import unittest
from datetime import datetime

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# deschide liniile listei de prețuri ca la clicul operatorului pe butonul din formular
OPEN_LINES_JS = """
    const until = async (selector) => {
        for (let i = 0; i < 100 && !document.querySelector(selector); i++) {
            await new Promise((resolve) => setTimeout(resolve, 100));
        }
        return document.querySelector(selector);
    };
    (await until("button[name='action_view_lines']")).click();
    // formularul listei de prețuri are și el o listă (tabul Prețuri de vânzare): așteptăm
    // bara de căutare, care apare doar în lista deschisă de buton
    await until(".o_searchview_input");
    await until(".o_list_view .o_data_row");
"""

# scrie textul în bara de căutare, ca să apară propunerile (Căutare Produs pentru: ...)
SEARCH_JS = """
    const input = document.querySelector(".o_searchview_input");
    input.focus();
    input.value = "{text}";
    input.dispatchEvent(new Event("input", {{bubbles: true}}));
    // lista de propuneri taie bulina numerotată a primei propuneri: o lăsăm să depășească
    (await until(".o_searchview_autocomplete")).style.overflow = "visible";
"""

# deschide regula de pe rândul dat
OPEN_ROW_JS = """
    document.querySelectorAll(".o_list_view .o_data_row")[{row}].querySelector("td.o_data_cell").click();
    await until(".o_form_view .o_form_sheet");
"""

# titlul grupului e un câmp îngust: îl lărgim ca numele să se vadă întreg
# antetul taburilor taie bulina numerotată a tabului evidențiat: îl lăsăm să depășească
WIDEN_NAME_JS = """() => {
    document.querySelector("div[name='name'] input").style.width = "16em";
    document.querySelectorAll(".o_notebook_headers, .o_notebook_headers .nav").forEach((el) => {
        el.style.overflow = "visible";
    });
}"""


def _js(*parts):
    return "async () => {" + OPEN_LINES_JS + "".join(parts) + "}"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPricelistLineViewerScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_pricelist_line_viewer"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        # o bază instalată doar în română are engleza inactivă: capturile EN ar ieși tot în RO
        cls.env.ref("base.lang_en").active = True
        # setarea Vânzări → Liste de prețuri (meniul și câmpul Listă de prețuri din căutare)
        cls.env["res.config.settings"].create({"group_product_pricelist": True}).execute()
        currency = cls.env.company.currency_id

        def product(name_ro, name_en, code, price):
            tmpl = cls.env["product.template"].create(
                {"name": name_ro, "default_code": code, "list_price": price, "sale_ok": True}
            )
            tmpl.update_field_translations("name", {"ro_RO": name_ro, "en_US": name_en})
            return tmpl

        laptop = product('Laptop 15,6" Pro', 'Laptop 15.6" Pro', "LAP-156", 4200.0)
        monitor = product('Monitor 27" 4K', 'Monitor 27" 4K', "MON-27K", 1650.0)
        mouse = product("Mouse wireless", "Wireless mouse", "MOU-WL", 89.0)
        keyboard = product("Tastatură mecanică", "Mechanical keyboard", "TAS-MEC", 349.0)
        dock = product("Stație de andocare USB-C", "USB-C docking station", "DOC-USBC", 720.0)

        cls.pricelist = cls.env["product.pricelist"].create({"name": "Distribuitori 2026", "currency_id": currency.id})
        cls.pricelist.update_field_translations("name", {"ro_RO": "Distribuitori 2026", "en_US": "Resellers 2026"})
        # Dată sfârșit conține și ora: 23:59:59, ca regula să se aplice toată ultima zi
        start, end = datetime(2026, 1, 1), datetime(2026, 12, 31, 23, 59, 59)
        rules = [
            (laptop, 1, 3950.0, start, end),
            (laptop, 10, 3790.0, start, end),
            (monitor, 1, 1540.0, start, end),
            (monitor, 5, 1480.0, start, end),
            (mouse, 1, 79.0, False, False),
            (mouse, 50, 69.0, False, False),
            (keyboard, 1, 319.0, start, end),
            (dock, 1, 665.0, datetime(2026, 11, 1), datetime(2026, 11, 30, 23, 59, 59)),
        ]
        cls.env["product.pricelist.item"].create(
            [
                {
                    "pricelist_id": cls.pricelist.id,
                    "applied_on": "1_product",
                    "product_tmpl_id": tmpl.id,
                    "min_quantity": qty,
                    "compute_price": "fixed",
                    "fixed_price": price,
                    "date_start": d_start,
                    "date_end": d_end,
                }
                for tmpl, qty, price, d_start, d_end in rules
            ]
        )
        cls.group = cls.env.ref("deltatech_pricelist_line_viewer.group_user_permit_prilist_edit_access")
        # un agent de vânzări care primește dreptul de a modifica listele de prețuri
        salesman = cls.env["res.users"].create(
            {
                "name": "Ana Popescu",
                "login": "ana.popescu",
                "email": "ana.popescu@example.ro",
                "group_ids": [(6, 0, [cls.env.ref("sales_team.group_sale_salesman").id])],
            }
        )
        cls.group.user_ids = [(4, salesman.id)]
        cls.env.flush_all()

    def _shots(self):
        form = f"id={self.pricelist.id}&model=product.pricelist&view_type=form"
        search = {"ro_RO": "Laptop", "en_US": "Laptop"}
        return [
            # 1. formularul listei de prețuri, cu butonul Linii Listă de Prețuri
            {
                "url": form,
                "name": "01_buton_linii_lista_preturi.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='action_view_lines']"],
            },
            # 2. lista regulilor listei de prețuri, deschisă din buton
            {
                "url": form,
                "name": "02_lista_linii_preturi.png",
                "wait": ".o_form_view",
                "eval": _js(),
                "eval_wait": 1500,
                "highlight": [".o_breadcrumb"],
            },
            # 3. căutarea după produs, în bara de căutare a listei
            {
                "url": form,
                "name": "03_cautare_produs.png",
                "wait": ".o_form_view",
                "eval": _js(SEARCH_JS.format(text=search["ro_RO"])),
                "eval_wait": 1500,
                "highlight": [".o_searchview_input_container", ".o_searchview_autocomplete .o-dropdown-item >> nth=0"],
            },
            # 4. o regulă deschisă din listă, în formularul standard al regulii
            {
                "url": form,
                "name": "04_formular_regula.png",
                "wait": ".o_form_view",
                "eval": _js(OPEN_ROW_JS.format(row=1)),
                "eval_wait": 1500,
                "highlight": ["div[name='min_quantity']", "div[name='fixed_price']"],
            },
            # 5. grupul Permite editarea listei de prețuri, cu utilizatorii lui (mod dezvoltator)
            {
                "path": f"/odoo/action-base.action_res_groups/{self.group.id}?debug=1",
                "name": "05_grup_utilizatori.png",
                "wait": ".o_form_view",
                "eval": WIDEN_NAME_JS,
                "highlight": [
                    "div[name='name']",
                    ".nav-link[name='user_ids']",
                    "div[name='user_ids'] .o_field_x2many_list_row_add a",
                ],
            },
            # 6. drepturile de acces date de grup: citire, scriere, creare, ștergere
            {
                "path": f"/odoo/action-base.action_res_groups/{self.group.id}?debug=1",
                "name": "06_grup_drepturi_acces.png",
                "wait": ".o_form_view",
                "eval": """async () => {
                    ("""
                + WIDEN_NAME_JS
                + """)();
                    document.querySelector(".nav-link[name='access_rights']").click();
                    await new Promise((resolve) => setTimeout(resolve, 800));
                    // coloana Nume e lată, iar antetul Acces Ștergere ieșea trunchiat
                    const nameTh = document.querySelector("div[name='access_ids'] th[data-name='name']");
                    if (nameTh) { nameTh.style.width = "220px"; }
                }""",
                "highlight": [".nav-link[name='access_rights']"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1600, 950), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1600, 950), hide_systray=True, lang="en_US")
