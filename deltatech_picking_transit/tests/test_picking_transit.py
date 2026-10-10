from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingTransit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.dest_partner = cls.env["res.partner"].create({"name": "Transit Destination Warehouse"})
        cls.dest_warehouse = cls.env["stock.warehouse"].create(
            {"name": "Transit Destination", "code": "TRD", "partner_id": cls.dest_partner.id}
        )
        cls.transit_location = cls.env["stock.location"].create(
            {"name": "Transit", "usage": "internal", "location_id": cls.warehouse.view_location_id.id}
        )
        cls.product = cls.env["product.product"].create({"name": "Transit Product", "is_storable": True})
        cls.other_product = cls.env["product.product"].create({"name": "Other Product", "is_storable": True})
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse.lot_stock_id, 10)

        cls.delivery_type = cls.env["stock.picking.type"].create(
            {
                "name": "Transit Delivery",
                "code": "internal",
                "sequence_code": "TRO",
                "warehouse_id": cls.warehouse.id,
                "two_step_transfer_use": "delivery",
                "default_location_src_id": cls.warehouse.lot_stock_id.id,
                "default_location_dest_id": cls.transit_location.id,
            }
        )
        cls.reception_type = cls.env["stock.picking.type"].create(
            {
                "name": "Transit Reception",
                "code": "internal",
                "sequence_code": "TRI",
                "warehouse_id": cls.dest_warehouse.id,
                "two_step_transfer_use": "reception",
                "default_location_src_id": cls.transit_location.id,
                "default_location_dest_id": cls.dest_warehouse.lot_stock_id.id,
            }
        )

    def _create_first_picking(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.delivery_type.id,
                "partner_id": self.dest_partner.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.transit_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 4,
                            "location_id": self.warehouse.lot_stock_id.id,
                            "location_dest_id": self.transit_location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = 4
        picking.move_ids.picked = True
        return picking

    def _second_picking(self, picking):
        return self.env["stock.picking"].search([("source_transfer_id", "=", picking.id)])

    def test_wizard_creates_second_transfer(self):
        picking = self._create_first_picking()
        wizard = (
            self.env["stock.picking.transfer.wizard"]
            .with_context(active_id=picking.id)
            .create({"operation_id": self.reception_type.id})
        )
        wizard.confirm_transfer()

        second = self._second_picking(picking)
        self.assertEqual(len(second), 1)
        self.assertTrue(picking.second_transfer_created)
        self.assertEqual(second.picking_type_id, self.reception_type)
        self.assertEqual(second.location_id, self.transit_location)
        self.assertEqual(second.location_dest_id, self.dest_warehouse.lot_stock_id)
        self.assertEqual(second.move_ids.product_id, self.product)
        self.assertEqual(second.move_ids.product_uom_qty, 4)
        self.assertEqual(second.move_ids.location_dest_id, self.dest_warehouse.lot_stock_id)

    def test_auto_second_transfer_and_validation(self):
        self.delivery_type.auto_second_transfer = True
        picking = self._create_first_picking()
        picking.button_validate()
        self.assertEqual(picking.state, "done")

        second = self._second_picking(picking)
        self.assertEqual(len(second), 1)
        self.assertEqual(second.move_ids.product_id, self.product)

        # validating the receiving leg checks its products against the source transfer
        second.action_assign()
        second.move_ids.quantity = 4
        second.move_ids.picked = True
        second.button_validate()
        self.assertEqual(second.state, "done")

    def test_validation_rejects_product_not_in_source(self):
        picking = self._create_first_picking()
        picking.button_validate()
        foreign = self.env["stock.picking"].create(
            {
                "picking_type_id": self.reception_type.id,
                "source_transfer_id": picking.id,
                "location_id": self.transit_location.id,
                "location_dest_id": self.dest_warehouse.lot_stock_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.other_product.id,
                            "product_uom_qty": 1,
                            "location_id": self.transit_location.id,
                            "location_dest_id": self.dest_warehouse.lot_stock_id.id,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            foreign.button_validate()

    def test_computes_on_multiple_records(self):
        pickings = self._create_first_picking() | self._create_first_picking()
        pickings.invalidate_recordset(["is_transit_transfer", "sub_location_existent"])
        self.assertEqual(pickings.mapped("is_transit_transfer"), [True, True])
        self.assertEqual(pickings.mapped("sub_location_existent"), [False, False])

    def test_second_transfer_without_rights_on_destination(self):
        # ticket 8970: the operator validating the first leg may not see the
        # operation types of the receiving warehouse
        user = self.env["res.users"].create(
            {
                "name": "Transit Operator",
                "login": "transit_operator",
                "group_ids": [(6, 0, [self.env.ref("stock.group_stock_user").id])],
            }
        )
        self.env["ir.access"].create(
            [
                {
                    "name": "Transit operator: source warehouse operation types only",
                    "model_id": self.env.ref("stock.model_stock_picking_type").id,
                    "operation": "r",
                    "domain": f"[('warehouse_id', '=', {self.warehouse.id})]",
                },
                {
                    "name": "Transit operator: create transfers in source warehouse only",
                    "model_id": self.env.ref("stock.model_stock_picking").id,
                    "operation": "c",
                    "domain": f"[('picking_type_id.warehouse_id', '=', {self.warehouse.id})]",
                },
            ]
        )
        self.delivery_type.auto_second_transfer = True
        picking = self._create_first_picking().with_user(user)
        picking.button_validate()
        self.assertEqual(picking.state, "done")

        second = self._second_picking(picking).sudo()
        self.assertEqual(len(second), 1)
        self.assertEqual(second.picking_type_id, self.reception_type)
        self.assertEqual(second.move_ids.product_uom_qty, 4)

    def _process_backorder(self, action):
        # the native backorder confirmation, "Create Backorder"
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "stock.backorder.confirmation")
        wizard = Form(self.env["stock.backorder.confirmation"].with_context(**action["context"])).save()
        wizard.process()

    def test_partial_delivery_backorder_keeps_receiving_leg_executable(self):
        # TRANSIT-004: A delivered, B wholly left for a backorder
        self.delivery_type.auto_second_transfer = True
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.delivery_type.id,
                "partner_id": self.dest_partner.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.transit_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 4,
                            "location_id": self.warehouse.lot_stock_id.id,
                            "location_dest_id": self.transit_location.id,
                        },
                    )
                    for product in (self.product, self.other_product)
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        move_a = picking.move_ids.filtered(lambda m: m.product_id == self.product)
        move_a.quantity = 4
        move_a.picked = True
        self._process_backorder(picking.button_validate())

        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.move_ids.product_id, self.product)
        source_backorder = picking.backorder_ids
        self.assertEqual(len(source_backorder), 1)
        self.assertEqual(source_backorder.move_ids.product_id, self.other_product)
        # the pending products are already in the receiving leg: no second reception for the backorder
        self.assertTrue(source_backorder.second_transfer_created)

        reception = self._second_picking(picking)
        self.assertEqual(len(reception), 1)
        self.assertIn(reception.name, "".join(source_backorder.message_ids.mapped("body")))
        self.assertEqual(reception.move_ids.product_id, self.product | self.other_product)

        # receive A, leave B for a reception backorder: B now comes from the source backorder
        reception.action_assign()
        reception_a = reception.move_ids.filtered(lambda m: m.product_id == self.product)
        reception_a.quantity = 4
        reception_a.picked = True
        self._process_backorder(reception.button_validate())
        self.assertEqual(reception.state, "done")
        reception_backorder = reception.backorder_ids
        self.assertEqual(reception_backorder.move_ids.product_id, self.other_product)
        self.assertEqual(reception_backorder.source_transfer_id, picking)

        # ship B, then receive it: the whole flow completes
        self.env["stock.quant"]._update_available_quantity(self.other_product, self.warehouse.lot_stock_id, 4)
        source_backorder.action_assign()
        source_backorder.move_ids.quantity = 4
        source_backorder.move_ids.picked = True
        source_backorder.button_validate()
        self.assertEqual(source_backorder.state, "done")
        self.assertFalse(self._second_picking(source_backorder))

        reception_backorder.action_assign()
        reception_backorder.move_ids.quantity = 4
        reception_backorder.move_ids.picked = True
        reception_backorder.button_validate()
        self.assertEqual(reception_backorder.state, "done")
