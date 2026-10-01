# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestInventoryConflict(TransactionCase):
    """INVENTORY-001: documentul de inventar nu se finalizeaza cat timp standardul
    intoarce wizardul de conflict (stock.inventory.conflict) fara sa aplice stocul."""

    def setUp(self):
        super().setUp()
        self.location = self.env["stock.location"].create({"name": "Test conflict", "usage": "internal"})
        self.product = self.env["product.product"].create({"name": "Test conflict", "is_storable": True})
        self.Quant = self.env["stock.quant"]
        self.Quant._update_available_quantity(self.product, self.location, 10)
        self.quant = self.Quant.search([("product_id", "=", self.product.id), ("location_id", "=", self.location.id)])
        # numarare la 15, apoi o receptie intervenita (+2) => quant-ul devine is_outdated
        self.quant.inventory_quantity = 15
        self.quant.inventory_note = "Motiv"
        # diferenta (camp stocat) se fixeaza la numarare, ca in interfata
        self.assertEqual(self.quant.inventory_diff_quantity, 5)
        move = self.env["stock.move"].create(
            {
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.location.id,
                "product_id": self.product.id,
                "product_uom_qty": 2.0,
            }
        )
        move._action_confirm()
        move.quantity = 2
        move.picked = True
        move._action_done()
        self.assertEqual(self.quant.quantity, 12)
        self.assertTrue(self.quant.is_outdated)

    def _moves(self):
        return self.env["stock.move"].search([("product_id", "=", self.product.id), ("is_inventory", "=", True)])

    def _open_conflict(self):
        res = self.quant.action_apply_inventory()
        self.assertEqual(res and res.get("res_model"), "stock.inventory.conflict")
        return res

    def test_conflict_does_not_finalize_inventory(self):
        """Cat timp wizardul nu e rezolvat, documentul ramane in lucru, cu legaturile si nota."""
        self._open_conflict()
        inventory = self.quant.inventory_id
        self.assertTrue(inventory)
        self.assertEqual(inventory.state, "confirm")
        self.assertFalse(self.quant.inventory_line_id.is_ok)
        self.assertEqual(self.quant.inventory_note, "Motiv")
        self.assertFalse(self.quant.last_inventory_date)
        self.assertFalse(self._moves())
        self.assertEqual(self.quant.quantity, 12)

    def _resolve(self, method):
        res = self._open_conflict()
        inventory = self.quant.inventory_id
        wizard = Form(self.env["stock.inventory.conflict"].with_context(**res["context"])).save()
        getattr(wizard, method)()
        return inventory

    def test_keep_counted_quantity_uses_same_document(self):
        """Rezolvarea wizardului finalizeaza documentul initial, nu unul nou."""
        inventory_count = self.env["stock.inventory"].search_count([])
        inventory = self._resolve("action_keep_counted_quantity")
        self.assertEqual(self.env["stock.inventory"].search_count([]), inventory_count + 1)
        self.assertEqual(inventory.state, "done")
        self.assertEqual(self.quant.quantity, 15)
        moves = self._moves()
        self.assertEqual(len(moves), 1)  # receptia nu e is_inventory
        self.assertEqual(moves.inventory_id, inventory)
        self.assertEqual(moves.reference, "Motiv")
        self.assertTrue(inventory.line_ids.is_ok)
        self.assertFalse(self.quant.inventory_id)
        self.assertFalse(self.quant.inventory_note)

    def test_keep_difference_uses_same_document(self):
        inventory = self._resolve("action_keep_difference")
        self.assertEqual(inventory.state, "done")
        self.assertEqual(self.quant.quantity, 17)
        self.assertEqual(self._moves().inventory_id, inventory)

    def test_without_conflict_finalizes(self):
        """Fara conflict, comportamentul ramane neschimbat: documentul se finalizeaza imediat."""
        self.quant.inventory_quantity = 20
        self.assertFalse(self.quant.is_outdated)
        inventory = self.quant.create_inventory_lines()
        self.assertFalse(self.quant.action_apply_inventory())
        self.assertEqual(inventory.state, "done")
        self.assertEqual(self.quant.quantity, 20)
        self.assertEqual(self._moves().inventory_id, inventory)
