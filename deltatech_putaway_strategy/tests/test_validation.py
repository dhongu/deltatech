from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "validation")
class TestPutawayValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.StockLocation = self.env["stock.location"].sudo()
        self.Product = self.env["product.product"].sudo()
        self.Picking = self.env["stock.picking"].sudo()
        self.Move = self.env["stock.move"].sudo()

        # Creează o locație frunză cu capacitate limitată
        self.loc1 = self.StockLocation.create(
            {
                "name": "Validation L1",
                "usage": "internal",
                "max_products_leaf": 5,
            }
        )

        self.product = self.Product.create(
            {
                "name": "Validation Product",
                "is_storable": True,
            }
        )

        self.supplier_loc = self.env.ref("stock.stock_location_suppliers")
        self.picking_type = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)
        if not self.picking_type:
            self.picking_type = self.env.ref("stock.picking_type_in")

    def test_action_done_validation_fails(self):
        """Testează dacă validarea capacității aruncă o eroare la _action_done."""
        picking = self.Picking.create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.supplier_loc.id,
                "location_dest_id": self.loc1.id,
            }
        )

        move = self.Move.create(
            {
                "name": "Test Move Fail",
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.supplier_loc.id,
                "location_dest_id": self.loc1.id,
            }
        )

        picking.action_confirm()
        picking.action_assign()

        for line in move.move_line_ids:
            line.quantity = 10

        with self.assertRaises(UserError):
            picking.button_validate()
