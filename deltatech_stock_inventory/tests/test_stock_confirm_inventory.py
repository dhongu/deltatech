# ©  2015-2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockConfirmInventory(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create location
        self.location = self.env["stock.location"].create({"name": "Test Location", "usage": "internal"})
        # Create a storable product
        self.product = self.env["product.product"].create(
            {
                "name": "Confirm Inv Product",
                "is_storable": True,
                "standard_price": 10.0,
            }
        )
        # Put some stock to have quants and qty_available
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "quantity": 5.0,
            }
        )
        # Create an inventory with a line so that wizard can compute last inventory
        self.inventory = self.env["stock.inventory"].create(
            {
                "name": "INV/CONFIRM",
                "date": fields.Datetime.now(),
                "location_ids": [(6, 0, [self.location.id])],
                "state": "confirm",
            }
        )
        self.inventory.action_start()
        self.env["stock.inventory.line"].create(
            {
                "inventory_id": self.inventory.id,
                "product_id": self.product.id,
                "location_id": self.location.id,
                "product_qty": 5.0,
                "is_ok": True,
            }
        )
        self.inventory.action_validate()

    def test_confirm_inventory_wizard_flow(self):
        # Create wizard with context on product template
        wiz = (
            self.env["stock.confirm.inventory"]
            .with_context(active_id=self.product.product_tmpl_id.id, active_model="product.template")
            .create(
                {
                    "location_id": self.location.id,
                }
            )
        )
        # Trigger onchange/compute to fill fields
        wiz._onchange_product_tmpl_id()
        # Ensure the wizard computed fields without error
        self.assertTrue(wiz.last_inventory_id, "Wizard should compute last inventory")
        self.assertTrue(wiz.last_inventory_date, "Wizard should compute last inventory date")
        # Calling confirm should not raise and should act on quants
        wiz.confirm_actual_inventory()

    def test_confirm_inventory_from_product_variant_context(self):
        # Create wizard with context on product.product
        wiz = (
            self.env["stock.confirm.inventory"]
            .with_context(active_id=self.product.id, active_model="product.product")
            .create({"location_id": self.location.id})
        )
        wiz._onchange_product_tmpl_id()
        self.assertEqual(wiz.product_tmpl_id, self.product.product_tmpl_id)
        wiz.confirm_actual_inventory()
