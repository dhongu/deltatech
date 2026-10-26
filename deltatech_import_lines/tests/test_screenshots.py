# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Import linii document" — generate în timpul testelor, în limba RO,
# pe compania „Demo Import SRL" în RON. Cer și punțile de vânzări, achiziții, stoc și producție.
#
# Asistentul se pregătește pe server (fișier încărcat, coloane mapate, previzualizare) și se
# deschide peste document cu serviciul de acțiuni, ca dialogul pe care îl vede operatorul.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_import_lines_sale,deltatech_import_lines_purchase,deltatech_import_lines_stock,\
#          deltatech_import_lines_mrp,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
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

BRIDGE_MODELS = ("sale.order", "purchase.order", "stock.picking", "stock.quant", "mrp.production")
DIALOG = ".modal .o_form_view"


def open_wizard_js(wizard):
    """JS care deschide asistentul deja pregătit pe server, ca dialog peste pagina curentă."""
    action = {
        "type": "ir.actions.act_window",
        "res_model": "import.lines.wizard",
        "res_id": wizard.id,
        "views": [[False, "form"]],
        "target": "new",
        "name": "Import linii",
        "context": {"import_lines_model": wizard.res_model, "dialog_size": "extra-large"},
    }
    return (
        "(async () => {"
        f"await odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)});"
        "await new Promise((r) => setTimeout(r, 1500));"
        "document.activeElement && document.activeElement.blur();"
        "})()"
    )


