# ©  2008-2023 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product category for testing
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test Category",
                "complete_name": "Test Category",
            }
        )

        # Create a product with the category
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "categ_id": self.product_category.id,
                "is_storable": True,
                "list_price": 100.0,
            }
        )

        # Create a stock picking with move lines
        self.stock_picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "picking_type_id": self.ref("stock.picking_type_out"),
            }
        )

        self.move_line = self.env["stock.move.line"].create(
            {
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "picking_id": self.stock_picking.id,
                "location_id": self.ref("stock.stock_location_stock"),
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "quantity": 10.0,
                "state": "done",
            }
        )

    def test_compute_categ_ids(self):
        # Trigger the compute method
        self.stock_picking._compute_categ_ids()

        # Check that categ_ids are correctly computed
        self.assertEqual(len(self.stock_picking.categ_ids), 1, "Should have one category")
        self.assertEqual(
            self.stock_picking.categ_ids.ids,
            [self.product_category.id],
            "Computed category should match product's category",
        )
