# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest import mock

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from ..models.warehouse_location import get_location_type


@tagged("post_install", "-at_install")
class TestWarehouseArrangement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        cls.storehouse = cls.env["warehouse.location.storehouse"].create(
            {"name": "SH1", "location_id": cls.stock_location.id}
        )
        cls.zone = cls.env["warehouse.location.zone"].create({"name": "Z1", "storehouse_id": cls.storehouse.id})
        cls.shelf = cls.env["warehouse.location.shelf"].create({"name": "SF1", "zone_id": cls.zone.id})
        cls.section = cls.env["warehouse.location.section"].create({"name": "SC1", "shelf_id": cls.shelf.id})
        cls.rack = cls.env["warehouse.location.rack"].create(
            {"name": "R1", "section_id": cls.section.id, "barcode": "RACK-TEST-001"}
        )
        cls.rack2 = cls.env["warehouse.location.rack"].create(
            {"name": "R2", "section_id": cls.section.id, "barcode": "RACK-TEST-002"}
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Arrangement Product",
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
        cls.product_no_loc = cls.env["product.product"].create(
            {"name": "Arrangement Product No Loc", "type": "consu", "is_storable": True, "tracking": "lot"}
        )

    def _loc_vals(self, record):
        return (
            record.loc_storehouse_id,
            record.loc_zone_id,
            record.loc_shelf_id,
            record.loc_section_id,
            record.loc_rack_id,
        )

    def _full_location(self):
        return (self.storehouse, self.zone, self.shelf, self.section, self.rack)

    def _empty_location(self):
        model = self.env["warehouse.location.storehouse"]
        return (
            model,
            self.env["warehouse.location.zone"],
            self.env["warehouse.location.shelf"],
            self.env["warehouse.location.section"],
            self.env["warehouse.location.rack"],
        )

    def _move(self, product, lot, qty, src, dest):
        move = self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "location_id": src.id,
                "location_dest_id": dest.id,
            }
        )
        move._action_confirm()
        move.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "product_id": product.id,
                "lot_id": lot.id,
                "quantity": qty,
                "product_uom_id": product.uom_id.id,
                "location_id": src.id,
                "location_dest_id": dest.id,
            }
        )
        move.picked = True
        move._action_done()
        self.assertEqual(move.state, "done")
        return move

    # ------------------------------------------------------------------ helpers / names
    def test_get_location_type(self):
        self.assertEqual(get_location_type("warehouse.location.rack"), "Rack: ")
        self.assertEqual(get_location_type("warehouse.location.section"), "Section: ")
        self.assertEqual(get_location_type("warehouse.location.shelf"), "Shelf: ")
        self.assertEqual(get_location_type("warehouse.location.zone"), "Zone: ")
        self.assertEqual(get_location_type("warehouse.location.storehouse"), "Storehouse: ")
        self.assertEqual(get_location_type("res.partner"), "")

    def test_full_and_display_names(self):
        prefix = "Storehouse: SH1/Zone: Z1"
        self.assertEqual(self.zone.full_name, prefix)
        self.assertEqual(self.zone.display_name, f"Z1 ({prefix})")
        self.assertEqual(self.shelf.full_name, prefix + "/Shelf: SF1")
        self.assertEqual(self.shelf.display_name, f"SF1 ({prefix}/Shelf: SF1)")
        self.assertEqual(self.section.full_name, prefix + "/Shelf: SF1/Section: SC1")
        self.assertEqual(self.section.display_name, f"SC1 ({prefix}/Shelf: SF1/Section: SC1)")
        self.assertEqual(self.rack.full_name, prefix + "/Shelf: SF1/Section: SC1/Rack: R1")
        self.assertEqual(self.rack.display_name, f"R1 ({prefix}/Shelf: SF1/Section: SC1/Rack: R1)")

    def test_storehouse_names(self):
        location_name = self.stock_location.name
        self.assertEqual(self.storehouse.full_name, f"{location_name}/SH1")
        self.assertEqual(self.storehouse.display_name, f"SH1 ({location_name}/SH1)")
        storehouse = self.env["warehouse.location.storehouse"].create({"name": "SH2"})
        self.assertEqual(storehouse.full_name, "SH2")
        self.assertEqual(storehouse.display_name, "SH2 (SH2)")

    def test_names_with_missing_parents(self):
        # the parents are not required: a missing level is skipped instead of raising TypeError
        zone = self.env["warehouse.location.zone"].create({"name": "Z-ORPHAN"})
        self.assertEqual(zone.full_name, "Zone: Z-ORPHAN")
        self.assertEqual(zone.display_name, "Z-ORPHAN (Zone: Z-ORPHAN)")
        shelf = self.env["warehouse.location.shelf"].create({"name": "SF-ORPHAN"})
        self.assertEqual(shelf.full_name, "Shelf: SF-ORPHAN")
        section = self.env["warehouse.location.section"].create({"name": "SC-ORPHAN", "shelf_id": shelf.id})
        self.assertEqual(section.full_name, "Shelf: SF-ORPHAN/Section: SC-ORPHAN")
        rack = self.env["warehouse.location.rack"].create({"name": "R-ORPHAN"})
        self.assertEqual(rack.display_name, "R-ORPHAN (Rack: R-ORPHAN)")

    # ------------------------------------------------------------------ stock.lot create
    def test_lot_create_takes_product_locations(self):
        lot = self.env["stock.lot"].create({"name": "LOT-A", "product_id": self.product.id})
        self.assertEqual(self._loc_vals(lot), self._full_location())

    def test_lot_create_with_default_product_context(self):
        lot = self.env["stock.lot"].with_context(default_product_id=self.product.id).create({"name": "LOT-CTX"})
        self.assertEqual(lot.product_id, self.product)
        self.assertEqual(self._loc_vals(lot), self._full_location())

    def test_lot_create_keeps_explicit_locations(self):
        lot = self.env["stock.lot"].create(
            {"name": "LOT-EXPLICIT", "product_id": self.product.id, "loc_rack_id": self.rack2.id}
        )
        self.assertEqual(lot.loc_rack_id, self.rack2, "An explicit lot location must not be replaced by the product's")
        self.assertEqual(lot.loc_shelf_id, self.shelf, "Omitted locations still default from the product")

    def test_lot_create_batch_uses_each_product(self):
        lots = self.env["stock.lot"].create(
            [
                {"name": "LOT-B1", "product_id": self.product.id},
                {"name": "LOT-B2", "product_id": self.product_no_loc.id},
            ]
        )
        self.assertEqual(self._loc_vals(lots[0]), self._full_location())
        self.assertEqual(self._loc_vals(lots[1]), self._empty_location())

    def test_lot_create_without_product(self):
        # no product in vals nor in context: no UnboundLocalError, the standard NOT NULL check applies
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.env["stock.lot"].create({"name": "LOT-NOPROD"})

    def test_lot_create_product_without_locations(self):
        lot = self.env["stock.lot"].create({"name": "LOT-NOLOC", "product_id": self.product_no_loc.id})
        self.assertEqual(self._loc_vals(lot), self._empty_location())

    # ------------------------------------------------------------------ check_if_depleted
    def test_check_if_depleted(self):
        lot = self.env["stock.lot"].create({"name": "LOT-DEP", "product_id": self.product.id})
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 5.0, lot_id=lot)
        lot.check_if_depleted(self.stock_location)
        self.assertEqual(lot.loc_rack_id, self.rack, "Lot still has stock, location must be kept")
        quant = lot.quant_ids.filtered(lambda q: q.location_id == self.stock_location)
        self.assertEqual(quant.loc_storehouse_id, self.storehouse)
        self.assertEqual(quant.loc_rack_id, self.rack)
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, -5.0, lot_id=lot)
        lot.check_if_depleted(self.stock_location)
        self.assertEqual(self._loc_vals(lot), self._empty_location())

    def test_check_if_depleted_storehouse_without_location(self):
        storehouse = self.env["warehouse.location.storehouse"].create({"name": "SH-NOLOC"})
        lot = self.env["stock.lot"].create({"name": "LOT-NSH", "product_id": self.product_no_loc.id})
        lot.loc_storehouse_id = storehouse
        lot.check_if_depleted(self.stock_location)
        self.assertEqual(lot.loc_storehouse_id, storehouse)

    # ------------------------------------------------------------------ stock.move.line _action_done
    def test_move_in_and_out_master_location(self):
        lot = self.env["stock.lot"].create({"name": "LOT-MOVE", "product_id": self.product_no_loc.id})
        self.assertFalse(lot.loc_storehouse_id)
        self.product_no_loc.product_tmpl_id.write(
            {
                "loc_storehouse_id": self.storehouse.id,
                "loc_zone_id": self.zone.id,
                "loc_shelf_id": self.shelf.id,
                "loc_section_id": self.section.id,
                "loc_rack_id": self.rack2.id,
            }
        )
        # receipt into the master location sets the lot location from product
        self._move(self.product_no_loc, lot, 10, self.supplier_location, self.stock_location)
        self.assertEqual(self._loc_vals(lot), (self.storehouse, self.zone, self.shelf, self.section, self.rack2))
        # partial delivery: lot keeps its location
        self._move(self.product_no_loc, lot, 4, self.stock_location, self.customer_location)
        self.assertEqual(lot.loc_rack_id, self.rack2)
        # full delivery: location removed
        self._move(self.product_no_loc, lot, 6, self.stock_location, self.customer_location)
        self.assertEqual(self._loc_vals(lot), self._empty_location())

    def test_move_outside_master_location(self):
        other_location = self.env["stock.location"].create(
            {"name": "Other Internal", "usage": "internal", "location_id": self.warehouse.view_location_id.id}
        )
        lot = self.env["stock.lot"].create({"name": "LOT-OTHER", "product_id": self.product.id})
        self._move(self.product, lot, 3, self.supplier_location, other_location)
        self._move(self.product, lot, 3, other_location, self.customer_location)
        self.assertEqual(self._loc_vals(lot), self._full_location())

    def test_move_line_exception_is_logged(self):
        lot = self.env["stock.lot"].create({"name": "LOT-EXC", "product_id": self.product.id})
        lot_model = type(self.env["stock.lot"])
        with mock.patch.object(lot_model, "write", side_effect=ValueError("boom"), autospec=True):
            self._move(self.product, lot, 2, self.supplier_location, self.stock_location)
        self.assertEqual(lot.loc_rack_id, self.rack)

    # ------------------------------------------------------------------ wizard
    def test_wizard_scan_and_change(self):
        lot = self.env["stock.lot"].create({"name": "LOT-WIZ-UNIQUE", "product_id": self.product.id})
        wizard = self.env["lot.change.location"].create({})
        wizard.on_barcode_scanned("LOT-WIZ-UNIQUE")
        self.assertEqual(wizard.lot_id, lot)
        self.assertTrue(wizard.lot_scanned)
        wizard.on_barcode_scanned("RACK-TEST-002")
        self.assertEqual(wizard.rack_id, self.rack2)
        wizard.do_change()
        self.assertEqual(self._loc_vals(lot), (self.storehouse, self.zone, self.shelf, self.section, self.rack2))
        wizard.reset()
        self.assertFalse(wizard.lot_id)
        self.assertFalse(wizard.rack_id)
        self.assertFalse(wizard.lot_scanned)
        # nothing selected: do_change does nothing
        wizard.do_change()

    def test_wizard_errors(self):
        self.env["stock.lot"].create({"name": "LOT-WIZ-ERR", "product_id": self.product.id})
        wizard = self.env["lot.change.location"].create({})
        with self.assertRaises(UserError):
            wizard.on_barcode_scanned("UNKNOWN-LOT-XYZ")
        wizard.on_barcode_scanned("LOT-WIZ-ERR")
        with self.assertRaises(UserError):
            wizard.on_barcode_scanned("UNKNOWN-RACK-XYZ")

    def test_wizard_ambiguous_lot(self):
        self.env["stock.lot"].create({"name": "LOT-DUP", "product_id": self.product.id})
        self.env["stock.lot"].create({"name": "LOT-DUP", "product_id": self.product_no_loc.id})
        wizard = self.env["lot.change.location"].create({})
        with self.assertRaisesRegex(UserError, "Several lots/serials"):
            wizard.on_barcode_scanned("LOT-DUP")
        self.assertFalse(wizard.lot_id)
        self.assertFalse(wizard.lot_scanned)

    def test_wizard_new_lot_clears_previous_rack(self):
        lot_a = self.env["stock.lot"].create({"name": "LOT-WIZ-A", "product_id": self.product.id})
        lot_b = self.env["stock.lot"].create({"name": "LOT-WIZ-B", "product_id": self.product.id})
        wizard = self.env["lot.change.location"].create({})
        wizard.on_barcode_scanned("LOT-WIZ-A")
        wizard.on_barcode_scanned("RACK-TEST-002")
        wizard.do_change()
        self.assertEqual(lot_a.loc_rack_id, self.rack2)
        # scanning lot B without Reset must not reuse the rack chosen for lot A
        wizard.on_barcode_scanned("LOT-WIZ-B")
        self.assertEqual(wizard.lot_id, lot_b)
        self.assertFalse(wizard.rack_id)
        wizard.do_change()
        self.assertEqual(lot_b.loc_rack_id, self.rack)
