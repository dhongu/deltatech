from odoo.tests import tagged
from odoo.tests.common import TransactionCase

PARAM = "deltatech_putaway_strategy.prefer_existing_stock_location"


@tagged("post_install", "-at_install")
class TestPreferExistingStock(TransactionCase):
    """Produsul a fost mutat fizic pe alt raft, dar regula de putaway a rămas pe raftul vechi."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("deltatech_putaway_strategy.search_sublocation", "False")
        Location = cls.env["stock.location"]
        cls.root = Location.create({"name": "ZONA", "usage": "internal"})
        cls.shelf_old = Location.create(
            {"name": "RAFT VECHI", "usage": "internal", "location_id": cls.root.id, "max_products_leaf": 15}
        )
        cls.shelf_new = Location.create(
            {"name": "RAFT NOU", "usage": "internal", "location_id": cls.root.id, "max_products_leaf": 15}
        )
        cls.shelf_other = Location.create(
            {"name": "RAFT ALTUL", "usage": "internal", "location_id": cls.root.id, "max_products_leaf": 15}
        )
        cls.product = cls.env["product.product"].create({"name": "Covorase test", "is_storable": True})
        cls.env["stock.putaway.rule"].create(
            {
                "product_id": cls.product.id,
                "location_in_id": cls.root.id,
                "location_out_id": cls.shelf_old.id,
                "sequence": 1,
            }
        )
        Quant = cls.env["stock.quant"]
        Quant._update_available_quantity(cls.product, cls.shelf_new, 1.0)
        # marfa recepționată, încă nepusă la raft
        Quant._update_available_quantity(cls.product, cls.root, 5.0)

    def _set_option(self, value):
        self.env["ir.config_parameter"].sudo().set_param(PARAM, value)

    def test_option_off_keeps_rule(self):
        self._set_option("False")
        self.assertEqual(self.root._get_putaway_strategy(self.product, quantity=1), self.shelf_old)

    def test_option_on_prefers_existing_stock(self):
        self._set_option("True")
        self.assertEqual(self.root._get_putaway_strategy(self.product, quantity=1), self.shelf_new)

    def test_largest_quantity_first(self):
        self._set_option("True")
        self.env["stock.quant"]._update_available_quantity(self.product, self.shelf_other, 3.0)
        self.assertEqual(self.root._get_putaway_strategy(self.product, quantity=1), self.shelf_other)

    def test_rule_location_with_stock_wins(self):
        self._set_option("True")
        self.env["stock.quant"]._update_available_quantity(self.product, self.shelf_old, 1.0)
        self.assertEqual(self.root._get_putaway_strategy(self.product, quantity=1), self.shelf_old)

    def test_full_shelf_falls_back_to_rule(self):
        self._set_option("True")
        self.shelf_new.max_products_leaf = 2
        self.assertEqual(self.root._get_putaway_strategy(self.product, quantity=5), self.shelf_old)

    def test_stock_only_on_root_is_ignored(self):
        self._set_option("True")
        product = self.env["product.product"].create({"name": "Doar pe radacina", "is_storable": True})
        self.env["stock.putaway.rule"].create(
            {"product_id": product.id, "location_in_id": self.root.id, "location_out_id": self.shelf_old.id}
        )
        self.env["stock.quant"]._update_available_quantity(product, self.root, 4.0)
        self.assertEqual(self.root._get_putaway_strategy(product, quantity=1), self.shelf_old)

    def test_reserved_stock_is_not_a_destination(self):
        """Stocul care pleacă de pe raft (rezervat) nu face din raft o destinație."""
        self._set_option("True")
        self.env["stock.quant"]._update_reserved_quantity(self.product, self.shelf_new, 1.0)
        self.assertEqual(self.root._get_putaway_strategy(self.product, quantity=1), self.shelf_old)

    def test_excluded_source_is_not_a_destination(self):
        self._set_option("True")
        root = self.root.with_context(putaway_exclude_location_ids=self.shelf_new.ids)
        self.assertEqual(root._get_putaway_strategy(self.product, quantity=1), self.shelf_old)

    def _internal_transfer(self, source, quantity, product=None):
        product = product or self.product
        picking_type = self.env.ref("stock.picking_type_internal")
        picking_type.active = True
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": source.id,
                "location_dest_id": self.root.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": quantity,
                            "product_uom": product.uom_id.id,
                            "location_id": source.id,
                            "location_dest_id": self.root.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        return picking

    def test_internal_transfer_goes_to_existing_shelf(self):
        self._set_option("True")
        # marfa de pe ZONA e mai veche, ca rezervarea FIFO să o ia doar de acolo
        product = self.env["product.product"].create({"name": "Recepție la raft", "is_storable": True})
        self.env["stock.putaway.rule"].create(
            {"product_id": product.id, "location_in_id": self.root.id, "location_out_id": self.shelf_old.id}
        )
        Quant = self.env["stock.quant"]
        Quant._update_available_quantity(product, self.root, 5.0)
        Quant._update_available_quantity(product, self.shelf_new, 1.0)
        picking = self._internal_transfer(self.root, 5.0, product)
        self.assertEqual(picking.move_line_ids.location_id, self.root)
        self.assertEqual(picking.move_line_ids.location_dest_id, self.shelf_new)

    def test_reserved_line_from_shelf_is_not_sent_back(self):
        """Rezervarea din ZONA ia și bucata de pe RAFT NOU: linia aceea nu se întoarce pe RAFT NOU."""
        self._set_option("True")
        picking = self._internal_transfer(self.root, 6.0)
        line_from_shelf = picking.move_line_ids.filtered(lambda ml: ml.location_id == self.shelf_new)
        self.assertTrue(line_from_shelf)
        self.assertEqual(line_from_shelf.location_dest_id, self.shelf_old)

    def test_transfer_from_shelf_is_not_sent_back(self):
        """Un transfer de pe raftul cu stoc nu primește drept destinație chiar raftul-sursă,
        nici când acolo rămâne stoc nerezervat."""
        self._set_option("True")
        self.env["stock.quant"]._update_available_quantity(self.product, self.shelf_new, 2.0)
        picking = self._internal_transfer(self.shelf_new, 1.0)
        self.assertEqual(picking.move_line_ids.location_id, self.shelf_new)
        self.assertEqual(picking.move_line_ids.location_dest_id, self.shelf_old)
