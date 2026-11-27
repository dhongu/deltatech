# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Export și import linii comandă de vânzare în Excel" — generate în
# timpul testelor, în RO pentru fișă și în EN pentru readme/USAGE.md, pe „Demo Vânzări SRL" în RON.
#
# Comanda are produsul „Scaun birou" pe două linii (negru și gri). Fișierul clientului fără coloana
# Descriere dă eroare la Test, pentru că rândul se potrivește cu ambele linii; fișierul cu coloana
# Descriere actualizează fiecare linie.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_sale_xls,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init --http-port=8987 --gevent-port=8988
import base64
import io
import json
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

# Antetele fișierului în limba interfeței, ca ecranul de import să mapeze singur coloanele.
HEADERS = {
    "ro_RO": {"product": "Produs", "name": "Descriere", "qty": "Cantitate"},
    "en_US": {"product": "Product", "name": "Description", "qty": "Quantity"},
}

SLEEP = "const sleep = (ms) => new Promise((r) => setTimeout(r, ms));\n"

# Selectează toate liniile din listă și deschide dialogul standard de export.
JS_EXPORT_BODY = """
    document.querySelector('thead .o_list_record_selector input').click();
    await sleep(800);
    [...document.querySelectorAll('.o_cp_action_menus button')]
        .find((b) => b.querySelector('.fa-cog')).click();
    await sleep(900);
    [...document.querySelectorAll('.o-dropdown-item')]
        .find((i) => i.textContent.trim().startsWith('Export')).click();
    await sleep(2500);
    // export compatibil cu importul, cu ID extern și Descriere: așa fișierul se poate reimporta
    document.querySelector('.modal .o_import_compat input').click();
    await sleep(1500);
    for (const fieldId of ['id', 'name']) {
        const add = document.querySelector(`.modal .o_export_tree_item[data-field_id='${fieldId}'] .o_add_field`);
        if (add) { add.click(); await sleep(600); }
    }
    // coloanele analitice (linii o2m) nu se trimit clientului: completate, ar crea linii analitice
    for (const item of document.querySelectorAll('.modal .o_fields_list li')) {
        if ((item.dataset.field_id || '').startsWith('analytic_line_ids')) {
            item.querySelector('.o_remove_field').click();
            await sleep(400);
        }
    }
"""


def open_action_js(action, then=""):
    """Deschide acțiunea peste pagina curentă și rulează apoi corpul JS ``then``."""
    return (
        "(async () => {"
        + SLEEP
        + f"await odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)});"
        + "await sleep(2000);"
        + then
        + "})()"
    )