@tagged("-at_install", "post_install", "fise_screenshots")
class TestImportLinesScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_import_lines"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        mixin_models = env.registry["import.lines.mixin"]._inherit_children
        if openpyxl is None or any(model not in mixin_models for model in BRIDGE_MODELS):
            raise unittest.SkipTest("capturile cer punțile de vânzări, achiziții, stoc și producție")
        cls.prepare_ro_company(name="Demo Import SRL")
        admin = env.ref("base.user_admin")
        groups = (
            env.ref("sales_team.group_sale_manager")
            | env.ref("purchase.group_purchase_manager")
            | env.ref("stock.group_stock_manager")
            | env.ref("stock.group_production_lot")
            | env.ref("mrp.group_mrp_manager")
        )
        admin.group_ids = [Command.link(group.id) for group in groups]

        # baza fără plan de conturi RO: moneda RON pe lista de prețuri și pe comenzi, TVA 21% pe produse
        cls.ron = env.ref("base.RON")
        cls.ron.active = True
        # curs 1, ca prețurile din fișa produsului să apară neschimbate în lei
        env["res.currency.rate"].search([("currency_id", "=", cls.ron.id)]).unlink()
        env["res.currency.rate"].create({"currency_id": cls.ron.id, "rate": 1.0, "name": "2020-01-01"})
        pricelist = env["product.pricelist"].create({"name": "Listă de prețuri RON", "currency_id": cls.ron.id})
        tax_group = env["account.tax.group"].create({"name": "TVA 21%"})
        tax_vals = {"name": "TVA 21%", "amount": 21.0, "tax_group_id": tax_group.id}
        sale_tax = env["account.tax"].create(dict(tax_vals, type_tax_use="sale"))
        purchase_tax = env["account.tax"].create(dict(tax_vals, type_tax_use="purchase"))
        taxes = {"taxes_id": [Command.set(sale_tax.ids)], "supplier_taxes_id": [Command.set(purchase_tax.ids)]}
        cls.customer = env["res.partner"].create(
            {"name": "Client Exemplu SRL", "is_company": True, "property_product_pricelist": pricelist.id}
        )
        cls.vendor = env["res.partner"].create({"name": "Furnizor Exemplu SRL", "is_company": True})
        product = env["product.product"]
        cls.chair = product.create(
            {"name": "Scaun birou", "default_code": "SC-01", "list_price": 450.0, "is_storable": True, **taxes}
        )
        cls.table = product.create(
            {"name": "Masă ședință", "default_code": "MS-02", "list_price": 1890.0, "is_storable": True, **taxes}
        )
        cls.cabinet = product.create(
            {
                "name": "Dulap arhivă",
                "default_code": "DA-03",
                "list_price": 1250.0,
                "is_storable": True,
                **taxes,
                "seller_ids": [Command.create({"partner_id": cls.vendor.id, "product_code": "F-7710", "price": 820.0})],
            }
        )
        cls.board = product.create(
            {
                "name": "Placă PAL 18 mm",
                "default_code": "PAL-18",
                "is_storable": True,
                **taxes,
                "seller_ids": [Command.create({"partner_id": cls.vendor.id, "product_code": "F-2018", "price": 96.0})],
            }
        )
        cls.paint = product.create(
            {"name": "Vopsea lavabilă 15 L", "default_code": "VL-15", "is_storable": True, "tracking": "lot"}
        )
        env["stock.lot"].create({"name": "L2610-01", "product_id": cls.paint.id})
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
        cls.warehouse.name = "Depozit central"
        env.flush_all()

    @classmethod
    def _xlsx(cls, rows):
        book = openpyxl.Workbook()
        for row in rows:
            book.active.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        return base64.b64encode(buffer.getvalue())

    def _wizard(self, document, rows, file_name, context=None, **vals):
        ctx = {"active_model": document._name, "active_id": document.id}
        ctx.update(context or {})
        values = {"file": self._xlsx(rows), "file_name": file_name}
        values.update(vals)
        return self.env["import.lines.wizard"].with_context(**ctx).create(values)

    @staticmethod
    def _form_url(record):
        return f"id={record.id}&model={record._name}&view_type=form"

    def test_capture_fise(self):
        env = self.env
        # --- vânzări: comanda, asistentul în cei trei pași, liniile importate, maparea
        order = env["sale.order"].create({"partner_id": self.customer.id})
        rows = [
            ["Cod", "Denumire", "Cantitate", "Preț unitar"],
            ["SC-01", "Scaun birou", 12, ""],
            ["MS-02", "Masă ședință", 2, 1750],
            ["DA-03", "Dulap arhivă", 4, ""],
            ["SC-99", "Scaun vizitator", 6, ""],
        ]
        wizard_file = self._wizard(order, rows, "comanda_client.xlsx")
        wizard_map = self._wizard(order, rows, "comanda_client.xlsx")
        wizard_map.action_load()
        wizard_map.column_ids.filtered(lambda c: c.column_index == 2).target = False
        wizard_preview = self._wizard(order, rows, "comanda_client.xlsx")
        wizard_preview.action_load()
        wizard_preview.column_ids.filtered(lambda c: c.column_index == 2).target = False
        wizard_preview.action_preview()
        env.flush_all()
        order_url = self._form_url(order)
        self.capture_screenshots(
            [
                {
                    "url": order_url,
                    "name": "01_comanda_buton_import.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["button:has-text('Import linii')"],
                },
                {
                    "url": order_url,
                    "name": "02_asistent_fisier.png",
                    "wait": ".o_form_view",
                    "eval": open_wizard_js(wizard_file),
                    "eval_wait": 2000,
                    "settle": 1500,
                    "highlight": [
                        ".modal div[name='file']",
                        ".modal div[name='has_header']",
                        ".modal div[name='match_by']",
                        ".modal button[name='action_load']",
                    ],
                },
                {
                    "url": order_url,
                    "name": "03_asistent_coloane.png",
                    "wait": ".o_form_view",
                    "eval": open_wizard_js(wizard_map),
                    "eval_wait": 2000,
                    "settle": 1500,
                    "highlight": [
                        ".modal div[name='column_ids']",
                        ".modal div[name='mapping_name']",
                        ".modal button[name='action_preview']",
                    ],
                },
                {
                    "url": order_url,
                    "name": "04_asistent_previzualizare.png",
                    "wait": ".o_form_view",
                    "eval": open_wizard_js(wizard_preview),
                    "eval_wait": 2000,
                    "settle": 1500,
                    "highlight": [
                        ".modal .alert-warning",
                        ".modal div[name='skip_errors']",
                        ".modal button[name='action_import']",
                    ],
                },
            ]
        )
        # operatorul salvează maparea pe client, omite rândul negăsit și importă
        wizard_preview.write({"mapping_name": "Comenzi Client Exemplu", "mapping_for_partner": True})
        wizard_preview.action_back()
        wizard_preview.action_save_mapping()
        mapping = wizard_preview.mapping_id
        wizard_preview.action_preview()
        wizard_preview.skip_errors = True
        wizard_preview.action_import()
        self.assertEqual(len(order.order_line), 3)

        # --- achiziții: fișierul furnizorului, cu codurile lui
        purchase = env["purchase.order"].create({"partner_id": self.vendor.id, "currency_id": self.ron.id})
        vendor_rows = [["Cod articol", "Cant.", "U.M."], ["F-7710", 5, "Units"], ["F-2018", 40, "Units"]]
        wizard_purchase = self._wizard(purchase, vendor_rows, "oferta_furnizor.xlsx", match_by="vendor_code")
        wizard_purchase.action_load()
        for column, target in zip(wizard_purchase.column_ids, ("product", "quantity", "uom"), strict=True):
            column.target = target
        wizard_purchase.action_preview()

        # --- recepție cu loturi
        receipt = env["stock.picking"].create(
            {
                "picking_type_id": self.warehouse.in_type_id.id,
                "partner_id": self.vendor.id,
                "location_id": env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            }
        )
        receipt_rows = [
            ["Cod", "Cantitate", "Lot"],
            ["VL-15", 20, "L2610-01"],
            ["VL-15", 10, "L2610-02"],
            ["PAL-18", 40, ""],
        ]
        wizard_receipt = self._wizard(receipt, receipt_rows, "aviz_furnizor.xlsx")
        wizard_receipt.action_load()
        wizard_receipt.action_preview()

        # --- inventar: numărătoarea pe locație
        count_rows = [["Cod", "Cantitate", "Lot"], ["SC-01", 18, ""], ["MS-02", 3, ""], ["VL-15", 7, "L2610-01"]]
        wizard_count = self._wizard(
            env["stock.quant"],
            count_rows,
            "inventar_raft_A.xlsx",
            context={"import_lines_model": "stock.quant", "inventory_mode": True},
        )
        wizard_count.action_load()
        wizard_count.action_preview()

        # --- producție: componentele comenzii
        production = env["mrp.production"].create({"product_id": self.cabinet.id, "product_qty": 4})
        wizard_mrp = self._wizard(production, [["Cod", "Cantitate"], ["PAL-18", 24]], "componente.xlsx")
        wizard_mrp.action_load()
        wizard_mrp.action_preview()
        wizard_mrp.action_import()
        env.flush_all()

        self.capture_screenshots(
            [
                {
                    "url": order_url,
                    "name": "05_comanda_linii_importate.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["div[name='order_line'] .o_list_renderer"],
                },
                {
                    "url": self._form_url(mapping),
                    "name": "06_mapare_salvata.png",
                    "wait": ".o_form_view",
                    "settle": 1500,
                    "highlight": ["div[name='partner_id']", "div[name='column_ids']"],
                },
                {
                    "url": self._form_url(purchase),
                    "name": "07_achizitie_cod_furnizor.png",
                    "wait": ".o_form_view",
                    "eval": open_wizard_js(wizard_purchase),
                    "eval_wait": 2000,
                    "settle": 1500,
                    "highlight": [".modal div[name='match_by']", ".modal div[name='row_ids']"],
                },
                {
                    "url": self._form_url(receipt),
                    "name": "08_receptie_loturi.png",
                    "wait": ".o_form_view",
                    "eval": open_wizard_js(wizard_receipt),
                    "eval_wait": 2000,
                    "settle": 1500,
                    "highlight": [".modal div[name='row_ids']"],
                },
            ]
        )
        wizard_receipt.action_import()
        env.flush_all()
        self.capture_screenshots(
            [
                {
                    "url": self._form_url(receipt),
                    "name": "09_receptie_linii_importate.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["div[name='move_ids'] .o_list_renderer"],
                },
                {
                    "path": "/odoo/physical-inventory",
                    "name": "10_inventar_buton_import.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                    "highlight": ["button:has-text('Import cantități numărate')"],
                },
                {
                    "path": "/odoo/physical-inventory",
                    "name": "11_inventar_previzualizare.png",
                    "wait": ".o_list_view",
                    "eval": open_wizard_js(wizard_count),
                    "eval_wait": 2000,
                    "settle": 1500,
                    "highlight": [".modal div[name='location_id']", ".modal div[name='row_ids']"],
                },
            ]
        )
        wizard_count.action_import()
        env.flush_all()
        self.capture_screenshots(
            [
                {
                    "path": "/odoo/physical-inventory",
                    "name": "12_inventar_cantitati_numarate.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                    "highlight": ["th[data-name='inventory_quantity']", "button[name='action_apply_all']"],
                },
                {
                    "url": self._form_url(production),
                    "name": "13_productie_componente.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": ["button:has-text('Import componente')", "div[name='move_raw_ids'] .o_list_renderer"],
                },
            ]
        )
