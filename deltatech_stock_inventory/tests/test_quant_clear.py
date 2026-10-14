# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestQuantClear(TransactionCase):
    """Butonul "Clear" de pe quant desface legatura cu documentul de inventar."""

    def setUp(self):
        super().setUp()
        self.location = self.env["stock.location"].create({"name": "Test clear", "usage": "internal"})
        self.product = self.env["product.product"].create({"name": "Test clear", "is_storable": True})
        self.env["stock.quant"]._update_available_quantity(self.product, self.location, 10)
        self.quant = self.env["stock.quant"]._gather(self.product, self.location)
        self.quant.inventory_quantity = 12
        self.inventory = self.quant.create_inventory_lines()

    def test_clear_unlinks_inventory(self):
        self.assertEqual(self.quant.inventory_id, self.inventory)
        self.assertTrue(self.quant.inventory_line_id)
        self.quant.action_clear_inventory_quantity()
        self.assertFalse(self.quant.inventory_id)
        self.assertFalse(self.quant.inventory_line_id)
        self.assertFalse(self.quant.inventory_quantity_set)

    def test_apply_after_clear_uses_new_document(self):
        self.quant.action_clear_inventory_quantity()
        self.quant.inventory_quantity = 14
        self.quant.action_apply_inventory()
        self.assertEqual(self.quant.quantity, 14)
        self.assertEqual(self.inventory.state, "confirm", "documentul vechi nu e finalizat de noua numarare")
        new_inventory = self.env["stock.inventory"].search(
            [("line_ids.product_id", "=", self.product.id), ("id", "!=", self.inventory.id)]
        )
        self.assertEqual(new_inventory.state, "done")
        self.assertEqual(new_inventory.line_ids.product_qty, 14)
