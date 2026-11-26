# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWishlistQtyAvailable(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse_a = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.warehouse_b = cls.env["stock.warehouse"].create({"name": "Wishlist WH B", "code": "WLB"})
        cls.product_1 = cls.env["product.product"].create({"name": "Wishlist product 1", "is_storable": True})
        cls.product_2 = cls.env["product.product"].create({"name": "Wishlist product 2", "is_storable": True})
        quant = cls.env["stock.quant"]
        quant._update_available_quantity(cls.product_1, cls.warehouse_a.lot_stock_id, 5.0)
        quant._update_available_quantity(cls.product_2, cls.warehouse_a.lot_stock_id, 7.0)
        cls.website = cls.env["website"].search([], limit=1) or cls.env["website"].create({"name": "Test"})
        cls.item = cls.env["product.wishlist"].create(
            {
                "product_id": cls.product_1.id,
                "partner_id": cls.env.user.partner_id.id,
                "website_id": cls.website.id,
            }
        )

    def test_qty_follows_warehouse_context(self):
        item_a = self.item.with_context(warehouse_id=self.warehouse_a.id)
        item_b = self.item.with_context(warehouse_id=self.warehouse_b.id)
        self.assertEqual(item_a.qty_available, 5.0)
        # same record, same cache, other warehouse: must not reuse warehouse A's value
        self.assertEqual(item_b.qty_available, 0.0)
        self.assertEqual(item_b.qty_available, item_b.product_id.qty_available)

    def test_qty_follows_product_change(self):
        item = self.item.with_context(warehouse_id=self.warehouse_a.id)
        self.assertEqual(item.qty_available, 5.0)
        item.product_id = self.product_2
        self.assertEqual(item.qty_available, 7.0)

    def test_qty_follows_stock_change(self):
        item = self.item.with_context(warehouse_id=self.warehouse_a.id)
        self.assertEqual(item.qty_available, 5.0)
        # receive 3 more units through a done stock move (the dependency native qty_available relies on)
        move = self.env["stock.move"].create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 3.0,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.warehouse_a.lot_stock_id.id,
            }
        )
        move._action_confirm()
        move.quantity = 3.0
        move.picked = True
        move._action_done()
        self.assertEqual(item.qty_available, 8.0)
