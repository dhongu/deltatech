# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCoverageQuant(TransactionCase):
    """Quant-uri: legatura cu documentul de inventar si drepturile de modificare a cantitatii."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env["stock.location"].create({"name": "Test quant cov", "usage": "internal"})
        cls.product = cls.env["product.product"].create({"name": "Test quant cov", "is_storable": True})
        cls.Quant = cls.env["stock.quant"]
        cls.Quant._update_available_quantity(cls.product, cls.location, 10)
        cls.quant = cls.Quant._gather(cls.product, cls.location)
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Fara drept de ajustare",
                    "login": "no_adjust_cov",
                    "group_ids": [(6, 0, cls.env.ref("stock.group_stock_manager").ids)],
                }
            )
        )

    def test_quants_from_different_inventories(self):
        product_b = self.env["product.product"].create({"name": "Test quant cov B", "is_storable": True})
        self.Quant._update_available_quantity(product_b, self.location, 1)
        quant_b = self.Quant._gather(product_b, self.location)
        self.quant.inventory_id = self.env["stock.inventory"].create({"name": "INV A"})
        quant_b.inventory_id = self.env["stock.inventory"].create({"name": "INV B"})
        with self.assertRaises(UserError):
            (self.quant | quant_b).create_inventory_lines()

    def test_counted_quantity_updates_inventory_line(self):
        self.quant.inventory_quantity = 12
        self.quant.create_inventory_lines()
        line = self.quant.inventory_line_id
        self.assertEqual(line.product_qty, 12)
        line.is_ok = False
        self.quant.inventory_quantity = 14
        self.assertEqual(line.product_qty, 14)
        self.assertTrue(line.is_ok)

    def test_user_without_group_cannot_change_quantities(self):
        self.quant.inventory_quantity = 15
        with self.assertRaises(UserError):
            self.quant.with_user(self.user).action_apply_inventory()
        with self.assertRaises(UserError):
            self.quant.with_user(self.user).write({"inventory_quantity": 3, "inventory_quantity_set": True})
        with self.assertRaises(UserError):
            self.Quant.with_user(self.user).create(
                {"product_id": self.product.id, "location_id": self.location.id, "inventory_quantity": 2}
            )

    def test_default_location_from_putaway_rule(self):
        shelf = self.env["stock.location"].create(
            {"name": "Raft cov", "usage": "internal", "location_id": self.location.id}
        )
        self.env["stock.putaway.rule"].create(
            {"product_id": self.product.id, "location_in_id": self.location.id, "location_out_id": shelf.id}
        )
        defaults = self.Quant.with_context(default_product_id=self.product.id).default_get(["location_id"])
        self.assertEqual(defaults["location_id"], shelf.id)


@tagged("post_install", "-at_install")
class TestCoverageInventory(TransactionCase):
    """Documentul de inventar si liniile lui: stari, generare fara locatie, onchange, cautari."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.location = cls.env["stock.location"].create({"name": "Test inv cov", "usage": "internal"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test inv cov", "is_storable": True, "standard_price": 2}
        )
        cls.product_b = cls.env["product.product"].create({"name": "Test inv cov B", "is_storable": True})
        cls.product_lot = cls.env["product.product"].create(
            {"name": "Test inv cov lot", "is_storable": True, "tracking": "lot"}
        )
        cls.product_serial = cls.env["product.product"].create(
            {"name": "Test inv cov serial", "is_storable": True, "tracking": "serial"}
        )
        cls.Quant = cls.env["stock.quant"]
        cls.Quant._update_available_quantity(cls.product, cls.location, 5)
        cls.Line = cls.env["stock.inventory.line"]

    def _inventory(self, **vals):
        values = {"name": "INV cov", "location_ids": [(6, 0, self.location.ids)]}
        values.update(vals)
        return self.env["stock.inventory"].create(values)

    def _line(self, inventory, product, **vals):
        values = {"inventory_id": inventory.id, "product_id": product.id, "location_id": self.location.id}
        values.update(vals)
        return self.Line.create(values)

    def test_validate_guards(self):
        self.assertIsNone(self.env["stock.inventory"].action_validate())
        with self.assertRaises(UserError):
            self._inventory().action_validate()
        # produs cu loturi numarat fara lot
        inventory = self._inventory(state="confirm")
        self._line(inventory, self.product_lot, product_qty=5)
        with self.assertRaises(UserError):
            inventory.action_validate()

    def test_cancel_draft_removes_lines(self):
        inventory = self._inventory()
        inventory.action_start()
        self.assertTrue(inventory.line_ids)
        inventory.action_cancel_draft()
        self.assertFalse(inventory.line_ids)
        self.assertEqual(inventory.state, "draft")

    def test_lines_not_ok(self):
        inventory = self._inventory(state="confirm")
        line_ok = self._line(inventory, self.product, product_qty=5)
        line_not_ok = self._line(inventory, self.product_b, product_qty=1, is_ok=False)

        inventory.action_new_for_not_ok()
        self.assertEqual(inventory.line_ids, line_ok)
        new_inventory = line_not_ok.inventory_id
        self.assertNotEqual(new_inventory, inventory)
        self.assertEqual(new_inventory.state, "confirm")
        self.assertEqual(new_inventory.name, "INV cov (copy)")

        new_inventory.action_remove_not_ok()
        self.assertFalse(new_inventory.line_ids)

    def test_lines_without_locations(self):
        """Fara locatii: stocul se cauta in locatiile interne ale companiei, iar produsele
        epuizate primesc linii pe locatiile de stoc ale depozitelor."""
        self.Quant._update_available_quantity(self.product, self.stock_location, 3)
        inventory = self.env["stock.inventory"].create(
            {
                "name": "INV fara locatii",
                "product_ids": [(6, 0, (self.product | self.product_b).ids)],
                "exhausted": True,
                "prefill_counted_quantity": "zero",
            }
        )
        vals = inventory._get_inventory_lines_values()
        found = {(v["product_id"], v["location_id"]): v for v in vals}
        self.assertEqual(found[(self.product.id, self.location.id)]["theoretical_qty"], 5)
        self.assertEqual(found[(self.product.id, self.location.id)]["product_qty"], 0)
        self.assertEqual(found[(self.product.id, self.stock_location.id)]["theoretical_qty"], 3)
        self.assertEqual(found[(self.product_b.id, self.stock_location.id)]["theoretical_qty"], 0)

    def test_open_lines_of_done_inventory(self):
        self.env["stock.location"].create({"name": "Sub cov", "usage": "internal", "location_id": self.location.id})
        inventory = self._inventory(state="done", product_ids=[(6, 0, self.product.ids)])
        action = inventory.action_open_inventory_lines()
        context = action["context"]
        self.assertFalse(context["default_is_editable"])
        self.assertEqual(context["default_location_id"], self.location.id)
        self.assertNotIn("readonly_location_id", context, "locatia are sublocatii")
        self.assertEqual(context["default_product_id"], self.product.id)
        self.assertEqual(
            action["view_id"], self.env.ref("deltatech_stock_inventory.stock_inventory_line_tree_no_product_create").id
        )

    def test_onchange_quantity_context_edge_cases(self):
        # produs fara locatie: scriptic 0
        line = self.Line.new({"product_id": self.product.id, "product_qty": 0})
        line._onchange_quantity_context()
        self.assertEqual(line.theoretical_qty, 0)
        self.assertEqual(line.product_uom_id, self.product.uom_id)
        self.assertEqual(line.standard_price, 2)

        # lotul altui produs se goleste
        other_lot = self.env["stock.lot"].create({"name": "LOT-ALT", "product_id": self.product_serial.id})
        line = self.Line.new(
            {"product_id": self.product_lot.id, "location_id": self.location.id, "prod_lot_id": other_lot.id}
        )
        line._onchange_quantity_context()
        self.assertFalse(line.prod_lot_id)

        # produs cu numar de serie: cantitatea numarata devine 1
        serial = self.env["stock.lot"].create({"name": "SN-1", "product_id": self.product_serial.id})
        line = self.Line.new(
            {"product_id": self.product_serial.id, "location_id": self.location.id, "prod_lot_id": serial.id}
        )
        line._onchange_quantity_context()
        self.assertEqual(line.product_qty, 1)

        line.is_ok = False
        line.onchange_product_qty()
        self.assertTrue(line.is_ok)

    def test_line_price_from_default_product(self):
        inventory = self._inventory(state="confirm")
        line = self.Line.with_context(
            default_product_id=self.product.id, default_product_uom_id=self.product.uom_id.id
        ).create({"inventory_id": inventory.id, "location_id": self.location.id, "theoretical_qty": 5})
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.standard_price, 2)

    def test_get_quants_create_and_refresh_without_quant(self):
        empty_location = self.env["stock.location"].create({"name": "Gol cov", "usage": "internal"})
        inventory = self._inventory(state="confirm", location_ids=[(6, 0, empty_location.ids)])
        line = self._line(inventory, self.product_b, location_id=empty_location.id, theoretical_qty=5)
        self.assertFalse(line.get_quants())

        # quant-ul a disparut: butonul de reimprospatare pune scripticul pe 0
        self.assertTrue(line.outdated)
        line.action_refresh_quantity()
        self.assertEqual(line.theoretical_qty, 0)

        quant = line.get_quants(create=True)
        self.assertTrue(quant)
        self.assertEqual(quant.location_id, empty_location)

    def test_reset_quantity_skips_done_lines(self):
        line_open = self._line(self._inventory(state="confirm"), self.product, product_qty=7)
        line_done = self._line(self._inventory(name="INV done", state="done"), self.product, product_qty=7)
        (line_open | line_done).action_reset_product_qty()
        self.assertEqual(line_open.product_qty, 0)
        self.assertEqual(line_done.product_qty, 7)

    def test_search_helpers_outside_inventory(self):
        with self.assertRaises(NotImplementedError):
            self.Line._search_difference_qty("=", 0)
        with self.assertRaises(NotImplementedError):
            self.Line.with_context(default_inventory_id=1)._search_difference_qty("like", 0)
        with self.assertRaises(NotImplementedError):
            self.Line._search_outdated("=", True)
        with self.assertRaises(NotImplementedError):
            self.Line._search_outdated("<", 1)

    def test_field_domains_from_active_inventory(self):
        inventory = self._inventory(product_ids=[(6, 0, (self.product | self.product_b).ids)])
        Line = self.Line.with_context(active_model="stock.inventory", active_id=inventory.id)
        self.assertIn(str(self.location.ids), Line._domain_location_id())
        self.assertIn(str((self.product | self.product_b).ids), Line._domain_product_id())


