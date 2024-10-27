from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary test data (locations, products, etc.) here if needed
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "default_code": "TEST_PROD",
                "uom_id": self.ref("uom.product_uom_unit"),  # Replace with appropriate UOM ID
                "uom_po_id": self.ref("uom.product_uom_unit"),  # Replace with appropriate UOM ID
            }
        )

        self.location_src = self.env["stock.location"].create(
            {
                "name": "Source Location",
                "usage": "internal",
            }
        )

        self.location_dest = self.env["stock.location"].create(
            {
                "name": "Destination Location",
                "usage": "internal",
            }
        )

        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "code": "internal",
                "sequence_code": "INT",
                "default_location_src_id": self.location_src.id,
                "default_location_dest_id": self.location_dest.id,
                "active": True,
            }
        )

    def test_get_negative_products(self):
        StockQuant = self.env["stock.quant"]

        # Create or update stock quant to set the quantity to -5
        quant = StockQuant.search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", self.location_dest.id),
            ],
            limit=1,
        )

        if quant:
            quant.write({"quantity": -5})
        else:
            StockQuant.create(
                {
                    "product_id": self.product.id,
                    "location_id": self.location_dest.id,
                    "quantity": -5,
                }
            )

        StockPicking = self.env["stock.picking"]

        # Create a draft stock picking
        picking = StockPicking.create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.location_src.id,
                "location_dest_id": self.location_dest.id,
                "scheduled_date": fields.Date.today(),
                "state": "draft",
            }
        )

        # Call the method to fetch negative products
        picking.get_negative_products()

        # Check if moves were created correctly
        self.assertTrue(picking.move_ids_without_package, "Expected move lines to be created")
