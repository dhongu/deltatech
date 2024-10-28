from odoo.exceptions import UserError
from odoo.tests import common


class TestSaleOrder(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a sale order stage
        self.stage = self.env["sale.order.stage"].create(
            {
                "name": "Test Stage",
                "sequence": 1,
                "confirmed": True,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        # Create a sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "stage_id": self.stage.id,
            }
        )

        # Create a picking type
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "sequence": 1,
                "stage_id": self.stage.id,
                "sequence_code": "TEST",  # Add this line
                "code": "internal",  # Add this line
            }
        )

        # Create a stock picking
        self.stock_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        self.stock_picking.sale_id = self.sale_order

    def test_sale_order_stage_creation(self):
        # Test the creation of a sale order stage
        self.assertEqual(self.stage.name, "Test Stage")
        self.assertEqual(self.stage.sequence, 1)
        self.assertEqual(self.stage.confirmed, True)

    def test_sale_order_creation(self):
        # Test the creation of a sale order
        self.assertEqual(self.sale_order.stage_id, self.stage)

    def test_stock_picking_creation(self):
        # Test the creation of a stock picking
        self.assertEqual(self.stock_picking.sale_id, self.sale_order)
        self.assertEqual(self.stock_picking.picking_type_id, self.picking_type)

    def test_action_done(self):
        # Test the _action_done method
        self.stock_picking._action_done()
        self.assertEqual(self.sale_order.stage_id, self.stage)

    def test_set_stage(self):
        # Test the set_stage method
        self.sale_order.set_stage("confirmed")
        self.assertEqual(self.sale_order.stage_id.confirmed, True)

    def test_write(self):
        # Test the write method
        self.sale_order.write({"stage_id": self.stage.id})
        self.assertEqual(self.sale_order.stage_id, self.stage)

    def test_onchange_stage_id(self):
        # Test the onchange_stage_id method
        self.sale_order.stage_id = self.env["sale.order.stage"].create(
            {
                "name": "Invoiced Stage",
                "invoiced": True,
            }
        )
        self.sale_order.invoice_status = "invoiced"
        with self.assertRaises(UserError):
            self.sale_order.onchange_stage_id()

    def test_action_confirm(self):
        # Test the action_confirm method
        self.sale_order.action_confirm()

    def test_action_quotation_sent(self):
        # Test the action_quotation_sent method
        send_email_stage = self.env["sale.order.stage"].create(
            {
                "name": "Send Email Stage",
                "send_email": True,
            }
        )
        self.sale_order.action_quotation_sent()
        self.assertEqual(self.sale_order.stage_id, send_email_stage)

    def test_compute_stage_ids(self):
        # Test the _compute_stage_ids method
        self.sale_order._compute_stage_ids()
        self.assertEqual(self.sale_order.stage_ids, self.sale_order.stage_id)

    def test_inverse_stage_ids(self):
        # Test the _inverse_stage_ids method
        new_stage = self.env["sale.order.stage"].create(
            {
                "name": "New Stage",
                "sequence": 2,
            }
        )
        self.sale_order.stage_ids = new_stage
        self.sale_order._inverse_stage_ids()
        self.assertEqual(self.sale_order.stage_id, new_stage)
