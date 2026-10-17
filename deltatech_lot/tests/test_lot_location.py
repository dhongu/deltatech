from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestLotLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Lot Location Product",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.location_a = cls.env["stock.location"].create(
            {"name": "Lot Loc A", "usage": "internal", "location_id": warehouse.lot_stock_id.id}
        )
        cls.location_b = cls.env["stock.location"].create(
            {"name": "Lot Loc B", "usage": "internal", "location_id": warehouse.lot_stock_id.id}
        )
        cls.lot = cls.env["stock.lot"].create({"name": "LOTLOC001", "product_id": cls.product.id})
        cls.Quant = cls.env["stock.quant"]

    def _update(self, location, quantity, owner=None):
        self.Quant._update_available_quantity(self.product, location, quantity, lot_id=self.lot, owner_id=owner)

    def test_location_refreshed_when_quant_quantity_changes(self):
        """The stored lot location follows quantity changes on existing quants (#3395)."""
        self._update(self.location_a, 10)
        self._update(self.location_b, 5)
        self.assertFalse(self.lot.location_id, "Lot is in two locations")
        # Empty location B: quant B still exists, only its quantity changes
        self._update(self.location_b, -5)
        self.assertEqual(self.lot.location_id, self.location_a)
        # Empty location A too: no positive stock left
        self._update(self.location_a, -10)
        self.assertFalse(self.lot.location_id)

    def test_location_kept_with_several_quants_in_one_location(self):
        """Quants split by owner in the same location keep the lot location (#3396)."""
        owner = self.env["res.partner"].create({"name": "Lot Owner"})
        self._update(self.location_a, 10)
        self._update(self.location_a, 3, owner=owner)
        positive = self.lot.quant_ids.filtered(lambda q: q.quantity > 0)
        self.assertEqual(len(positive), 2)
        self.assertEqual(self.lot.location_id, self.location_a)
