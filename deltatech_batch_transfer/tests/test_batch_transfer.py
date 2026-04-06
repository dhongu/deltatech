from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBatchTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({"group_ids": [(4, cls.env.ref("stock.group_stock_user").id)]})
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.location_dest = cls.env.ref("stock.stock_location_customers")

    def test_batch_transfer(self):
        picking_1 = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.picking_type.default_location_src_id.id,
                "location_dest_id": self.location_dest.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_1.id,
                "location_id": picking_1.location_id.id,
                "location_dest_id": picking_1.location_dest_id.id,
            }
        )
        picking_1.action_confirm()

        batch = self.env["stock.picking.batch"].create(
            {
                "picking_ids": [(4, picking_1.id)],
            }
        )
        self.assertEqual(batch.state, "draft")
        batch.action_confirm()
        self.assertEqual(batch.state, "in_progress")

        # Set quantity to 0 explicitly if needed, though by default it should be 0
        move.quantity = 0.0

        # Test action_done logic
        # If no quantity is set, it should remove the picking from the batch
        batch.action_done()
        self.assertFalse(picking_1.batch_id)
        # In Odoo 19, if all pickings are removed, the batch might be cancelled or stay in progress/done
        # Based on my observation, it becomes 'cancel'
        self.assertEqual(batch.state, "cancel")
