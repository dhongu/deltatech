from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPosStockAvailable(TransactionCase):
    """`free_qty` exists on product.product but not on product.template, and the POS card is
    handed a template — so the aggregation is ours and needs to hold."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "Size",
                "value_ids": [
                    (0, 0, {"name": "Small"}),
                    (0, 0, {"name": "Large"}),
                ],
            }
        )
        cls.template = cls.env["product.template"].create(
            {
                "name": "Badge Test Product",
                "is_storable": True,
                "available_in_pos": True,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [(6, 0, cls.attribute.value_ids.ids)],
                        },
                    )
                ],
            }
        )
        # Created, not searched: a demo-free database has no pos.config at all, and an empty
        # recordset would make these assertions pass without testing anything.
        cls.config = cls.env["pos.config"].create({"name": "Badge Test Register"})

    def _set_stock(self, variant, quantity):
        self.env["stock.quant"]._update_available_quantity(variant, self.stock_location, quantity)

    def test_free_qty_sums_the_variants(self):
        small, large = self.template.product_variant_ids[:2]
        self._set_stock(small, 4)
        self._set_stock(large, 6)
        self.template.invalidate_recordset()
        self.assertEqual(self.template.free_qty, 10)
        self.assertEqual(self.template.qty_available, 10)

    def test_free_qty_drops_when_stock_is_reserved(self):
        """A sale left for the warehouse reserves without moving anything: on hand stays put,
        available goes down. That gap is the whole point of the setting."""
        variant = self.template.product_variant_ids[0]
        self._set_stock(variant, 10)
        quant = self.env["stock.quant"]._gather(variant, self.stock_location)
        quant.reserved_quantity = 3
        self.template.invalidate_recordset()
        self.assertEqual(self.template.qty_available, 10, "physical stock must not move")
        self.assertEqual(self.template.free_qty, 7, "available must drop by what is reserved")

    def test_loaded_fields_follow_the_setting(self):
        self.config.write({"display_stock": True, "stock_badge_quantity": "on_hand"})
        fields_on_hand = self.env["product.template"]._load_pos_data_fields(self.config)
        self.assertIn("qty_available", fields_on_hand)
        self.assertNotIn(
            "free_qty",
            fields_on_hand,
            "registers left on 'on hand' should not pay for reading every reservation",
        )

        self.config.stock_badge_quantity = "available"
        fields_available = self.env["product.template"]._load_pos_data_fields(self.config)
        self.assertIn("qty_available", fields_available)
        self.assertIn("free_qty", fields_available)

    def test_reservation_gate_stays_shut_on_default_settings(self):
        """`reserved_quantity` is written on every reservation. With no register asking for the
        available quantity, nothing on that path should be worth doing."""
        self.config.write({"display_stock": True, "stock_badge_quantity": "on_hand"})
        self.assertFalse(self.env["stock.quant"]._pos_available_badge_in_use())

    def test_reservation_gate_opens_for_available_badges(self):
        self.config.write({"display_stock": True, "stock_badge_quantity": "available"})
        self.assertTrue(self.env["stock.quant"]._pos_available_badge_in_use())

    def test_reservation_gate_ignores_registers_with_the_badge_off(self):
        self.config.write({"display_stock": False, "stock_badge_quantity": "available"})
        self.assertFalse(self.env["stock.quant"]._pos_available_badge_in_use())

    def test_no_stock_fields_when_the_badge_is_off(self):
        self.config.display_stock = False
        loaded = self.env["product.template"]._load_pos_data_fields(self.config)
        self.assertNotIn("free_qty", loaded)
