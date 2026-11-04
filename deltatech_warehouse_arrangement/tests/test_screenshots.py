# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Amplasarea în depozit" — generate în timpul testelor,
# în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: ierarhia Hală → Zonă → Raft → Secțiune → Poliță, eticheta poliței, locațiile
# implicite pe produs, recepția unui lot în locația principală (lotul preia locațiile
# produsului), stocul pe polițe și mutarea lotului pe altă poliță cu asistentul de scanare.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_warehouse_arrangement,deltatech_doc_screenshots \
#       --test-tags=/deltatech_warehouse_arrangement:TestWarehouseArrangementScreenshots --stop-after-init
import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image, ImageDraw
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Group, Rect

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


def _barcode_png(barcode_type, value, width=600, height=100, **kwargs):
    """Codul de bare ca PNG, desenat cu PIL din dreptunghiurile desenului reportlab.

    Folosit doar când serverul de test nu are backend-ul renderPM al reportlab (rlPyCairo):
    altfel eticheta poliței ar ieși fără codul de bare.
    """
    drawing = createBarcodeDrawing(barcode_type, value=value, width=width, height=height, quiet=True)
    rects = []

    def walk(node, tf):
        for child in getattr(node, "contents", []):
            if isinstance(child, Group):
                a, b, c, d, e, f = child.transform
                A, B, C, D, E, F = tf
                walk(
                    child,
                    (A * a + C * b, B * a + D * b, A * c + C * d, B * c + D * d, A * e + C * f + E, B * e + D * f + F),
                )
            elif isinstance(child, Rect) and child.fillColor is not None:
                rects.append((tf, child))

    walk(drawing.expandUserNodes(), tuple(drawing.transform))
    img = Image.new("RGB", (int(width), int(height)), "white")
    draw = ImageDraw.Draw(img)
    for (sx, _b, _c, sy, ex, ey), rect in rects:
        color = tuple(int(v * 255) for v in rect.fillColor.rgb())
        if color == (255, 255, 255):
            continue
        x0, x1 = rect.x * sx + ex, (rect.x + rect.width) * sx + ex
        y0, y1 = height - (rect.y + rect.height) * sy - ey, height - rect.y * sy - ey
        draw.rectangle((x0, y0, x1, y1), fill=color)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# insignele numerotate ale evidențierilor ies din celula tabelului: celulele nu le mai taie
