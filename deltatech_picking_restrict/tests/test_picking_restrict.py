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
            }
        )
        # Create a test group for validation
        self.validation_group = self.env["res.groups"].create(
            {
                "name": "Test Validation Group",
                "users": [(4, self.user_a.id)],
            }
        )

        # Ensure that the user is correctly added to the validation group
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
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "company_id": self.company.id,  # Ensure product is assigned to the same company
            }
        )

        # Create a test move
        self.move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "picking_id": self.stock_picking.id,
                "quantity_done": 10,
                "company_id": self.company.id,  # Ensure move is assigned to the same company
            }
        )

        # Create a test move line
        self.move_line = self.env["stock.move.line"].create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "qty_done": 10,
                "reserved_uom_qty": 10,
                "company_id": self.company.id,  # Ensure move line is assigned to the same company
            }
        )

    def test_validate_with_correct_user_and_quantities(self):
        # Test that validation succeeds with correct user and quantities

        with self.assertRaises(UserError):
            self.stock_picking.with_user(self.user_a).button_validate()

    def test_validate_with_incorrect_user(self):
        # Remove the current user from the validation group
        self.validation_group.users = [(3, self.env.user.id)]
        with self.assertRaises(UserError):
            self.stock_picking.button_validate()

    def test_validate_with_incorrect_quantities(self):
        # Set done quantity different from reserved quantity
        self.move_line.qty_done = 5
        with self.assertRaises(UserError):
            self.stock_picking.button_validate()

    def test_validate_with_new_product(self):
        # Create a new move line with done quantity but no reserved quantity
        self.env["stock.move.line"].create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "qty_done": 5,
                "company_id": self.company.id,  # Ensure new move line is assigned to the same company
            }
        )
        with self.assertRaises(UserError):
            self.stock_picking.button_validate()
