# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCoverageWizards(TransactionCase):
    """Wizard-urile modulului: retur din picking, motivul ajustarii, imbinarea documentelor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create({"name": "Test wizard", "is_storable": True})
        cls.Quant = cls.env["stock.quant"]
        cls.Quant._update_available_quantity(cls.product, cls.stock_location, 10)
        cls.quant = cls.Quant._gather(cls.product, cls.stock_location)

    def _validate(self, picking, qty):
        picking.action_assign()
        picking.move_ids.quantity = qty
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def _return_wizard(self, picking):
        return Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking.ids, active_id=picking.id, active_model="stock.picking"
            )
        ).save()

    def _done_inventory(self, location, product, qty):
        inventory = self.env["stock.inventory"].create(
            {
                "name": "INV merge",
                "location_ids": [(6, 0, location.ids)],
                "product_ids": [(6, 0, product.ids)],
            }
        )
        inventory.action_start()
        inventory.line_ids.product_qty = qty
        inventory.action_validate()
        self.assertEqual(inventory.state, "done")
        return inventory

    # retur din picking

    def test_return_suggests_quantity_not_yet_returned(self):
        """Wizardul de retur propune cantitatea livrata minus ce s-a returnat deja."""
        delivery = self.env["stock.picking"].create(
            {
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 10,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        delivery.action_confirm()
        self._validate(delivery, 10)

        wizard = self._return_wizard(delivery)
        self.assertEqual(wizard.product_return_moves.quantity, 10)
        wizard.product_return_moves.quantity = 3
        action = wizard.action_create_returns()
        self._validate(self.env["stock.picking"].browse(action["res_id"]), 3)

        wizard = self._return_wizard(delivery)
        self.assertEqual(wizard.product_return_moves.quantity, 7)

    # motivul ajustarii

    def test_adjustment_name_defaults_to_inventory_document(self):
        inventory = self.env["stock.inventory"].create({"name": "INV/MOTIV"})
        self.quant.inventory_id = inventory
        wizard = (
            self.env["stock.inventory.adjustment.name"]
            .with_context(default_quant_ids=self.quant.ids)
            .create({"quant_ids": [(6, 0, self.quant.ids)]})
        )
        self.assertEqual(wizard.inventory_adjustment_name, "INV/MOTIV")

    def test_adjustment_name_empty_without_inventory(self):
        wizard = (
            self.env["stock.inventory.adjustment.name"]
            .with_context(default_quant_ids=self.quant.ids)
            .create({"quant_ids": [(6, 0, self.quant.ids)]})
        )
        self.assertFalse(wizard.inventory_adjustment_name)
        wizard = self.env["stock.inventory.adjustment.name"].create({})
        self.assertFalse(wizard.inventory_adjustment_name)

    # imbinarea documentelor

    def test_merge_requires_two_inventories(self):
        wizard = self.env["stock.inventory.merge"].create({"name": "M"})
        with self.assertRaises(UserError):
            wizard.merge_inventory()
        inventory = self._done_inventory(self.stock_location, self.product, 10)
        with self.assertRaises(UserError):
            wizard.with_context(active_ids=inventory.ids).merge_inventory()

    def test_merge_without_name_and_location(self):
        """Cu numele "/" si fara locatie, documentul rezultat ia numarul din secventa
        si locatiile documentelor imbinate."""
        location_a = self.env["stock.location"].create(
            {"name": "Merge A", "usage": "internal", "location_id": self.stock_location.id}
        )
        location_b = self.env["stock.location"].create(
            {"name": "Merge B", "usage": "internal", "location_id": self.stock_location.id}
        )
        product_b = self.env["product.product"].create({"name": "Test wizard B", "is_storable": True})
        inventory_a = self._done_inventory(location_a, self.product, 4)
        inventory_b = self._done_inventory(location_b, product_b, 6)
        lines = inventory_a.line_ids | inventory_b.line_ids
        moves = inventory_a.move_ids | inventory_b.move_ids

        wizard = self.env["stock.inventory.merge"].create({"name": "/", "location_id": False})
        action = wizard.with_context(active_ids=(inventory_a | inventory_b).ids).merge_inventory()

        merged = self.env["stock.inventory"].browse(action["res_id"])
        self.assertNotEqual(merged.name, "/")
        self.assertEqual(merged.state, "done")
        self.assertEqual(merged.location_ids, location_a | location_b)
        self.assertEqual(merged.line_ids, lines)
        self.assertEqual(merged.move_ids, moves)
        self.assertFalse((inventory_a | inventory_b).exists())
