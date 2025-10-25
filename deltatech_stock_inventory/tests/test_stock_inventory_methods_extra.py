# © 2015-2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

autoinstall = False


class TestStockInventoryMethodsExtra(TransactionCase):
    def setUp(self):
        super().setUp()
        # Company, locations and product
        self.company = self.env.user.company_id
        self.location = self.env["stock.location"].create({"name": "LOC/EXTRA", "usage": "internal"})
        self.product = self.env["product.product"].create(
            {
                "name": "Extra Prod",
                "is_storable": True,
                "standard_price": 3.5,
            }
        )
        # Seed quants so that _get_quantities finds something
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "quantity": 5.0,
            }
        )
        # Build a draft inventory with location
        self.inventory = self.env["stock.inventory"].create(
            {
                "name": "INV/EXTRA",
                "location_ids": [(6, 0, [self.location.id])],
                "company_id": self.company.id,
            }
        )

    def test_action_open_and_related_actions_and_print(self):
        # Start inventory to have lines
        self.inventory.action_start()
        # action_open_inventory_lines returns an action dict with domain/context
        act = self.inventory.action_open_inventory_lines()
        self.assertIsInstance(act, dict)
        self.assertEqual(act.get("res_model"), "stock.inventory.line")
        self.assertIn("domain", act)
        # view related move lines (no moves yet)
        act2 = self.inventory.action_view_related_move_lines()
        self.assertEqual(act2.get("res_model"), "stock.move.line")
        # printing should return an action dict (report)
        act3 = self.inventory.action_print()
        self.assertIsInstance(act3, dict)

    def test_get_quantities_and_inventory_lines_values(self):
        quants = self.inventory._get_quantities()
        # _read_group returns a list of tuples-like groups in this customization
        self.assertTrue(quants, "Quants should be grouped for provided location")
        # Also test exhausted lines gathering
        non_exhausted = set()
        vals_exh = self.inventory._get_exhausted_inventory_lines_vals(non_exhausted)
        self.assertIsInstance(vals_exh, list)
        # Start to generate real lines and inspect values
        self.inventory.action_start()
        vals = self.inventory._get_inventory_lines_values()
        self.assertIsInstance(vals, list)
        self.assertTrue(any(v.get("product_id") == self.product.id for v in vals))

    def test_action_check_and_validate_flow(self):
        self.inventory.action_start()
        # Write a difference on one line to force move generation on validate
        line = self.inventory.line_ids.filtered(lambda l: l.product_id == self.product)[:1]
        # Ensure there is at least one line, otherwise create it explicitly
        if not line:
            line = self.env["stock.inventory.line"].create(
                {
                    "inventory_id": self.inventory.id,
                    "product_id": self.product.id,
                    "location_id": self.location.id,
                    "product_qty": 10.0,
                }
            )
        else:
            line.product_qty = line.theoretical_qty + 2.0
        # action_check should prepare moves without raising
        self.inventory.action_check()
        # Validate complete flow
        self.inventory.action_validate()
        self.assertEqual(self.inventory.state, "done")
        # post_inventory should be idempotent and return True
        self.assertTrue(self.inventory.post_inventory())

    def test_inventory_line_domains_and_computes(self):
        self.inventory.action_start()
        line = self.inventory.line_ids[:1]
        # Domain helpers should return strings
        self.assertIsInstance(self.env["stock.inventory.line"]._domain_location_id(), str)
        self.assertIsInstance(self.env["stock.inventory.line"]._domain_product_id(), str)
        # compute difference
        prev = line.difference_qty
        line.product_qty = (line.theoretical_qty or 0.0) + 1.0
        line._compute_difference()
        self.assertNotEqual(line.difference_qty, prev)
        # is_editable depends on state confirm/done
        self.assertTrue(line.is_editable)
        self.inventory.action_validate()

        # price editable flag follows parameter
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("stock.use_inventory_price", "True")
        line._compute_is_price_editable()
        self.assertTrue(line.is_price_editable)
        ICP.set_param("stock.use_inventory_price", "False")
        line._compute_is_price_editable()
        self.assertFalse(line.is_price_editable)

    def test_write_updates_quant_and_duplicate_check(self):
        self.inventory.action_start()
        # Ensure a single quant exists for the line to test write logic
        line = self.inventory.line_ids.filtered(lambda l: l.product_id == self.product)[:1]
        # Before write, ensure only one quant
        quants = line.get_quants(create=True)
        self.assertTrue(quants)
        # Update product_qty and ensure quant inventory_quantity follows
        new_qty = (line.product_qty or 0.0) + 1.0
        line.write({"product_qty": new_qty})
        self.assertEqual(quants.inventory_quantity, new_qty)
        # Duplicate line should raise
        with self.assertRaises(UserError):
            self.env["stock.inventory.line"].create(
                {
                    "inventory_id": line.inventory_id.id,
                    "product_id": line.product_id.id,
                    "location_id": line.location_id.id,
                }
            )

    def test_non_storable_product_is_rejected(self):
        self.inventory.action_start()
        service = self.env["product.product"].create({"name": "Service", "is_storable": False})
        with self.assertRaises(ValidationError):
            self.env["stock.inventory.line"].create(
                {"inventory_id": self.inventory.id, "product_id": service.id, "location_id": self.location.id}
            )

    def test_move_value_helpers_and_generate_moves(self):
        self.inventory.action_start()
        line = self.inventory.line_ids.filtered(lambda l: l.product_id == self.product)[:1]
        # Induce a positive difference to generate an inbound move
        line.product_qty = (line.theoretical_qty or 0.0) + 2.0
        vals = line._get_move_values(1.0, line.location_id.id, line.location_id.id, out=False)
        self.assertIsInstance(vals, dict)
        moves = line._generate_moves()
        self.assertTrue(moves, "_generate_moves should create stock.move records when there is a difference")

    def test_refresh_and_reset_and_search_helpers(self):
        self.inventory.action_start()
        line = self.inventory.line_ids.filtered(lambda l: l.product_id == self.product)[:1]
        # Force outdated by changing theoretical compared to quants
        line.theoretical_qty = (line.theoretical_qty or 0.0) + 1.0
        line._compute_outdated()
        # Now refresh should recompute theoretical back to sum(quants)
        self.assertTrue(line.outdated)
        self.env.invalidate_all()
        # In tests, committing the cursor is forbidden; flush changes instead
        self.env.flush_all()
        line.action_refresh_quantity()
        self.assertFalse(line.outdated or (line.theoretical_qty is None))
        # Reset product qty
        line.product_qty = 7.5
        line.action_reset_product_qty()
        self.assertEqual(line.product_qty, 0)
        # Search helpers: with proper context
        ctx = dict(default_inventory_id=self.inventory.id)
        # '=' should return lines where difference equals 0
        self.env["stock.inventory.line"].with_context(**ctx).search([["difference_qty", "=", True]])

        # '!=' should return lines where difference is not zero
        # Set a difference
        line.product_qty = (line.theoretical_qty or 0.0) + 3.0
        res_ne = self.env["stock.inventory.line"].with_context(**ctx).search([["difference_qty", "!=", True]])
        self.assertTrue(res_ne)
        # outdated search
        res_out = self.env["stock.inventory.line"].with_context(**ctx).search([["outdated", "=", False]])
        self.assertTrue(res_out)

    def test_virtual_location_and_create_inventory_moves(self):
        self.inventory.action_start()
        line = self.inventory.line_ids.filtered(lambda l: l.product_id == self.product)[:1]
        virt_loc = line._get_virtual_location()
        self.assertTrue(virt_loc)
        # Create explicit dummy moves via helpers
        move_out = line.create_inventory_out_move(svl_qty=1.0)
        self.assertEqual(move_out.state, "done")
        move_in = line.create_inventory_in_move()
        self.assertEqual(move_in.state, "done")
