# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockCountZero(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
            }
        )
        self.stock_location = self.env.ref("stock.stock_location_stock")

        # Create initial quant and apply it to have 10.0 in quantity
        self.quant = (
            self.env["stock.quant"]
            .with_context(inventory_mode=True)
            .create(
                {
                    "product_id": self.product.id,
                    "location_id": self.stock_location.id,
                    "inventory_quantity": 10.0,
                }
            )
        )
        self.quant.action_apply_inventory()
        self.assertEqual(self.quant.quantity, 10.0)

    def test_stock_count_zero_checked(self):
        """Test setting count to zero when 'set_count_zero' is checked in wizard"""
        # Create the wizard
        wizard = self.env["stock.request.count"].create(
            {
                "set_count_zero": True,
                "quant_ids": [(6, 0, self.quant.ids)],
            }
        )

        # Action the wizard
        wizard.action_request_count()

        # Invalidate cache to ensure we get fresh data from DB
        self.quant.invalidate_recordset(["quantity"])

        # Verify that quantity is now 0.0 (inventory_quantity is cleared after application)
        self.assertEqual(
            self.quant.quantity, 0.0, "The quantity should be set to 0.0 when 'set_count_zero' is checked."
        )

    def test_stock_count_zero_unchecked(self):
        """Test that count is NOT set to zero when 'set_count_zero' is unchecked"""
        # Create the wizard
        wizard = self.env["stock.request.count"].create(
            {
                "set_count_zero": False,
                "quant_ids": [(6, 0, self.quant.ids)],
            }
        )

        # Action the wizard
        wizard.action_request_count()

        # Invalidate cache
        self.quant.invalidate_recordset(["quantity"])

        # Verify that quantity is still 10.0
        self.assertEqual(
            self.quant.quantity, 10.0, "The quantity should not be changed when 'set_count_zero' is unchecked."
        )
