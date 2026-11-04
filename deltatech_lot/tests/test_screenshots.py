# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Generarea loturilor la recepție și locația lotului" —
# generate în timpul testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: produs urmărit pe loturi, recepție de la furnizor validată fără numere de lot
# (modulul le generează), apoi lista și fișa loturilor cu locația lor și căutarea după locație.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_lot,deltatech_doc_screenshots \
#       --test-tags=/deltatech_lot:TestLotScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# bulina numerotată a evidențierii stă peste colțul celulei: celulele nu o mai taie
CELLS_VISIBLE_JS = (
    "() => document.querySelectorAll('.o_data_row td, .modal .o_list_renderer')"
    ".forEach((el) => (el.style.overflow = 'visible'))"
)

# acțiunea standard grupează loturile după locație: scoatem gruparea, ca lista să fie plată
UNGROUP_JS = """
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const remove = document.querySelector(".o_searchview_facet .o_facet_remove");
    if (remove) {
        remove.click();
        await sleep(1500);
    }
"""

# caută în lista loturilor după Locație: scrie textul, apoi alege „Caută Locație pentru: ..."
SEARCH_LOCATION_JS = """
    const input = document.querySelector(".o_searchview_input");
    input.focus();
    input.value = "%s";
    input.dispatchEvent(new Event("input", {bubbles: true}));
    let item = null;
    for (let i = 0; i < 30 && !item; i++) {
        await sleep(200);
        item = [...document.querySelectorAll(".o_searchview_autocomplete .o-dropdown-item")].find((li) =>
            /%s/.test(li.textContent)
        );
    }
    if (item) {
        item.click();
    }
    await sleep(1500);
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestLotScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_lot"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write(
            {
                "group_ids": [
                    Command.link(env.ref("stock.group_production_lot").id),
                    Command.link(env.ref("stock.group_stock_multi_locations").id),
                ]
            }
        )
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
        cls.warehouse.name = "Depozit central"
        stock = cls.warehouse.lot_stock_id
        Location = env["stock.location"]
        cls.loc_a1 = Location.create({"name": "Raft A1", "usage": "internal", "location_id": stock.id})
        cls.loc_b2 = Location.create({"name": "Raft B2", "usage": "internal", "location_id": stock.id})
        cls.loc_c3 = Location.create({"name": "Raft C3", "usage": "internal", "location_id": stock.id})
        cls.supplier = env["res.partner"].create({"name": "Vopsele Demo SRL"})
        cls.product = env["product.product"].create(
            {
                "name": "Vopsea lavabilă albă 15 L",
                "default_code": "VOP-ALB15",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        cls.product.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Vopsea lavabilă albă 15 L", "en_US": "White emulsion paint 15 L"}
        )
        # un lot mai vechi, împărțit pe două rafturi: locația lotului rămâne goală
        cls.old_lot = env["stock.lot"].create({"name": "VOP-2509-07", "product_id": cls.product.id})
        Quant = env["stock.quant"]
        Quant._update_available_quantity(cls.product, cls.loc_a1, 4, lot_id=cls.old_lot)
        Quant._update_available_quantity(cls.product, cls.loc_c3, 6, lot_id=cls.old_lot)

        # recepția de la furnizor: 12 bucăți pe Raft A1 și 8 pe Raft B2, fără numere de lot
        picking_type = cls.warehouse.in_type_id
        cls.receipt = env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": cls.supplier.id,
                "origin": "P00042",
                "location_id": env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": stock.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 20,
                            "location_id": env.ref("stock.stock_location_suppliers").id,
                            "location_dest_id": stock.id,
                        }
                    )
                ],
            }
        )
        # numele fix: secvența recepțiilor nu revine la rollback, iar capturile trebuie să fie stabile
        cls.receipt.name = "WH/IN/00001"
        cls.receipt.action_confirm()
        move = cls.receipt.move_ids
        line = move.move_line_ids[:1]
        line.write({"quantity": 12, "location_dest_id": cls.loc_a1.id, "lot_name": False})
        (move.move_line_ids - line).unlink()
        env["stock.move.line"].create(
            {
                "move_id": move.id,
                "picking_id": cls.receipt.id,
                "product_id": cls.product.id,
                "quantity": 8,
                "location_id": move.location_id.id,
                "location_dest_id": cls.loc_b2.id,
            }
        )
        move.picked = True

    def _shots_before(self):
        product_form = f"id={self.product.product_tmpl_id.id}&model=product.template&view_type=form"
        receipt_form = f"id={self.receipt.id}&model=stock.picking&view_type=form"
        return [
            # 1. produsul urmărit pe loturi (în 20 câmpul din formular e store_by)
            {
                "url": product_form,
                "name": "01_produs_urmarire_loturi.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='store_by']"],
            },
            # 2. recepția gata de validare
            {
                "url": receipt_form,
                "name": "02_receptie_de_validat.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='button_validate']"],
            },
            # 3. operațiile detaliate: rânduri pe rafturi, fără număr de lot
            {
                "url": receipt_form,
                "name": "03_operatii_detaliate_fara_lot.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='action_show_details']",
                "wait_after": ".modal .o_list_view",
                "eval": CELLS_VISIBLE_JS,
                "highlight": [".modal .o_data_row td[name='lot_name']"],
            },
        ]

    def _shots_after(self):
        receipt_form = f"id={self.receipt.id}&model=stock.picking&view_type=form"
        lot_list = f"action={self.env.ref('stock.action_production_lot_form').id}&view_type=list"
        new_lot = self.receipt.move_line_ids.lot_id.sorted("name")[:1]
        return [
            # 4. după validare: loturile generate pe fiecare rând
            {
                "url": receipt_form,
                "name": "04_loturi_generate_receptie.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='action_show_details']",
                "wait_after": ".modal .o_list_view",
                "eval": CELLS_VISIBLE_JS,
                "highlight": [".modal .o_data_row td[name='lot_id']"],
            },
            # 5. lista loturilor, cu coloana Locație
            {
                "url": lot_list,
                "name": "05_lista_loturi_locatie.png",
                "wait": ".o_list_view",
                "eval": "async () => {" + UNGROUP_JS + CELLS_VISIBLE_JS[6:] + "}",
                "eval_wait": 1500,
                "highlight": [".o_data_row td[name='location_id']"],
            },
            # 6. fișa lotului, cu câmpul Locație
            {
                "url": f"id={new_lot.id}&model=stock.lot&view_type=form",
                "name": "06_fisa_lot_locatie.png",
                "wait": ".o_form_view",
                # câmpul adăugat de modul (al doilea); primul e cel standard, din grupul Inventar
                "highlight": ["div[name='location_id'] >> nth=1"],
            },
            # 7. căutarea loturilor după locație
            {
                "url": lot_list,
                "name": "07_cautare_loturi_locatie.png",
                "wait": ".o_list_view",
                "eval": {
                    "ro_RO": "async () => {" + UNGROUP_JS + SEARCH_LOCATION_JS % ("Raft A1", "Loca") + "}",
                    "en_US": "async () => {" + UNGROUP_JS + SEARCH_LOCATION_JS % ("Raft A1", "Location") + "}",
                },
                "eval_wait": 1500,
                "highlight": [".o_searchview_facet"],
            },
        ]

    def _capture(self, **kwargs):
        # descrierea rândului de recepție urmează limba furnizorului: aceeași cu interfața,
        # ca sub produs să nu apară încă o dată numele în cealaltă limbă
        self.supplier.lang = kwargs.get("lang", "ro_RO")
        # numerele de lot încep de la 1 în ambele limbi
        self.env.ref("stock.sequence_production_lots").number_next_actual = 1
        self.capture_screenshots(self._shots_before(), viewport=(1600, 900), hide_systray=True, **kwargs)
        self.receipt.button_validate()
        self.assertEqual(self.receipt.state, "done")
        lots = self.receipt.move_line_ids.lot_id
        self.assertEqual(len(lots), 2, "câte un lot generat pe fiecare rând")
        self.assertEqual(lots.location_id, self.loc_a1 | self.loc_b2)
        self.assertFalse(self.old_lot.location_id, "lotul pe două rafturi nu are o singură locație")
        self.env.flush_all()
        self.capture_screenshots(self._shots_after(), viewport=(1600, 900), hide_systray=True, **kwargs)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
