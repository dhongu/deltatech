from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockPickingTransfer(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a test partner
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Create a test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
            }
        )

        # Create stock locations
        self.location_source = self.env["stock.location"].create(
            {
                "name": "Source Location",
                "usage": "internal",
            }
        )
        self.location_dest = self.env["stock.location"].create(
            {
                "name": "Destination Location",
                "usage": "internal",
            }
        )
        self.final_dest_location = self.env["stock.location"].create(
            {
                "name": "Final Destination Location",
                "usage": "internal",
            }
        )

        # Create a picking type
        self.picking_type_internal = self.env["stock.picking.type"].create(
            {
                "name": "Internal Transfers",
                "code": "internal",
                "sequence_code": "INT",
                "warehouse_id": self.env["stock.warehouse"].search([], limit=1).id,
            }
        )

        # Create a second picking type
        self.picking_type_second = self.env["stock.picking.type"].create(
            {
                "name": "Second Operation",
                "code": "internal",
                "sequence_code": "SEC",
                "warehouse_id": self.env["stock.warehouse"].search([], limit=1).id,
            }
        )

        # Link the first picking type to the second
        self.picking_type_internal.write({"next_operation_id": self.picking_type_second.id})

        # Create a stock picking
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_internal.id,
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
                "note": "Test Picking Note",
            }
        )

        # Create a stock move
        self.move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
            }
        )

    def test_create_second_transfer(self):
        # Confirm the picking and move to 'done' state
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking._compute_sub_location_existent()
        for move in self.picking.move_lines:
            move.quantity_done = move.product_uom_qty
        self.picking.button_validate()
        self.picking.reassign_location()

        # Open transfer wizard and create second transfer
        wizard = (
            self.env["stock.picking.transfer.wizard"]
            .with_context(active_id=self.picking.id)
            .create(
                {
                    "final_dest_location_id": self.final_dest_location.id,
                }
            )
        )
        wizard.confirm_transfer()

        # Check if second transfer is created
        second_picking = self.env["stock.picking"].search(
            [("location_id", "=", self.location_dest.id), ("location_dest_id", "=", self.final_dest_location.id)],
            limit=1,
        )
        self.assertTrue(second_picking, "Second transfer should be created.")
        self.assertEqual(
            second_picking.picking_type_id,
            self.picking_type_second,
            "Second transfer should have the correct picking type.",
        )
        self.assertTrue(
            self.picking.second_transfer_created, "Second transfer flag should be set on the original picking."
        )

        # Check if moves are copied correctly
        self.assertEqual(len(second_picking.move_lines), 1, "There should be one move in the second picking.")
        self.assertEqual(
            second_picking.move_lines.product_id,
            self.product,
            "The product in the second move should match the original product.",
        )
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("deltatech_picking_transit.use_sub_locations", "True")

    def test_create_move_in_second_transfer_picking(self):
        # Confirm the picking and move to 'done' state
        self.picking.action_confirm()
        self.picking.action_assign()
        for move in self.picking.move_lines:
            move.quantity_done = move.product_uom_qty
        self.picking.button_validate()

        # Open transfer wizard and create second transfer
        wizard = (
            self.env["stock.picking.transfer.wizard"]
            .with_context(active_id=self.picking.id)
            .create(
                {
                    "final_dest_location_id": self.final_dest_location.id,
                }
            )
        )
        wizard.confirm_transfer()

        # Attempt to create another move in the original picking, expecting an error
        with self.assertRaises(
            UserError, msg="You can't add another move to this picking because the second transfer is already created."
        ):
            self.env["stock.move"].create(
                {
                    "name": "Another Test Move",
                    "product_id": self.product.id,
                    "product_uom_qty": 5,
                    "product_uom": self.product.uom_id.id,
                    "picking_id": self.picking.id,
                    "location_id": self.location_source.id,
                    "location_dest_id": self.location_dest.id,
                }
            )
