from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPutawayStrategy(TransactionCase):
    def setUp(self):
        super().setUp()
        self.StockLocation = self.env["stock.location"].sudo()
        self.Product = self.env["product.product"].sudo()
        self.Quant = self.env["stock.quant"].sudo()

        # Creează o locație părinte și două frunze interne
        self.parent_loc = self.StockLocation.create(
            {
                "name": "PARENT",
                "usage": "internal",
            }
        )
        self.loc1 = self.StockLocation.create(
            {
                "name": "L1",
                "usage": "internal",
                "location_id": self.parent_loc.id,
                "max_products_leaf": 5,
            }
        )
        self.loc2 = self.StockLocation.create(
            {
                "name": "L2",
                "usage": "internal",
                "location_id": self.parent_loc.id,
                "max_products_leaf": 5,
            }
        )

        # Creează un produs simplu
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        # Ocupă parțial L2 cu 2 bucăți
        self.Quant.create(
            {
                "product_id": self.product.id,
                "location_id": self.loc2.id,
                "quantity": 2.0,
            }
        )

    def test_check_can_be_used_capacity(self):
        # L1: max 5, curent 0 -> 5 e permis, 6 nu
        self.assertTrue(self.loc1._check_can_be_used(self.product, quantity=5))
        self.assertFalse(self.loc1._check_can_be_used(self.product, quantity=6))

        # L2: max 5, curent 2 -> +1 permis, +4 nu
        self.assertTrue(self.loc2._check_can_be_used(self.product, quantity=1))
        self.assertFalse(self.loc2._check_can_be_used(self.product, quantity=4))

    def test_get_putaway_prefers_empty_child(self):
        # Putaway pe părinte cu qty 1 ar trebui să aleagă L1 (goală) înaintea lui L2 (ocupată)
        dest = self.parent_loc._get_putaway_strategy(self.product, quantity=1)
        self.assertEqual(dest.id, self.loc1.id)
