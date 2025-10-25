# © 2015-2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProductMethods(TransactionCase):
    def setUp(self):
        super().setUp()
        # Use the main demo warehouse that always exists
        self.warehouse = self.env.ref("stock.warehouse0")
        self.stock_location = self.warehouse.lot_stock_id

        # Prepare a hierarchical location under warehouse stock: ROW/RACK
        self.row_loc = self.env["stock.location"].create(
            {
                "name": "R1",
                "usage": "internal",
                "location_id": self.stock_location.id,
            }
        )
        self.rack_loc = self.env["stock.location"].create(
            {
                "name": "A1",
                "usage": "internal",
                "location_id": self.row_loc.id,
            }
        )

        # Create a storable product and some stock at the warehouse stock location
        self.product = self.env["product.product"].create(
            {
                "name": "Prod Methods",
                "is_storable": True,
                "standard_price": 5.0,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 8.0,
            }
        )

        # Configure product template warehouse location mapping
        self.env["product.warehouse.location"].create(
            {
                "product_id": self.product.product_tmpl_id.id,
                "warehouse_id": self.warehouse.id,
                "loc_row": "R1",
                "loc_rack": "A1",
            }
        )

    def test_get_theoretical_quantity_basic_and_uom(self):
        # Basic theoretical quantity from stock location
        qty = self.env["product.product"].get_theoretical_quantity(self.product.id, self.stock_location.id)
        self.assertEqual(qty, 8.0)

        # With UoM conversion to dozen (if present)
        try:
            dozen_uom = self.env.ref("uom.product_uom_dozen")
        except Exception:
            dozen_uom = False
        if dozen_uom:
            qty_doz = self.env["product.product"].get_theoretical_quantity(
                self.product.id, self.stock_location.id, to_uom=dozen_uom.id
            )
            self.assertAlmostEqual(qty_doz, 8.0 / 12.0, places=2)

    def test_get_location_and_putaway_rules(self):
        # get_location should resolve to the rack location we created
        loc = self.product.product_tmpl_id.get_location()
        self.assertEqual(loc, self.rack_loc)

        # No putaway rules initially
        rules_before = self.env["stock.putaway.rule"].search([("product_id", "=", self.product.id)])
        self.assertFalse(rules_before)

        # Create putaway rules based on product's configured location
        self.product.product_tmpl_id.create_putaway_rule()
        rules = self.env["stock.putaway.rule"].search([("product_id", "=", self.product.id)])
        self.assertTrue(rules)
        self.assertEqual(rules.location_in_id, self.stock_location)
        self.assertEqual(rules.location_out_id, self.rack_loc)

    def test_move_to_putaway_location_creates_done_picking(self):
        # Ensure putaway rules exist
        self.product.product_tmpl_id.create_putaway_rule()

        # Move to putaway location should create a completed internal picking moving all available quants
        picking = self.product.product_tmpl_id.move_to_putaway_location()
        self.assertTrue(picking)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.picking_type_id.code, "internal")
        # Single product variant moved with expected quantity
        move = picking.move_ids.filtered(lambda m: m.product_id == self.product)
        self.assertTrue(move)
        self.assertEqual(move.product_uom_qty, 8.0)
        self.assertEqual(move.location_id, self.stock_location)
        self.assertEqual(move.location_dest_id, self.rack_loc)

    def test_compute_and_inverse_loc(self):
        # Update loc fields with warehouse context; inverse should write product.warehouse.location
        tmpl = self.product.product_tmpl_id.with_context(warehouse=self.warehouse.id)
        tmpl.loc_row = "R1"
        tmpl.loc_rack = "A1"
        tmpl.loc_case = "C1"
        tmpl.loc_shelf = "S1"

        # Verify the mapping record was created/updated
        mapping = self.env["product.warehouse.location"].search(
            [
                ("product_id", "=", tmpl.id),
                ("warehouse_id", "=", self.warehouse.id),
            ],
            limit=1,
        )
        self.assertTrue(mapping)
        self.assertEqual(mapping.loc_row, "R1")
        self.assertEqual(mapping.loc_rack, "A1")
        self.assertEqual(mapping.loc_case, "C1")
        self.assertEqual(mapping.loc_shelf, "S1")

        # Now compute should read back these values
        tmpl2 = self.env["product.template"].browse(tmpl.id).with_context(warehouse=self.warehouse.id)
        tmpl2._compute_loc()
        self.assertEqual(tmpl2.loc_row, "R1")
        self.assertEqual(tmpl2.loc_rack, "A1")
        self.assertEqual(tmpl2.loc_case, "C1")
        self.assertEqual(tmpl2.loc_shelf, "S1")

    def test_variants_is_ok(self):
        tmpl = self.product.product_tmpl_id
        # default False
        self.assertFalse(tmpl.variants_is_ok())
        # Set the single variant to True
        self.product.is_inventory_ok = True
        self.assertTrue(tmpl.variants_is_ok())
