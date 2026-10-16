from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCapacityIssues(TransactionCase):
    """Regresii pentru #3442 (raft complet plin), #3443 (unități de măsură diferite)
    și #3444 (excluderea rădăcinii la rezervare fără module nedeclarate)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Location = cls.env["stock.location"].sudo()
        cls.parent_loc = Location.create({"name": "CAP-PARENT", "usage": "internal"})
        cls.loc1 = Location.create(
            {"name": "CAP-L1", "usage": "internal", "location_id": cls.parent_loc.id, "max_products_leaf": 5}
        )
        cls.loc2 = Location.create(
            {"name": "CAP-L2", "usage": "internal", "location_id": cls.parent_loc.id, "max_products_leaf": 5}
        )
        cls.product = cls.env["product.product"].sudo().create({"name": "Cap Product", "is_storable": True})
        cls.filler = cls.env["product.product"].sudo().create({"name": "Cap Filler", "is_storable": True})
        cls.supplier_loc = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.in_type = cls.env.ref("stock.picking_type_in")
        cls.dozen = cls.env.ref("uom.product_uom_dozen")
        cls.env["ir.config_parameter"].sudo().set_param("deltatech_putaway_strategy.search_sublocation", "True")

    def _receipt(self, dest, qty, uom=None):
        picking = (
            self.env["stock.picking"]
            .sudo()
            .create(
                {
                    "picking_type_id": self.in_type.id,
                    "location_id": self.supplier_loc.id,
                    "location_dest_id": dest.id,
                }
            )
        )
        self.env["stock.move"].sudo().create(
            {
                "product_id": self.product.id,
                "product_uom": (uom or self.product.uom_id).id,
                "product_uom_qty": qty,
                "picking_id": picking.id,
                "location_id": self.supplier_loc.id,
                "location_dest_id": dest.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        return picking

    # --- #3442 -------------------------------------------------------------------------

    def test_completely_full_leaf_is_rerouted(self):
        """Un raft plin exact la capacitate nu trebuie să păstreze o linie cu cantitate pozitivă."""
        self.env["stock.quant"].sudo()._update_available_quantity(self.filler, self.loc1, 5)
        picking = self._receipt(self.parent_loc, 3)
        line = picking.move_line_ids
        self.assertEqual(len(line), 1)
        # Simulăm o linie rămasă pe raftul plin (ex. aleasă înainte ca raftul să se umple).
        line.location_dest_id = self.loc1

        is_split, _to_reprocess = line._split_by_putaway_capacity()

        self.assertTrue(is_split, "Linia de pe raftul plin trebuie redirecționată")
        lines = picking.move_ids.move_line_ids.filtered(lambda ml: ml.quantity)
        self.assertNotIn(self.loc1, lines.location_dest_id)
        self.assertEqual(lines.location_dest_id, self.loc2)
        self.assertEqual(sum(lines.mapped("quantity")), 3)

    def test_full_leaf_without_alternative_does_not_loop(self):
        """Fără alt raft liber, linia rămâne, dar rezervarea nu intră în buclă infinită."""
        self.env["stock.quant"].sudo()._update_available_quantity(self.filler, self.loc1, 5)
        picking = self._receipt(self.loc1, 3)
        self.assertEqual(sum(picking.move_ids.move_line_ids.mapped("quantity")), 3)

    def test_validation_checks_line_destinations(self):
        """Mișcarea are ca destinație părintele; depășirea pe raftul liniei blochează validarea."""
        picking = self._receipt(self.parent_loc, 7)
        picking.move_line_ids.unlink()
        self.env["stock.move.line"].sudo().create(
            {
                "move_id": picking.move_ids.id,
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.supplier_loc.id,
                "location_dest_id": self.loc1.id,
                "quantity": 7,
            }
        )
        picking.move_ids.picked = True
        with self.assertRaises(UserError):
            picking.with_context(skip_backorder=True).button_validate()

    # --- #3443 -------------------------------------------------------------------------

    def test_planned_quantity_in_product_unit(self):
        """O duzină planificată ocupă 12 bucăți, nu 1."""
        big = (
            self.env["stock.location"].sudo().create({"name": "CAP-BIG", "usage": "internal", "max_products_leaf": 100})
        )
        picking = self._receipt(big, 1, uom=self.dozen)
        self.assertEqual(picking.move_line_ids.product_uom_id, self.dozen)
        big.invalidate_recordset(["planned_products"])
        self.assertEqual(big.planned_products, 12)

    def test_split_converts_capacity_to_line_unit(self):
        """O duzină (12 buc.) nu încape întreagă pe un raft de 5 bucăți."""
        picking = self._receipt(self.parent_loc, 1, uom=self.dozen)
        by_loc = {}
        for ml in picking.move_ids.move_line_ids.filtered(lambda ml: ml.quantity):
            by_loc[ml.location_dest_id] = by_loc.get(ml.location_dest_id, 0) + ml.quantity_product_uom
        for loc in (self.loc1, self.loc2):
            self.assertLessEqual(by_loc.get(loc, 0), 5.0, f"{loc.name} primește peste capacitate: {by_loc}")
        self.assertAlmostEqual(sum(by_loc.values()), 12, places=1)

    # --- #3444 -------------------------------------------------------------------------

    def test_avoid_root_without_removal_priority(self):
        """Opțiunea exclude rădăcina din rezervare doar cu dependențele declarate (fără patch)."""
        Quant = self.env["stock.quant"].sudo()
        root = self.env["stock.location"].sudo().create({"name": "CAP-ROOT", "usage": "internal"})
        shelf = (
            self.env["stock.location"].sudo().create({"name": "CAP-SHELF", "usage": "internal", "location_id": root.id})
        )
        Quant._update_available_quantity(self.product, root, 10)
        Quant._update_available_quantity(self.product, shelf, 10)
        out_type = (
            self.env.ref("stock.picking_type_out")
            .sudo()
            .copy(
                {
                    "name": "Cap Delivery",
                    "default_location_src_id": root.id,
                    "default_location_dest_id": self.customer_loc.id,
                    "avoid_root_location_on_reservation": True,
                }
            )
        )
        picking = (
            self.env["stock.picking"]
            .sudo()
            .create(
                {
                    "picking_type_id": out_type.id,
                    "location_id": root.id,
                    "location_dest_id": self.customer_loc.id,
                }
            )
        )
        self.env["stock.move"].sudo().create(
            {
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 10,
                "picking_id": picking.id,
                "location_id": root.id,
                "location_dest_id": self.customer_loc.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        lines = picking.move_ids.move_line_ids
        self.assertEqual(lines.location_id, shelf)
        self.assertEqual(Quant._get_available_quantity(self.product, root, strict=True), 10)
