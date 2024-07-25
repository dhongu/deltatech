from odoo.tests.common import TransactionCase


class TestStockMoveAnalytics(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a test partner
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Create analytic accounts with required fields
        self.analytic_plan = self.env["account.analytic.plan"].create(
            {
                "name": "Test Plan",
            }
        )
        self.analytic_account_source = self.env["account.analytic.account"].create(
            {
                "name": "Source Analytic Account",
                "plan_id": self.analytic_plan.id,
            }
        )
        self.analytic_account_dest = self.env["account.analytic.account"].create(
            {
                "name": "Destination Analytic Account",
                "plan_id": self.analytic_plan.id,
            }
        )

        # Create stock locations with analytic accounts
        self.location_source = self.env["stock.location"].create(
            {
                "name": "Source Location",
                "usage": "internal",
                "analytic_id": self.analytic_account_source.id,
            }
        )
        self.location_dest = self.env["stock.location"].create(
            {
                "name": "Destination Location",
                "usage": "internal",
                "analytic_id": self.analytic_account_dest.id,
            }
        )

        # Create a test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
            }
        )

        # Create a picking type
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Internal Transfers",
                "code": "internal",
                "sequence_code": "INT",
                "warehouse_id": self.env["stock.warehouse"].search([], limit=1).id,
            }
        )

        # Create a stock picking
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
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

    def test_analytic_line_creation(self):
        # Confirm the picking and move to 'done' state
        self.picking.action_confirm()
        self.picking.action_assign()
        for move in self.picking.move_ids:
            move.quantity_done = move.product_uom_qty
        self.picking.button_validate()
