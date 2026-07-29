from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary test data (locations, products, etc.) here if needed
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "default_code": "TEST_PROD",
                "uom_id": self.ref("uom.product_uom_unit"),  # Replace with appropriate UOM ID
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

    def _set_negative_quant(self, location, quantity=-5):
        StockQuant = self.env["stock.quant"]
        quant = StockQuant.search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", location.id),
            ],
            limit=1,
        )
        if quant:
            quant.write({"quantity": quantity})
        else:
            quant = StockQuant.create(
                {
                    "product_id": self.product.id,
                    "location_id": location.id,
                    "quantity": quantity,
                }
            )
        return quant

    def test_get_negative_products(self):
        self._set_negative_quant(self.location_dest, -5)

        StockPicking = self.env["stock.picking"]

        # Create a draft stock picking
        picking = StockPicking.create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.location_src.id,
                "location_dest_id": self.location_dest.id,
                "scheduled_date": fields.Date.today(),
            }
        )
        self.assertEqual(picking.state, "draft")

        # Call the method to fetch negative products
        picking.get_negative_products()

        # Check if moves were created correctly
        # Odoo 19: `move_ids_without_package` was removed from `stock.picking`
        self.assertTrue(picking.move_ids, "Expected move lines to be created")
        move = picking.move_ids.filtered(lambda m: m.product_id == self.product)
        self.assertEqual(len(move), 1)
        self.assertEqual(move.product_uom_qty, 5)
        self.assertEqual(move.product_uom, self.product.uom_id)
        self.assertEqual(move.location_id, self.location_src)
        self.assertEqual(move.location_dest_id, self.location_dest)
        self.assertEqual(move.state, "draft")

    def test_location_get_negative_products(self):
        """The negative quantities are aggregated per product, over the sub-locations."""
        sub_location = self.env["stock.location"].create(
            {
                "name": "Sub Location",
                "usage": "internal",
                "location_id": self.location_dest.id,
            }
        )
        self._set_negative_quant(self.location_dest, -5)
        self._set_negative_quant(sub_location, -3)

        products = self.location_dest.get_negative_products()
        self.assertEqual(products, {self.product: -8})

    def test_send_mail_negative_stock(self):
        """The manager of the location is notified only when there is negative stock."""
        self.location_dest.user_id = self.env.user

        # no negative stock yet: nothing to notify about
        self.assertFalse(self.location_dest.send_mail_negative_stock())

        self._set_negative_quant(self.location_dest, -5)
        mails_before = self.env["mail.mail"].search_count([])
        self.assertTrue(self.location_dest.send_mail_negative_stock())
        self.assertEqual(self.env["mail.mail"].search_count([]), mails_before + 1)

    def test_send_mail_negative_stock_without_manager(self):
        """Without a manager the location is skipped, the cron must not fail."""
        self._set_negative_quant(self.location_dest, -5)
        self.assertFalse(self.location_dest.user_id)
        self.assertFalse(self.location_dest.send_mail_negative_stock())
