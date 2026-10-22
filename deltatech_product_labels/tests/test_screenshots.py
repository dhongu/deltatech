# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Etichete produs" — generate în timpul testelor, în limba RO, pe
# compania „Demo Magazin SRL", depozitul „Magazin Centru".
#
# Scenariul din fișă: cana și termosul cu cod de bare EAN-13, uleiul de măsline urmărit pe loturi
# (două loturi în stoc), o comandă de vânzare, o recepție de ulei fără lot și o machetă ZPL
# 40x25 la 203 dpi. Previzualizarea ZPL cere acces la api.labelary.com; fără rețea, captura ei
# se sare.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_product_labels,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import base64
import logging
import os
import subprocess
import tempfile
import unittest
from urllib.parse import urlsplit

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import _super_send

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

_logger = logging.getLogger(__name__)

ZPL_TEMPLATE = """<t t-name="deltatech_product_labels.fise_label_40x25_zpl">
<t t-foreach="docs._get_print_lines()" t-as="line">
^XA
^CI28
^PW320
^LL200
^FO10,12^A0N,26,22^FB300,2,0,L^FD<t t-out="line.product_id.with_context(display_default_code=False).display_name"/>^FS
^FO25,75^BY2^BEN,60,Y,N^FD<t t-out="(line.product_id.barcode or '')[:12]"/>^FS
^FO10,170^A0N,22,20^FD<t t-out="line.product_id.default_code or ''"/>^FS
<t t-if="line.lot">^FO170,170^A0N,22,20^FDLot: <t t-out="line.lot"/>^FS</t>
^XZ
</t>
</t>"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestProductLabelsScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_product_labels"

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        # previzualizarea ZPL apelează serviciul Labelary, blocat implicit în teste
        if urlsplit(r.url).hostname == "api.labelary.com":
            return _super_send(s, r, **kw)
        return super()._request_handler(s, r, **kw)

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        admin = env.ref("base.user_admin")
        for xmlid in ("sales_team.group_sale_manager", "stock.group_stock_manager", "stock.group_production_lot"):
            group = env.ref(xmlid)
            env.user.group_ids = [(4, group.id)]
            admin.group_ids = [(4, group.id)]
        admin.name = "Ioana Marin"

        cls.warehouse = env.ref("stock.warehouse0")
        cls.warehouse.write({"name": "Magazin Centru", "code": "MAG"})
        cls.location = cls.warehouse.lot_stock_id
        # fără lista de prețuri implicită: prețul de pe etichetă este prețul de vânzare
        env["ir.default"].search([("field_id.model", "=", "product.product.label")]).unlink()

        def product(name, code, barcode, price, tracking="none"):
            return env["product.template"].create(
                {
                    "name": name,
                    "default_code": code,
                    "barcode": barcode,
                    "type": "consu",
                    "is_storable": True,
                    "tracking": tracking,
                    "list_price": price,
                    "taxes_id": [(6, 0, tax.ids)],
                    "supplier_taxes_id": [(6, 0, [])],
                    "company_id": company.id,
                }
            )

        tax = env["account.tax"].create(
            {"name": "TVA 21%", "amount": 21, "type_tax_use": "sale", "company_id": company.id}
        )
        env["product.pricelist"].search([]).currency_id = company.currency_id
        cls.cana = product("Cană ceramică 350 ml", "CAN-350", "5940000001018", 39.0)
        cls.termos = product("Termos inox 0,5 l", "TRM-050", "5940000001025", 89.0)
        cls.ulei = product("Ulei de măsline extravirgin 1 l", "ULM-001", "5940000001032", 64.0, "lot")
        for template, qty in ((cls.cana, 40), (cls.termos, 15)):
            env["stock.quant"]._update_available_quantity(template.product_variant_id, cls.location, qty)
        cls.lots = env["stock.lot"]
        for lot_name, qty in (("UL-2609-01", 12), ("UL-2610-02", 8)):
            lot = env["stock.lot"].create(
                {"name": lot_name, "product_id": cls.ulei.product_variant_id.id, "company_id": company.id}
            )
            env["stock.quant"]._update_available_quantity(cls.ulei.product_variant_id, cls.location, qty, lot_id=lot)
            cls.lots |= lot

        customer = env["res.partner"].create({"name": "Casa Verde SRL", "city": "Cluj-Napoca"})
        supplier = env["res.partner"].create({"name": "Olivia Import SRL", "city": "București"})
        cls.sale = env["sale.order"].create(
            {
                "partner_id": customer.id,
                "warehouse_id": cls.warehouse.id,
                "order_line": [
                    (0, 0, {"product_id": cls.cana.product_variant_id.id, "product_uom_qty": 10}),
                    (0, 0, {"product_id": cls.termos.product_variant_id.id, "product_uom_qty": 5}),
                    (0, 0, {"product_id": cls.cana.product_variant_id.id, "product_uom_qty": 6}),
                ],
            }
        )
        cls.receipt = env["stock.picking"].create(
            {
                "partner_id": supplier.id,
                "picking_type_id": cls.warehouse.in_type_id.id,
                "location_id": env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": cls.location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.ulei.product_variant_id.id,
                            "product_uom_qty": 3,
                            "location_id": env.ref("stock.stock_location_suppliers").id,
                            "location_dest_id": cls.location.id,
                        },
                    )
                ],
            }
        )
        cls.receipt.action_confirm()

        # macheta ZPL de exemplu, definită de client ca raport de tip text pe modelul asistentului
        view = env["ir.ui.view"].create(
            {
                "name": "fise_label_40x25_zpl",
                "type": "qweb",
                "key": "deltatech_product_labels.fise_label_40x25_zpl",
                "arch": ZPL_TEMPLATE,
            }
        )
        env["ir.model.data"].create(
            {
                "module": "deltatech_product_labels",
                "name": "fise_label_40x25_zpl",
                "model": "ir.ui.view",
                "res_id": view.id,
            }
        )
        cls.zpl_report = env["ir.actions.report"].create(
            {
                "name": "Etichete 40x25 ZPL (203 DPI)",
                "model": "product.product.label",
                "report_type": "qweb-text",
                "report_name": "deltatech_product_labels.fise_label_40x25_zpl",
                "zpl_label_width": 40,
                "zpl_label_height": 25,
                "zpl_dpmm": "8",
            }
        )
        env.flush_all()

        cls.act_product = env.ref("stock.product_template_action_product").id
        cls.act_sale = env.ref("sale.action_orders").id
        cls.act_picking = env.ref("stock.action_picking_tree_all").id
        cls.act_lot = env.ref("stock.action_production_lot_form").id
        cls.act_report = env.ref("base.ir_action_report").id
        cls.act_param = env.ref("base.ir_config_list_action").id
        env["ir.config_parameter"].set_param("terrabit_labels.override_print_button", "True")
        cls.param = env["ir.config_parameter"].search([("key", "=", "terrabit_labels.override_print_button")])

    def _wizard(self, model, records, **vals):
        label = self.env["product.product.label"].with_context(active_model=model, active_ids=records.ids)
        return label.create(vals)

    def _form(self, action, record, name, **extra):
        shot = {
            "url": f"action={action}&id={record.id}&model={record._name}&view_type=form",
            "name": name,
            "wait": ".o_form_view",
        }
        shot.update(extra)
        return shot

    def _cog_item(self, action, record, item, name, **extra):
        """Deschide asistentul din meniul ⚙ al unui document (rubrica Acțiuni sau Tipărire)"""
        click = (
            "(async () => {"
            "const find = (text) => [...document.querySelectorAll('.o-dropdown-item, .dropdown-item, "
            ".o-dropdown--menu .dropdown-toggle')].find(e => e.textContent.trim() === text);"
            f"let item = find({item!r});"
            "if (!item) {"
            "const print = find('Tipăriți'); if (print) { print.click(); }"
            "await new Promise(r => setTimeout(r, 800));"
            f"item = find({item!r});"
            "}"
            "if (item) { item.click(); }"
            "})()"
        )
        extra.setdefault("highlight", ".modal button[name='print_labels']")
        return self._form(
            action,
            record,
            name,
            click_btn=".o_cp_action_menus button.dropdown-toggle",
            wait_after=".o-dropdown--menu",
            eval=click + ".then(() => new Promise(r => setTimeout(r, 2500)))"
            ".then(() => document.activeElement && document.activeElement.blur())",
            eval_wait=1500,
            **extra,
        )

    def _show_optional(self, column):
        """JS care afișează o coloană opțională a listei de etichete (ex. „Lot")"""
        return (
            "(async () => {"
            "const toggle = document.querySelector('.modal .o_optional_columns_dropdown_toggle');"
            "if (!toggle) { return; } toggle.click();"
            "await new Promise(r => setTimeout(r, 500));"
            "const item = [...document.querySelectorAll('.o-dropdown--menu .o-dropdown-item, "
            ".o-dropdown--menu label')]"
            f".find(e => e.textContent.trim() === {column!r});"
            "const box = item && (item.querySelector('input') || item);"
            "if (box && !box.checked) { box.click(); }"
            "await new Promise(r => setTimeout(r, 500));"
            "document.querySelector('.modal .modal-title').click();"
            "})()"
        )

    def _labelary_png(self, wizard):
        """Previzualizarea ZPL (PDF de la Labelary) ca imagine PNG, sau None fără rețea"""
        try:
            wizard.action_preview_zpl()
        except UserError as e:
            _logger.warning("Previzualizarea ZPL indisponibilă: %s", e)
            return None
        pdf = wizard.preview_pdf
        if not pdf.startswith(b"%PDF"):
            pdf = base64.b64decode(pdf)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "preview.pdf")
            with open(path, "wb") as f:
                f.write(pdf)
            subprocess.run(["pdftoppm", "-png", "-r", "200", path, os.path.join(tmp, "page")], check=True)
            pages = sorted(name for name in os.listdir(tmp) if name.endswith(".png"))
            images = []
            for page in pages:
                with open(os.path.join(tmp, page), "rb") as f:
                    images.append(base64.b64encode(f.read()).decode())
        cells = "".join(
            f'<img src="data:image/png;base64,{img}" style="border:1px solid #bbb;margin:8px"/>' for img in images
        )
        return f'<html><body style="background:#fff;margin:0;padding:8px">{cells}</body></html>'

    def test_capture_fise(self):
        wizard = self._wizard("product.template", self.cana | self.termos)
        wizard.label_lines.filtered(lambda line: line.product_id == self.cana.product_variant_id).quantity = 3
        wizard.label_lines.filtered(lambda line: line.product_id == self.termos.product_variant_id).quantity = 2
        single = self._wizard("product.template", self.cana | self.termos)
        # chenar punctat pe marginea etichetei, ca în captură să se vadă dimensiunea ei
        outline = "document.querySelectorAll('.dt_label').forEach(e => e.style.outline = '1px dashed #999')"
        report_a4 = "deltatech_product_labels.product_product_label_a4_3x8"
        report_40 = "deltatech_product_labels.product_product_label_40x25"
        report_100 = "deltatech_product_labels.product_product_label_100x50"
        shots = [
            self._form(
                self.act_product,
                self.cana,
                "01_produs_meniu_etichete.png",
                click_btn=".o_cp_action_menus button.dropdown-toggle",
                wait_after=".o-dropdown--menu",
                highlight=".o-dropdown--menu .o-dropdown-item:text-is('Tipărire Etichete')",
            ),
            self._cog_item(self.act_product, self.cana, "Tipărire Etichete", "02_asistent_din_produs.png"),
            self.report_shot(report_a4, wizard, "03_eticheta_a4_3x8.png", eval=outline),
            self.report_shot(
                report_40, single, "04_eticheta_40x25.png", eval=outline + "; document.body.style.zoom = 2"
            ),
            self.report_shot(report_100, single, "05_eticheta_100x50.png", eval=outline),
            self._cog_item(self.act_sale, self.sale, "Etichete produs", "06_asistent_din_comanda.png"),
            self._cog_item(
                self.act_picking,
                self.receipt,
                "Etichete produs",
                "07_asistent_din_receptie.png",
                highlight=[".modal div[name='auto_generate_lots']", ".modal button[name='print_labels']"],
            ),
        ]
        self.capture_screenshots(shots, hide_systray=True)

        # recepția: „Generează loturile" completează numele loturilor înainte de tipărire
        receipt_wizard = self._wizard("stock.picking", self.receipt)
        receipt_wizard.with_context(active_model="stock.picking", active_ids=self.receipt.ids).generate_lots()
        self.env.flush_all()
        shots = [
            self.report_shot(report_a4, receipt_wizard, "08_eticheta_lot_receptie.png", eval=outline),
        ]
        open_lot_column = self._show_optional("Lot")
        only_lots = self._cog_item(
            self.act_product,
            self.ulei,
            "Tipărire Etichete",
            "09_asistent_doar_loturi.png",
            highlight=".modal div[name='print_only_lots']",
        )
        only_lots["eval"] += (
            ".then(() => { const box = document.querySelector(\".modal div[name='print_only_lots'] input\");"
            " if (box) { box.click(); } })"
            ".then(() => new Promise(r => setTimeout(r, 2000)))"
            f".then(() => {open_lot_column})"
        )
        only_lots["eval_wait"] = 2500
        shots.append(only_lots)
        from_lot = self._cog_item(self.act_lot, self.lots[0], "Etichete produs", "10_asistent_din_lot.png")
        from_lot["eval"] += f".then(() => {open_lot_column})"
        from_lot["eval_wait"] = 2500
        shots.append(from_lot)
        shots.append(
            {
                "path": f"/odoo/action-{self.act_report}/{self.zpl_report.id}?debug=1",
                "name": "11_raport_zpl_dimensiuni.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='zpl_label_width']", "div[name='zpl_label_height']", "div[name='zpl_dpmm']"],
            }
        )
        self.capture_screenshots(shots, hide_systray=True)

        # macheta propusă = ultima tipărită de utilizator: după o tipărire ZPL, asistentul o propune
        zpl_wizard = self._wizard("product.template", self.cana | self.ulei, layout_id=self.zpl_report.id).with_user(
            self.env.ref("base.user_admin")
        )
        zpl_wizard.label_lines.filtered(lambda line: line.product_id == self.ulei.product_variant_id).lot = "UL-2609-01"
        zpl_wizard.print_labels()
        self.env.flush_all()
        shots = [
            self._cog_item(
                self.act_product,
                self.cana,
                "Etichete produs",
                "12_asistent_zpl_previzualizare.png",
                highlight=[".modal div[name='layout_id']", ".modal button[name='action_preview_zpl']"],
            )
        ]
        preview = self._labelary_png(zpl_wizard)
        if preview:
            shots.append({"html": preview, "name": "13_previzualizare_zpl.png", "full": True})
        self.capture_screenshots(shots, hide_systray=True)

        # parametrul care întoarce butonul „Tipărire Etichete" la asistentul standard Odoo
        self.param.value = "False"
        self.env.flush_all()
        shots = []
        shots.append(
            {
                "path": f"/odoo/action-{self.act_param}/{self.param.id}?debug=1",
                "name": "14_parametru_buton_etichete.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='key']", "div[name='value']"],
            }
        )
        self.capture_screenshots(shots, hide_systray=True)