def import_file_js(order_id, file_b64, file_name, lines_action, run_test=False):
    """Deschide ecranul standard de import pe liniile comenzii, încarcă fișierul și, opțional, apasă Test."""
    action = {
        "type": "ir.actions.client",
        "tag": "import",
        "params": {"active_model": "sale.order.line", "context": {"default_order_id": order_id}},
    }
    test = (
        """
    document.querySelector('.o_control_panel_main_buttons button.btn-primary').click();
    await sleep(3500);"""
        if run_test
        else ""
    )
    return (
        "(async () => {"
        + SLEEP
        + f"""
    // din lista Linii comandă, ca în fișă (breadcrumb: comandă / Linii comandă / import)
    await odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(lines_action)});
    await sleep(2000);
    await odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)});
    await sleep(2000);
    const bytes = Uint8Array.from(atob({json.dumps(file_b64)}), (c) => c.charCodeAt(0));
    const file = new File([bytes], {json.dumps(file_name)},
        {{type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}});
    const input = document.querySelector('.o_import_action input[type=file]')
        || document.querySelector('input[type=file]');
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', {{bubbles: true}}));
    await sleep(3500);{test}
}})()"""
    )


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleXlsScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_sale_xls"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        if openpyxl is None:
            raise unittest.SkipTest("capturile cer openpyxl")
        super().setUpClass()
        env = cls.env
        cls.prepare_ro_company(name="Demo Vânzări SRL")
        admin = env.ref("base.user_admin")
        admin.group_ids = [Command.link(env.ref("sales_team.group_sale_manager").id)]
        # baza fără plan de conturi RO: lista de prețuri în RON (curs 1) și TVA 21% pe produse
        ron = env.ref("base.RON")
        ron.active = True
        env["res.currency.rate"].search([("currency_id", "=", ron.id)]).unlink()
        env["res.currency.rate"].create({"currency_id": ron.id, "rate": 1.0, "name": "2020-01-01"})
        pricelist = env["product.pricelist"].create({"name": "Listă de prețuri RON", "currency_id": ron.id})
        tax_group = env["account.tax.group"].create({"name": "TVA 21%"})
        tax = env["account.tax"].create(
            {"name": "TVA 21%", "amount": 21.0, "type_tax_use": "sale", "tax_group_id": tax_group.id}
        )
        customer = env["res.partner"].create(
            {"name": "Client Exemplu SRL", "is_company": True, "property_product_pricelist": pricelist.id}
        )
        product = env["product.product"]
        taxes = {"taxes_id": [Command.set(tax.ids)]}
        cls.chair = product.create({"name": "Scaun birou", "default_code": "SC-01", "list_price": 450.0, **taxes})
        cls.table = product.create({"name": "Masă ședință", "default_code": "MS-02", "list_price": 1890.0, **taxes})
        cls.order = env["sale.order"].create(
            {
                "partner_id": customer.id,
                "pricelist_id": pricelist.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.chair.id,
                            "name": "Scaun birou - negru",
                            "product_uom_qty": 6,
                            "price_unit": 450,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.chair.id,
                            "name": "Scaun birou - gri",
                            "product_uom_qty": 2,
                            "price_unit": 450,
                        }
                    ),
                    Command.create(
                        {"product_id": cls.table.id, "name": "Masă ședință", "product_uom_qty": 1, "price_unit": 1890}
                    ),
                ],
            }
        )
        env.flush_all()

    @staticmethod
    def _xlsx(rows):
        book = openpyxl.Workbook()
        for row in rows:
            book.active.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        return base64.b64encode(buffer.getvalue()).decode()

    def _rows(self, lang, with_name):
        head = HEADERS[lang]
        if not with_name:
            return [[head["product"], head["qty"]], ["[SC-01] Scaun birou", 10], ["[MS-02] Masă ședință", 3]]
        return [
            [head["product"], head["name"], head["qty"]],
            ["[SC-01] Scaun birou", "Scaun birou - negru", 10],
            ["[SC-01] Scaun birou", "Scaun birou - gri", 4],
            ["[MS-02] Masă ședință", "Masă ședință", 3],
        ]

    def _capture(self, lang):
        order = self.order
        order_url = f"id={order.id}&model=sale.order&view_type=form"
        lines_action = order.with_context(lang=lang).show_order_lines()
        simple = self._xlsx(self._rows(lang, with_name=False))
        self.capture_screenshots(
            [
                {
                    "url": order_url,
                    "name": "01_comanda_buton_linii.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["button[name='show_order_lines']", "div[name='order_line'] .o_list_renderer"],
                },
                {
                    "url": order_url,
                    "name": "02_lista_linii.png",
                    "wait": ".o_form_view",
                    "eval": open_action_js(lines_action),
                    "eval_wait": 1500,
                    "highlight": [".o_list_renderer thead"],
                },
                {
                    "url": order_url,
                    "name": "03_export_linii.png",
                    "wait": ".o_form_view",
                    "eval": open_action_js(lines_action, JS_EXPORT_BODY),
                    "eval_wait": 1500,
                    "highlight": [".modal .o_import_compat", ".modal .o_fields_list", ".modal-footer .btn-primary"],
                },
                {
                    "url": order_url,
                    "name": "04_import_fisier.png",
                    "wait": ".o_form_view",
                    "eval": import_file_js(order.id, simple, "comanda_client.xlsx", lines_action),
                    "eval_wait": 1500,
                    "highlight": [
                        ".o_import_data_content table tbody",
                        ".o_control_panel_main_buttons button.btn-primary",
                    ],
                },
                {
                    "url": order_url,
                    "name": "05_import_eroare_linii_multiple.png",
                    "wait": ".o_form_view",
                    "eval": import_file_js(order.id, simple, "comanda_client.xlsx", lines_action, run_test=True),
                    "eval_wait": 1500,
                    "highlight": [".o_import_data_content .o_import_report"],
                },
            ],
            lang=lang,
        )
        # fișierul cu coloana Descriere: fiecare rând își găsește linia, apoi se importă
        result = (
            self.env["sale.order.line"]
            .with_context(default_order_id=order.id)
            .load(["product_id", "name", "product_uom_qty"], [row[:] for row in self._rows(lang, True)[1:]])
        )
        self.assertFalse([m for m in result["messages"] if m["type"] == "error"], result["messages"])
        self.assertEqual(sorted(order.order_line.mapped("product_uom_qty")), [3.0, 4.0, 10.0])
        self.env.flush_all()
        self.capture_screenshots(
            [
                {
                    "url": order_url,
                    "name": "06_comanda_actualizata.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["div[name='order_line'] td[name='product_uom_qty']"],
                },
            ],
            lang=lang,
        )

    def test_capture_fise(self):  # RO -> static/description, pentru fișă
        self._capture("ro_RO")

    def test_capture_usage(self):  # EN -> static/description/en, pentru readme/USAGE.md
        self._capture("en_US")
