# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Issue #3454: the order-line onchange must not replace a same-name onchange of another module.

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestOnchangeCollision(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.extra = cls.env["product.product"].create({"name": "Extra", "type": "consu", "list_price": 10})
        cls.product = cls.env["product.product"].create(
            {"name": "Main", "type": "consu", "list_price": 100, "extra_product_id": cls.extra.id}
        )
        cls.delivery_product = cls.env["product.product"].create({"name": "Shipping", "type": "service"})

    def _onchange_names(self):
        return [getattr(m, "__name__", "") for m in self.env["sale.order"]._onchange_methods.get("order_line", [])]

    def test_onchange_registered_under_own_name(self):
        self.assertIn("_onchange_order_line_extra", self._onchange_names())

    def test_delivery_onchange_kept(self):
        """The native `onchange_order_line` of `delivery` (also called from the product catalog)
        still flags the shipping price for recomputation."""
        self.assertIn("onchange_order_line", self._onchange_names())
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (0, 0, {"product_id": self.delivery_product.id, "is_delivery": True, "price_unit": 5}),
                ],
            }
        )
        self.assertFalse(order.recompute_delivery_price)
        order.onchange_order_line()
        self.assertTrue(order.recompute_delivery_price)

    def test_extra_line_still_generated_in_form(self):
        so_form = Form(self.env["sale.order"])
        so_form.partner_id = self.partner
        with so_form.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 3
        order = so_form.save()
        extra = order.order_line.filtered(lambda li: li.product_id == self.extra)
        self.assertEqual(extra.product_uom_qty, 3)