SHOW_CELL_BADGES_JS = (
    "() => document.head.insertAdjacentHTML('beforeend', "
    "'<style>td.o_data_cell, .modal .o_list_renderer, .modal .table-responsive"
    "{overflow:visible!important}</style>')"
)
LOCATION_FIELDS = ("loc_storehouse_id", "loc_zone_id", "loc_shelf_id", "loc_section_id", "loc_rack_id")
LOCATIONS_TAB = {"ro_RO": "Locație", "en_US": "Locations"}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestWarehouseArrangementScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_warehouse_arrangement"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        admin = env.ref("base.user_admin")
        # loturi și locații multiple vizibile (coloana Lot și raportul Locații din Inventar)
        admin.write(
            {
                "group_ids": [
                    Command.link(env.ref("stock.group_production_lot").id),
                    Command.link(env.ref("stock.group_stock_multi_locations").id),
                    Command.link(env.ref("deltatech_warehouse_arrangement.group_locations_manager").id),
                ]
            }
        )
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
        # numele depozitului apare în tipul de operație („RO Company: Recepții")
        cls.warehouse.name = "RO Company"
        cls.stock_location = cls.warehouse.lot_stock_id
        supplier = env.ref("stock.stock_location_suppliers")

        cls.storehouse = env["warehouse.location.storehouse"].create(
            {"name": "H1", "location_id": cls.stock_location.id}
        )
        cls.zone = env["warehouse.location.zone"].create({"name": "Z1", "storehouse_id": cls.storehouse.id})
        cls.shelf = env["warehouse.location.shelf"].create({"name": "R01", "zone_id": cls.zone.id})
        cls.section = env["warehouse.location.section"].create({"name": "S1", "shelf_id": cls.shelf.id})
        cls.rack = env["warehouse.location.rack"].create(
            {"name": "P01", "section_id": cls.section.id, "barcode": "H1-Z1-R01-S1-P01"}
        )
        cls.rack2 = env["warehouse.location.rack"].create(
            {"name": "P02", "section_id": cls.section.id, "barcode": "H1-Z1-R01-S1-P02"}
        )

        cls.product = env["product.product"].create(
            {
                "name": "Cablu cupru 2,5 mm²",
                "default_code": "CBL-CU25",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
                "loc_storehouse_id": cls.storehouse.id,
                "loc_zone_id": cls.zone.id,
                "loc_shelf_id": cls.shelf.id,
                "loc_section_id": cls.section.id,
                "loc_rack_id": cls.rack.id,
            }
        )
        cls.product.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Cablu cupru 2,5 mm²", "en_US": "Copper cable 2.5 mm²"}
        )

        # recepția a două loturi direct în locația principală a halei (WH/Stoc)
        cls.picking = env["stock.picking"].create(
            {
                "picking_type_id": cls.warehouse.in_type_id.id,
                "location_id": supplier.id,
                "location_dest_id": cls.stock_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 300,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": supplier.id,
                            "location_dest_id": cls.stock_location.id,
                        }
                    )
                ],
            }
        )
        cls.picking.action_confirm()
        move = cls.picking.move_ids
        move.move_line_ids.unlink()
        for lot_name, qty in (("LOT-2026-001", 100), ("LOT-2026-002", 200)):
            env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "picking_id": cls.picking.id,
                    "product_id": cls.product.id,
                    "lot_name": lot_name,
                    "quantity": qty,
                    "product_uom_id": cls.product.uom_id.id,
                    "location_id": supplier.id,
                    "location_dest_id": cls.stock_location.id,
                }
            )
        move.picked = True
        cls.picking.button_validate()
        cls.lot1 = env["stock.lot"].search([("name", "=", "LOT-2026-001"), ("product_id", "=", cls.product.id)])
        cls.lot2 = env["stock.lot"].search([("name", "=", "LOT-2026-002"), ("product_id", "=", cls.product.id)])
        env.flush_all()

    def _form(self, record, action=None):
        url = f"model={record._name}&id={record.id}&view_type=form"
        if action:
            url = f"action={action}&{url}"
        return f"{url}&menu_id={self.env.ref('stock.menu_stock_root').id}"

    def _shots_setup(self):
        mod = "deltatech_warehouse_arrangement"
        return [
            # 1. hala, legată de locația de stoc Odoo
            {
                "url": self._form(self.storehouse, f"{mod}.action_storehouse"),
                "name": "01_hala_formular.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='name']", "div[name='location_id']", "div[name='full_name']"],
            },
            # 2. lista polițelor, cu ierarhia lor
            {
                "url": f"action={mod}.action_rack&view_type=list",
                "name": "02_lista_polite.png",
                "wait": ".o_list_view",
            },
            # 3. polița: numele complet al ierarhiei și codul de bare
            {
                "url": self._form(self.rack, f"{mod}.action_rack"),
                "name": "03_polita_formular.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='section_id']", "div[name='full_name']", "div[name='barcode']"],
            },
            # 4. eticheta poliței (raportul tipăribil)
            self.report_shot(f"{mod}.report_rack", self.rack, "04_eticheta_polita.png", wait=".page"),
            # 5. locațiile implicite pe produs
            {
                "url": self._form(self.product.product_tmpl_id),
                "name": "05_produs_locatii.png",
                "wait": ".o_form_view",
                "click_tab": LOCATIONS_TAB,
                "highlight": [f"div[name='{name}']" for name in LOCATION_FIELDS],
            },
        ]

    def _shots_flow(self):
        return [
            # 6. recepția validată în WH/Stoc, cu cele două loturi
            {
                "url": self._form(self.picking, "stock.action_picking_tree_all"),
                "name": "06_receptie_loturi.png",
                "wait": ".o_form_view",
                # Detalii: liniile recepției, cu loturile și locația de destinație
                "click_btn": "button[name='action_show_details']",
                "wait_after": ".modal .o_list_view",
                "settle": 2000,
                "eval": SHOW_CELL_BADGES_JS,
                "highlight": [".modal td[name^='lot']", ".modal td[name='location_dest_id']"],
            },
            # 7. lotul a preluat locațiile produsului la recepție
            {
                "url": self._form(self.lot1, "stock.action_production_lot_form"),
                "name": "07_lot_locatii_receptie.png",
                "wait": ".o_form_view",
                "click_tab": LOCATIONS_TAB,
                "highlight": [f"div[name='{name}']" for name in LOCATION_FIELDS],
            },
        ]

    def _shots_wizard(self, wizard):
        mod = "deltatech_warehouse_arrangement"
        return [
            # 8. asistentul de schimbare a locației: lotul și polița nouă, scanate
            {
                "url": self._form(wizard, f"{mod}.action_lot_change_location"),
                "name": "08_schimbare_locatie_lot.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='lot_id']", "div[name='rack_id']"],
            },
        ]

    def _shots_after(self):
        return [
            # 9. lotul mutat pe polița P02
            {
                "url": self._form(self.lot2, "stock.action_production_lot_form"),
                "name": "09_lot_polita_noua.png",
                "wait": ".o_form_view",
                "click_tab": LOCATIONS_TAB,
                "highlight": ["div[name='loc_rack_id']"],
            },
            # 10. stocul pe polițe, grupat pe poliță (Inventar → Raportare → Locații)
            {
                "url": "action=stock.action_view_quants&view_type=list"
                f"&menu_id={self.env.ref('stock.menu_stock_root').id}",
                "name": "10_stoc_pe_polite.png",
                "wait": ".o_list_view",
                "eval": """async () => {
                    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
                    const input = document.querySelector('.o_searchview_input');
                    input.value = 'CBL-CU25';
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    await sleep(500);
                    input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
                    await sleep(1500);
                    // coloanele standard nerelevante (produsul e filtrat, rezervat, butoanele)
                    // se scot, ca amplasarea să încapă lizibil în lățimea capturii
                    const table = document.querySelector('.o_list_table');
                    const heads = [...table.querySelectorAll('thead th')];
                    const drop = heads
                        .map((th, i) => [th, i])
                        .filter(([th]) => ['product_id', 'reserved_quantity'].includes(th.dataset.name)
                            || (!th.dataset.name && !th.classList.contains('o_list_record_selector')
                                && !th.classList.contains('o_list_actions_header')))
                        .map(([, i]) => i)
                        .reverse();
                    table.querySelectorAll('tr').forEach((tr) => {
                        drop.forEach((i) => tr.children[i] && tr.children[i].remove());
                    });
                    table.querySelectorAll('colgroup col').forEach((col, i) => drop.includes(i) && col.remove());
                    table.style.tableLayout = 'auto';
                    document.head.insertAdjacentHTML(
                        'beforeend', '<style>td.o_data_cell{overflow:visible!important}</style>'
                    );
                }""",
                "eval_wait": 1500,
                "highlight": ["td[name='lot_id']", "td[name='loc_rack_id']"],
            },
        ]

    def _capture(self, **kwargs):
        report_model = type(self.env["ir.actions.report"])
        original = report_model.barcode

        def barcode(report, barcode_type, value, **kw):
            try:
                return original(report, barcode_type, value, **kw)
            except Exception:  # noqa: BLE001 - fără renderPM (rlPyCairo) în mediul de test
                return _barcode_png(barcode_type, value, int(kw.get("width", 600)), int(kw.get("height", 100)))

        with patch.object(report_model, "barcode", barcode):
            self._capture_all(**kwargs)

    def _capture_all(self, **kwargs):
        options = dict(viewport=(1920, 1000), hide_systray=True, **kwargs)
        # starea inițială: ambele loturi pe P01
        self.lot2.write({"loc_rack_id": self.rack.id})
        self.assertEqual(self.lot1.loc_rack_id, self.rack)
        self.capture_screenshots(self._shots_setup() + self._shots_flow(), **options)
        # asistentul, ca după scanarea lotului și a poliței noi
        admin = self.env.ref("base.user_admin")
        wizard = self.env["lot.change.location"].with_user(admin).create({})
        wizard.on_barcode_scanned("LOT-2026-002")
        wizard.on_barcode_scanned("H1-Z1-R01-S1-P02")
        self.assertEqual(wizard.rack_id, self.rack2)
        self.env.flush_all()
        self.capture_screenshots(self._shots_wizard(wizard), **options)
        # în Odoo 19 asistentul deschis din meniu nu are butoane (footer-ul apare doar în dialog):
        # polița nouă se alege direct pe lot, în tabul Locație
        self.lot2.write({"loc_rack_id": self.rack2.id})
        self.env.flush_all()
        self.capture_screenshots(self._shots_after()[:1], **options)
        self.capture_screenshots(self._shots_after()[1:], **options)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
