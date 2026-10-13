# ©  2008-2023 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_category = cls.env["product.category"].create({"name": "Test Category"})
        cls.product_category_2 = cls.env["product.category"].create({"name": "Test Category 2"})

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "categ_id": cls.product_category.id,
                "is_storable": True,
                "list_price": 100.0,
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Test Product 2",
                "categ_id": cls.product_category_2.id,
                "is_storable": True,
            }
        )

        cls.stock_picking = cls.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
            }
        )

    def _add_move_line(self, product):
        return self.env["stock.move.line"].create(
            {
                "product_id": product.id,
                "product_uom_id": product.uom_id.id,
                "picking_id": self.stock_picking.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "quantity": 10.0,
            }
        )

    def test_category_color_default(self):
        self.assertTrue(1 <= self.product_category.color <= 11, "Default color index should be between 1 and 11")
        self.product_category.color = 5
        self.assertEqual(self.product_category.color, 5)

    def test_compute_categ_ids(self):
        self.assertFalse(self.stock_picking.categ_ids, "Picking without lines has no category")

        self._add_move_line(self.product)
        self.assertEqual(
            self.stock_picking.categ_ids,
            self.product_category,
            "Computed category should match product's category",
        )

        # same category twice + a second category: categories are not duplicated
        self._add_move_line(self.product)
        self._add_move_line(self.product_2)
        self.assertEqual(self.stock_picking.categ_ids, self.product_category | self.product_category_2)

    def _add_move(self, product):
        return self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": 5.0,
                "picking_id": self.stock_picking.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )

    def test_categ_ids_from_unreserved_moves(self):
        """Transfers that are not reserved yet have moves but no move lines"""
        move = self._add_move(self.product)
        self.assertFalse(self.stock_picking.move_line_ids)
        self.assertEqual(self.stock_picking.categ_ids, self.product_category)

        move_2 = self._add_move(self.product_2)
        self.assertEqual(self.stock_picking.categ_ids, self.product_category | self.product_category_2)

        # cancelled moves do not count
        move_2._action_cancel()
        self.assertEqual(self.stock_picking.categ_ids, self.product_category)

        # a product category change is reflected
        move.product_id.categ_id = self.product_category_2
        self.assertEqual(self.stock_picking.categ_ids, self.product_category_2)

    def test_kanban_view_loads(self):
        arch = self.env["stock.picking"].get_view(self.env.ref("stock.stock_picking_kanban").id, "kanban")["arch"]
        self.assertIn('name="categ_ids"', arch)
        arch = self.env["product.category"].get_view(self.env.ref("product.product_category_form_view").id, "form")[
            "arch"
        ]
        self.assertIn('name="color"', arch)
