# tests/test_stock_picking.py

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Define the company
        self.company = self.env.ref("base.main_company")

        # Create a sequence for request numbers
        self.sequence = self.env["ir.sequence"].create(
            {
                "name": "Test Sequence",
                "implementation": "standard",
                "prefix": "REQ/",
                "padding": 5,
                "number_increment": 1,
                "number_next": 1,
                "company_id": self.company.id,
            }
        )

        # Create a test picking type
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "code": "incoming",
                "sequence_code": "IN",
                "request_sequence_id": self.sequence.id,
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
            }
        )

    def test_action_get_number(self):
        # Test that the request number is generated correctly
        self.stock_picking.action_get_number()
        self.assertTrue(self.stock_picking.request_number, "Request number was not generated.")
        self.assertTrue(self.stock_picking.name.startswith("REQ/"), "Request number prefix is incorrect.")

    def test_unlink_with_request_number(self):
        # Test that unlink raises an error when the picking has a request number
        self.stock_picking.action_get_number()
        with self.assertRaises(UserError):
            self.stock_picking.unlink()

    def test_unlink_without_request_number(self):
        # Test that unlink works when the picking does not have a request number
        self.stock_picking.unlink()
        self.assertFalse(
            self.env["stock.picking"].search([("id", "=", self.stock_picking.id)]), "Stock picking was not deleted."
        )
