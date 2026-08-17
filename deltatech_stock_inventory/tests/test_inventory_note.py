# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestInventoryNote(TransactionCase):
    def setUp(self):
        super().setUp()
        self.stock_location = self.env["stock.location"].create({"name": "Test location", "usage": "internal"})
        self.product = self.env["product.product"].create({"name": "Test note", "is_storable": True})

    def _apply(self, quantity, note=False):
        quant = self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "inventory_quantity": quantity,
                "inventory_note": note,
            }
        )
        quant.action_apply_inventory()
        return quant

    def _last_move(self):
        return self.env["stock.move"].search(
            [("product_id", "=", self.product.id), ("is_inventory", "=", True)], order="id desc", limit=1
        )

    def test_note_becomes_move_reference(self):
        """Nota de pe linie ajunge in referinta mișcării de stoc generate."""
        self._apply(7, note="Marfa deteriorata la manipulare")
        move = self._last_move()
        # Pe 18.0 referinta unei mișcări fara transfer este chiar numele mișcării.
        self.assertEqual(move.name, "Marfa deteriorata la manipulare")
        self.assertEqual(move.reference, "Marfa deteriorata la manipulare")

    def test_note_cleared_after_apply(self):
        """Nota se goleste dupa aplicare, ca sa nu fie refolosita la ajustarea urmatoare."""
        quant = self._apply(7, note="Motiv prima ajustare")
        self.assertFalse(quant.inventory_note)

        quant.inventory_quantity = 9
        quant.action_apply_inventory()
        move = self._last_move()
        self.assertNotEqual(move.reference, "Motiv prima ajustare")

    def test_without_note_standard_reference_kept(self):
        """Fara nota, referinta rămâne cea standard.

        Standardul adauga in referinta numele utilizatorului din `user_id` (*Assigned To*, cel
        caruia i s-a repartizat numaratoarea), nu al celui care opereaza efectiv ajustarea. Fara
        `user_id` completat, referinta nu spune nimic despre motiv sau despre operator — de aceea
        nota de pe linie este singura urma per produs a motivului.
        """
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Operator inventar",
                    "login": "operator_inv_note",
                    "groups_id": [
                        (
                            6,
                            0,
                            [
                                self.env.ref("stock.group_stock_manager").id,
                                self.env.ref("deltatech_stock_inventory.group_view_inventory_button").id,
                            ],
                        )
                    ],
                }
            )
        )
        quant = (
            self.env["stock.quant"]
            .with_user(user)
            .create(
                {
                    "product_id": self.product.id,
                    "location_id": self.stock_location.id,
                    "inventory_quantity": 5,
                }
            )
        )
        quant.action_apply_inventory()
        self.assertNotIn(user.display_name, self._last_move().reference)

        quant.write({"inventory_quantity": 8, "user_id": user.id})
        quant.action_apply_inventory()
        self.assertIn(user.display_name, self._last_move().reference)
