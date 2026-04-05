from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAvoidPutaway(TransactionCase):
    def setUp(self):
        super().setUp()
        self.StockLocation = self.env["stock.location"].sudo()
        self.Product = self.env["product.product"].sudo()

        # Creează o locație părinte și o locație destinație (putaway)
        self.parent_loc = self.StockLocation.create(
            {
                "name": "PARENT",
                "usage": "internal",
            }
        )
        self.putaway_loc = self.StockLocation.create(
            {
                "name": "PUTAWAY",
                "usage": "internal",
                "location_id": self.parent_loc.id,
            }
        )

        # Creează un produs
        self.product = self.Product.create(
            {
                "name": "Test Avoid Putaway Product",
                "is_storable": True,
            }
        )

        # Regulă de putaway: PARENT -> PUTAWAY
        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product.id,
                "location_in_id": self.parent_loc.id,
                "location_out_id": self.putaway_loc.id,
            }
        )

        # Tip de operație
        self.picking_type = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)
        if not self.picking_type:
            self.picking_type = self.env.ref("stock.picking_type_in")

        self.supplier_location = self.env.ref("stock.stock_location_suppliers")

    def test_avoid_putaway_rules_false(self):
        """Verifică dacă putaway se aplică normal când avoid_putaway_rules este False."""
        self.picking_type.avoid_putaway_rules = False

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()

        self.assertEqual(
            move.move_line_ids[0].location_dest_id.id,
            self.putaway_loc.id,
            "Strategia de putaway ar fi trebuit să se aplice.",
        )

    def test_avoid_putaway_rules_true(self):
        """Verifică dacă putaway este evitat când avoid_putaway_rules este True."""
        self.picking_type.avoid_putaway_rules = True

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": "Test Move Avoid",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()

        self.assertEqual(
            move.move_line_ids[0].location_dest_id.id,
            self.parent_loc.id,
            "Strategia de putaway ar fi trebuit să fie evitată.",
        )
