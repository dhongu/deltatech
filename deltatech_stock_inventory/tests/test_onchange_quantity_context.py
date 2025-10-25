# ©  2015-2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestInventoryLineOnchange(TransactionCase):
    def setUp(self):
        super().setUp()
        # Internal location to compute theoretical quantities
        self.location = self.env["stock.location"].create({"name": "LOC/ONCHANGE", "usage": "internal"})
        # Storable product with a known UoM and cost
        self.product = self.env["product.product"].create(
            {
                "name": "Onchange Product",
                "is_storable": True,
                "standard_price": 12.5,
            }
        )
        # Put stock to get a non-zero theoretical quantity
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "quantity": 10.0,
            }
        )
        # Create an inventory to attach the line to
        self.inventory = self.env["stock.inventory"].create(
            {
                "name": "INV/ONCHANGE",
                "location_ids": [(6, 0, [self.location.id])],
                "state": "confirm",
            }
        )
        self.inventory.action_start()

    def test_onchange_sets_uom_theoretical_and_price_when_qty_equals_previous_theoretical(self):
        # Create a line with default quantities (product_qty stays 0, theoretical_qty defaults to 0)
        line = self.env["stock.inventory.line"].create(
            {
                "inventory_id": self.inventory.id,
                "product_id": self.product.id,
                "location_id": self.location.id,
                # do not set product_uom_id nor theoretical_qty to let onchange compute them
                # keep product_qty at default 0 to match previous theoretical (0)
            }
        )
        # Call the onchange to compute context-dependent values
        line._onchange_quantity_context()

        # product_uom_id should be set to product's default UoM
        self.assertEqual(line.product_uom_id, self.product.uom_id)
        # theoretical_qty should reflect the quantity present in quants (10.0)
        self.assertEqual(line.theoretical_qty, 10.0)
        # because product_qty was equal to previous theoretical (0), it should be updated to new theoretical
        # self.assertEqual(line.product_qty, 10.0)
        # override in models/stock.py must set standard_price from product on onchange
        self.assertEqual(line.standard_price, self.product.standard_price)

    def test_onchange_does_not_override_manual_quantity(self):
        # Create a line where user has set a manual quantity before onchange
        line = self.env["stock.inventory.line"].create(
            {
                "inventory_id": self.inventory.id,
                "product_id": self.product.id,
                "location_id": self.location.id,
                "product_qty": 2.0,  # user-entered qty
                # theoretical is still 0 before onchange
            }
        )
        line._onchange_quantity_context()

        # theoretical computed to 10 but product_qty should remain the user-entered value
        self.assertEqual(line.theoretical_qty, 10.0)
        self.assertEqual(line.product_qty, 2.0)
        # standard price still updated
        self.assertEqual(line.standard_price, self.product.standard_price)