@tagged("post_install", "-at_install")
class TestCoverageProduct(TransactionCase):
    """Stoc pe depozite (mod detaliat si principal) si amplasarea produsului in depozit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.product = cls.env["product.product"].create({"name": "Test prod cov", "is_storable": True})
        cls.template = cls.product.product_tmpl_id
        cls.Quant = cls.env["stock.quant"]

    def _sublocation(self, name, parent):
        return self.env["stock.location"].create({"name": name, "usage": "internal", "location_id": parent.id})

    def test_detailed_stock_with_reserved_restricted_and_main(self):
        blocked = self._sublocation("Blocat cov", self.stock_location)
        blocked.restricted_stock = True
        self.Quant._update_available_quantity(self.product, self.stock_location, 10)
        self.Quant._update_available_quantity(self.product, blocked, 3)
        self.Quant._update_reserved_quantity(self.product, self.stock_location, 2)
        self.warehouse.kanban_display_stock = "detailed"
        wh_main = self.env["stock.warehouse"].create(
            {"name": "Cov main", "code": "CVM", "kanban_display_stock": "main"}
        )
        self.Quant._update_available_quantity(self.product, wh_main.lot_stock_id, 4)
        # depozit detaliat fara stoc pentru produs: nu apare
        self.env["stock.warehouse"].create({"name": "Cov empty", "code": "CVE", "kanban_display_stock": "detailed"})

        self.template.invalidate_recordset(["warehouse_stock"])
        lines = self.template.warehouse_stock.split("\n")
        self.assertIn(f"{self.warehouse.code}: 13.0 (R: 2.0, B: 3.0)", lines)
        self.assertIn("CVM: 4.0", lines)
        self.assertFalse([line for line in lines if line.startswith("CVE")])
        self.assertEqual(lines[-1].split(": ")[-1], "8.0")

    def test_detailed_stock_without_variants(self):
        self.assertEqual(self.env["product.template"]._get_detailed_warehouse_stocks(self.warehouse), {})

    def test_loc_from_location_context_and_inverse_create(self):
        wh2 = self.env["stock.warehouse"].create({"name": "Cov loc", "code": "CVL"})
        self.template.with_context(warehouse=wh2.id).write({"loc_rack": "R9", "loc_row": "S9"})
        mapping = self.env["product.warehouse.location"].search(
            [("product_id", "=", self.template.id), ("warehouse_id", "=", wh2.id)]
        )
        self.assertEqual(mapping.loc_rack, "R9")
        template = self.template.with_context(location=wh2.lot_stock_id.id)
        self.assertEqual(template.loc_rack, "R9")
        self.assertEqual(template.loc_row, "S9")

    def test_get_location_variants(self):
        row = self._sublocation("RC", self.stock_location)
        rack = self._sublocation("A1", row)
        rack_short = self._sublocation("7", row)
        mapping = self.env["product.warehouse.location"].create(
            {"product_id": self.template.id, "warehouse_id": self.warehouse.id, "loc_row": "RC/RD", "loc_rack": "A1/A2"}
        )
        self.assertEqual(self.template.get_location(), rack)
        mapping.write({"loc_row": "RC", "loc_rack": "07"})
        self.assertEqual(self.template.get_location(), rack_short, "fara zero in fata")
        mapping.loc_rack = "08"
        self.assertFalse(self.template.get_location())
        mapping.loc_rack = "X8"
        self.assertFalse(self.template.get_location())
        mapping.loc_row = False
        self.assertFalse(self.template.get_location())
        mapping.unlink()
        self.assertFalse(self.template.get_location())

    def test_move_to_putaway_without_rule(self):
        with self.assertRaises(UserError):
            self.template.move_to_putaway_location()

    def test_theoretical_quantity_by_lot(self):
        product = self.env["product.product"].create(
            {"name": "Test prod cov lot", "is_storable": True, "tracking": "lot"}
        )
        lot_1 = self.env["stock.lot"].create({"name": "L1", "product_id": product.id})
        lot_2 = self.env["stock.lot"].create({"name": "L2", "product_id": product.id})
        self.Quant._update_available_quantity(product, self.stock_location, 4, lot_id=lot_1)
        self.Quant._update_available_quantity(product, self.stock_location, 6, lot_id=lot_2)
        qty = self.env["product.product"].get_theoretical_quantity(product.id, self.stock_location.id, lot_id=lot_1.id)
        self.assertEqual(qty, 4)
