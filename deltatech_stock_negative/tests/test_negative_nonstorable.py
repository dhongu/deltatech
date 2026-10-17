"""Produse fără evidență de stoc (`is_storable=False`) pe o locație fără stoc negativ.

Odoo nu ține quant-uri pentru produsele consumabile fără evidență de stoc:
`_should_bypass_reservation` sare rezervarea, iar `_synchronize_quant` nu scrie
nimic. Verificarea modulului compara totuși cantitatea liniei cu un stoc fizic
care, pentru ele, este mereu zero, așa că orice livrare care le conținea era
refuzată (#3480). Regula trebuie să se aplice doar produselor cu stoc urmărit.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestNegativeNonStorable(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.no_negative_stock = True
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.storable = cls.env["product.product"].create({"name": "Storable", "type": "consu", "is_storable": True})
        cls.consumable = cls.env["product.product"].create(
            {"name": "Consumable", "type": "consu", "is_storable": False}
        )

    def _move(self, product, quantity):
        move = self.env["stock.move"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "product_id": product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": quantity,
            }
        )
        move._action_confirm()
        move.picked = True
        move.move_line_ids.unlink()
        vals = move._prepare_move_line_vals()
        vals["quantity"] = quantity
        self.env["stock.move.line"].create(vals)
        return move

    def test_nonstorable_product_is_not_blocked(self):
        move = self._move(self.consumable, 1.0)
        move._action_done()
        self.assertEqual(move.state, "done")

    def test_mixed_delivery_checks_only_the_storable_line(self):
        self.env["stock.quant"]._update_available_quantity(self.storable, self.stock_location, 1.0)
        moves = self._move(self.storable, 1.0) | self._move(self.consumable, 3.0)
        moves._action_done()
        self.assertEqual(set(moves.mapped("state")), {"done"})

    def test_mixed_delivery_still_blocks_the_short_storable_line(self):
        self.env["stock.quant"]._update_available_quantity(self.storable, self.stock_location, 1.0)
        moves = self._move(self.storable, 2.0) | self._move(self.consumable, 3.0)
        with self.assertRaises(UserError) as cm:
            moves._action_done()
        self.assertRegex(cm.exception.args[0], "avoid negative stock")
