from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReplenishmentExplainLegacyMultiple(TransactionCase):
    """`qty_multiple` is a legacy rounding field added by the optional
    deltatech_stock_orderpoint_multiple module (not a hard dependency here).
    When present, the explanation must attribute rounding to it too, not only
    to the native `replenishment_uom_id`.
    """

    def test_legacy_qty_multiple_is_explained(self):
        orderpoint_model = self.env["stock.warehouse.orderpoint"]
        if "qty_multiple" not in orderpoint_model._fields:
            self.skipTest("deltatech_stock_orderpoint_multiple is not installed")

        warehouse = self.env["stock.warehouse"].search([], limit=1)
        product = self.env["product.product"].create({"name": "Test product legacy qty multiple", "is_storable": True})
        # Negative on-hand qty so forecast < min_qty (0) even with min = max = 0
        # (required: max_qty = 0 is what makes the rounding go *up*).
        self.env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, -38)

        orderpoint = orderpoint_model.create(
            {
                "product_id": product.id,
                "location_id": warehouse.lot_stock_id.id,
                "warehouse_id": warehouse.id,
                "product_min_qty": 0,
                "product_max_qty": 0,
                "qty_multiple": 100,
            }
        )

        explanation = orderpoint._get_replenishment_explanation()
        self.assertIn("100", explanation["multiple_name"])
        self.assertTrue(
            any(risk["title"] == "Rounded up to a multiple" for risk in explanation["risks"]),
            "Legacy qty_multiple rounding must be surfaced in the explanation risks",
        )
