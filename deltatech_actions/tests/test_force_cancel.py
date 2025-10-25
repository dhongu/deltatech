# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestForceCancelOrderAndMoves(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Basic records
        cls.partner = cls.env["res.partner"].create({"name": "Customer A"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product A",
                "is_storable": True,
                "lst_price": 10.0,
            }
        )
        # Create sale order without running the whole confirmation flow
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "state": "sale",  # set state directly to match method precondition
            }
        )
        cls.group = cls.env["procurement.group"].create({"name": "SO Group"})
        cls.so.procurement_group_id = cls.group.id

        # Create a picking linked to the sale order via group
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "group_id": cls.group.id,
                "sale_id": cls.so.id,
            }
        )
        # Minimal move and move line under the picking
        cls.move = cls.env["stock.move"].create(
            {
                "name": "Move A",
                "product_id": cls.product.id,
                "product_uom": cls.product.uom_id.id,
                "product_uom_qty": 1.0,
                "location_id": cls.picking.location_id.id,
                "location_dest_id": cls.picking.location_dest_id.id,
                "picking_id": cls.picking.id,
            }
        )
        cls.move_line = cls.env["stock.move.line"].create(
            {
                "move_id": cls.move.id,
                "product_id": cls.product.id,
                "product_uom_id": cls.product.uom_id.id,
                "qty_done": 0.0,
                "location_id": cls.picking.location_id.id,
                "location_dest_id": cls.picking.location_dest_id.id,
                "picking_id": cls.picking.id,
            }
        )

        # Add a dummy PDF attachment on picking to ensure unlink pathways don't error if any
        cls.env["ir.attachment"].create(
            {
                "name": "PICK_0001.pdf",
                "res_model": "stock.picking",
                "res_id": cls.picking.id,
                "type": "binary",
                "datas": base64.b64encode(b"content"),
                "mimetype": "application/pdf",
            }
        )

    def test_force_cancel(self):
        self.assertTrue(self.so.picking_ids, "Precondition: sale order should have related picking")
        # Call the method under test
        self.so.force_cancel_order_and_moves()

        # Assertions: all states should be 'cancel'
        self.assertEqual(self.so.state, "cancel")
        self.assertTrue(all(p.state == "cancel" for p in self.so.picking_ids))
        self.assertTrue(all(m.state == "cancel" for m in self.so.picking_ids.move_ids))
        self.assertTrue(all(ml.state == "cancel" for ml in self.so.picking_ids.move_ids.move_line_ids))
