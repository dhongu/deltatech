# tests/test_picking_restrict.py

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockPickingValidation(TransactionCase):
    def setUp(self):
        super().setUp()

        self.user_a = self.env["res.users"].create(
            {
                "name": "User A",
                "login": "user_a",
                "group_ids": [(4, self.env.ref("stock.group_stock_manager").id)],
            }
        )
        # Create a test group for validation
        self.validation_group = self.env["res.groups"].create(
            {
                "name": "Test Validation Group",
                "user_ids": [(4, self.user_a.id)],
            }
        )

        # Define the company
        self.company = self.env.ref("base.main_company")

        # Create a test picking type with restrictions
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "code": "internal",
                "sequence_code": "INT",
                "validate_group_id": self.validation_group.id,
                "restrict_quantities": True,
                "restrict_new_products": True,
                "company_id": self.company.id,
            }
        )

        # Create a test stock picking
        self.stock_picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                "picking_type_id": self.picking_type.id,
                "company_id": self.company.id,  # Ensure picking is assigned to the same company
            }
        )

        # Create a test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "is_storable": True,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "company_id": self.company.id,  # Ensure product is assigned to the same company
            }
        )

        # Create a test move
        self.move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "picking_id": self.stock_picking.id,
                "quantity": 10,
                "company_id": self.company.id,  # Ensure move is assigned to the same company
            }
        )

        # Setting the move quantity already creates its move line
        self.move_line = self.move.move_line_ids
        self.assertEqual(self.move.quantity, 10)

    def test_validate_with_incorrect_user(self):
        # Remove the validating user from the validation group
        self.validation_group.user_ids = [(3, self.user_a.id)]
        with self.assertRaisesRegex(UserError, "cannot validate this type of transfer"):
            self.stock_picking.with_user(self.user_a).button_validate()

    def test_validate_with_incorrect_quantities(self):
        # Set done quantity different from reserved quantity
        self.move_line.quantity = 5
        with self.assertRaisesRegex(UserError, "Done quantities not equal to reserved"):
            self.stock_picking.with_user(self.user_a).button_validate()

    def test_validate_with_new_product(self):
        # A line for another product, added directly on the transfer, has no ordered quantity
        new_product = self.env["product.product"].create({"name": "New Product", "type": "consu"})
        self.env["stock.move.line"].create(
            {
                "picking_id": self.stock_picking.id,
                "product_id": new_product.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "quantity": 5,
                "company_id": self.company.id,
            }
        )
        with self.assertRaisesRegex(UserError, "Unrecognized product"):
            self.stock_picking.with_user(self.user_a).button_validate()
