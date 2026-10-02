from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingTransitLinked(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.dest_partner = cls.env["res.partner"].create({"name": "Linked Destination Warehouse"})
        cls.dest_warehouse = cls.env["stock.warehouse"].create(
            {"name": "Linked Destination", "code": "LKD", "partner_id": cls.dest_partner.id}
        )
        cls.transit_location = cls.env["stock.location"].create(
            {
                "name": "Linked Transit",
                "usage": "transit",
                "company_id": cls.env.company.id,
                "location_id": cls.env.company.internal_transit_location_id.id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Linked Product", "is_storable": True})
        cls.lot_product = cls.env["product.product"].create(
            {"name": "Linked Lot Product", "is_storable": True, "tracking": "lot"}
        )
        cls.lot_1 = cls.env["stock.lot"].create({"name": "L1", "product_id": cls.lot_product.id})
        cls.lot_2 = cls.env["stock.lot"].create({"name": "L2", "product_id": cls.lot_product.id})
        Quant = cls.env["stock.quant"]
        Quant._update_available_quantity(cls.product, cls.stock_location, 10)
        Quant._update_available_quantity(cls.lot_product, cls.stock_location, 5, lot_id=cls.lot_1)
        # another lot of the same product already waiting in transit
        Quant._update_available_quantity(cls.lot_product, cls.transit_location, 3, lot_id=cls.lot_2)

        cls.delivery_type = cls.env["stock.picking.type"].create(
            {
                "name": "Linked Delivery",
                "code": "internal",
                "sequence_code": "LKO",
                "warehouse_id": cls.warehouse.id,
                "two_step_transfer_use": "delivery",
                "link_second_transfer": True,
                "default_location_src_id": cls.stock_location.id,
                "default_location_dest_id": cls.transit_location.id,
            }
        )
        cls.reception_type = cls.env["stock.picking.type"].create(
            {
                "name": "Linked Reception",
                "code": "internal",
                "sequence_code": "LKI",
                "warehouse_id": cls.dest_warehouse.id,
                "two_step_transfer_use": "reception",
                "default_location_src_id": cls.transit_location.id,
                "default_location_dest_id": cls.dest_warehouse.lot_stock_id.id,
            }
        )

    def _create_first_picking(self, product=None, qty=4, confirm=True):
        product = product or self.product
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.delivery_type.id,
                "partner_id": self.dest_partner.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.transit_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.transit_location.id,
                        },
                    )
                ],
            }
        )
        if confirm:
            picking.action_confirm()
            picking.action_assign()
        return picking

    def _create_second_picking(self, picking):
        wizard = (
            self.env["stock.picking.transfer.wizard"]
            .with_context(active_id=picking.id)
            .create({"operation_id": self.reception_type.id})
        )
        wizard.confirm_transfer()
        return self._second_picking(picking)

    def _second_picking(self, picking):
        return self.env["stock.picking"].search([("source_transfer_id", "=", picking.id)])

    def _validate(self, picking, qty=None, backorder=False):
        if qty is not None:
            picking.move_ids.quantity = qty
        picking.move_ids.picked = True
        if backorder:
            picking = picking.with_context(skip_backorder=True)
        else:
            picking = picking.with_context(skip_backorder=True, picking_ids_not_to_backorder=picking.ids)
        picking.button_validate()

    def test_option_off_keeps_unlinked_copy(self):
        self.delivery_type.link_second_transfer = False
        picking = self._create_first_picking()
        second = self._create_second_picking(picking)
        self.assertFalse(second.linked_to_source_transfer)
        self.assertFalse(second.move_ids.move_orig_ids)
        self.assertEqual(second.move_ids.procure_method, "make_to_stock")

    def test_wizard_before_validation_waits_for_first(self):
        picking = self._create_first_picking(confirm=False)
        second = self._create_second_picking(picking)
        # the draft first transfer is confirmed, not blocked
        self.assertNotEqual(picking.state, "draft")
        self.assertTrue(second.linked_to_source_transfer)
        self.assertEqual(second.move_ids.move_orig_ids, picking.move_ids)
        self.assertEqual(second.move_ids.procure_method, "make_to_order")
        self.assertEqual(second.state, "waiting")

        self._validate(picking, 4)
        self.assertEqual(picking.state, "done")
        self.assertEqual(second.state, "assigned")
        self.assertEqual(second.move_ids.quantity, 4)
        self._validate(second)
        self.assertEqual(second.state, "done")

    def test_wizard_after_validation_reserves_delivered(self):
        picking = self._create_first_picking()
        self._validate(picking, 4)
        second = self._create_second_picking(picking)
        self.assertEqual(second.state, "assigned")
        self.assertEqual(second.move_ids.quantity, 4)

    def test_auto_second_transfer_linked(self):
        self.delivery_type.auto_second_transfer = True
        picking = self._create_first_picking()
        self._validate(picking, 4)
        second = self._second_picking(picking)
        self.assertEqual(second.move_ids.move_orig_ids, picking.move_ids)
        self.assertEqual(second.state, "assigned")
        self._validate(second)
        self.assertEqual(second.state, "done")

    def test_second_cannot_be_validated_before_first(self):
        picking = self._create_first_picking()
        second = self._create_second_picking(picking)
        with self.assertRaisesRegex(UserError, "before the source transfer"):
            self._validate(second, 4)
        self.assertNotEqual(second.state, "done")

    def test_second_cannot_receive_more_than_delivered(self):
        picking = self._create_first_picking()
        second = self._create_second_picking(picking)
        self._validate(picking, 4)
        with self.assertRaisesRegex(UserError, "more than the source transfer"):
            self._validate(second, 5)

    def test_partial_delivery_and_backorders(self):
        picking = self._create_first_picking()
        second = self._create_second_picking(picking)
        self._validate(picking, 2, backorder=True)
        first_backorder = picking.backorder_ids
        self.assertEqual(first_backorder.move_ids.product_uom_qty, 2)
        # only what was delivered is reserved
        self.assertEqual(second.move_ids.quantity, 2)

        self._validate(second, backorder=True)
        self.assertEqual(second.state, "done")
        second_backorder = second.backorder_ids
        self.assertTrue(second_backorder.linked_to_source_transfer)
        self.assertEqual(second_backorder.source_transfer_id, picking)
        # the rest is still in the first transfer's backorder
        with self.assertRaisesRegex(UserError, "more than the source transfer"):
            self._validate(second_backorder, 2)

        self._validate(first_backorder, 2)
        self.assertEqual(second_backorder.move_ids.quantity, 2)
        self._validate(second_backorder)
        self.assertEqual(second_backorder.state, "done")

    def test_second_receives_the_delivered_lot(self):
        self.delivery_type.auto_second_transfer = True
        picking = self._create_first_picking(self.lot_product, 2)
        self.assertEqual(picking.move_line_ids.lot_id, self.lot_1)
        self._validate(picking)
        second = self._second_picking(picking)
        # L2 is also in transit, but only L1 was delivered
        self.assertEqual(second.move_line_ids.lot_id, self.lot_1)
        self.assertEqual(second.move_ids.quantity, 2)

        second.move_line_ids.lot_id = self.lot_2
        with self.assertRaisesRegex(UserError, "more than the source transfer"):
            self._validate(second)

    def test_kit_components_are_linked(self):
        if "mrp.bom" not in self.env:
            self.skipTest("mrp is not installed")
        kit = self.env["product.product"].create({"name": "Linked Kit", "is_storable": True})
        component = self.env["product.product"].create({"name": "Linked Component", "is_storable": True})
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": kit.product_tmpl_id.id,
                "type": "phantom",
                "bom_line_ids": [
                    (0, 0, {"product_id": self.product.id, "product_qty": 1}),
                    (0, 0, {"product_id": component.id, "product_qty": 2}),
                ],
            }
        )
        self.env["stock.quant"]._update_available_quantity(component, self.stock_location, 10)
        picking = self._create_first_picking(kit, 2, confirm=False)
        second = self._create_second_picking(picking)
        self.assertEqual(picking.move_ids.product_id, self.product | component)
        self.assertEqual(second.move_ids.product_id, self.product | component)
        for move in second.move_ids:
            self.assertEqual(move.move_orig_ids.product_id, move.product_id)

        self._validate(picking)
        self.assertEqual(second.state, "assigned")
        self._validate(second)
        self.assertEqual(second.state, "done")
