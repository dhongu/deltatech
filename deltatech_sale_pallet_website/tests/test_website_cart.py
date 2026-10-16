# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteCartPallet(WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pallet = cls._create_product(name="Test Pallet", type="consu", list_price=20.0)
        cls.bricks = cls._create_product(
            name="Test Bricks",
            type="consu",
            list_price=5.0,
            pallet_product_id=cls.pallet.id,
            pallet_qty_min=10,
        )

    def _pallet_line(self, cart):
        return cart.order_line.filtered(lambda sol: sol.product_id == self.pallet)

    def test_cart_add_creates_flagged_pallet_line(self):
        cart = self.empty_cart
        cart._cart_add(product_id=self.bricks.id, quantity=20)
        pallet_line = self._pallet_line(cart)
        self.assertEqual(pallet_line.product_uom_qty, 2)
        self.assertTrue(pallet_line.is_pallet_line)

    def test_pallet_lines_present_for_native_verification(self):
        # WEBPALLET-001 (#3466): the delivery rate is computed by the native
        # verification; the pallet lines must already be on the cart at that time.
        cart = self.empty_cart
        cart.carrier_id = self.carrier
        carrier_class = self.registry["delivery.carrier"]
        rate_shipment = carrier_class.rate_shipment
        seen = []

        def wrapped(carrier, order):
            seen.append(order.order_line.product_id)
            return rate_shipment(carrier, order)

        with patch.object(carrier_class, "rate_shipment", wrapped):
            cart._cart_add(product_id=self.bricks.id, quantity=20)
        self.assertTrue(seen)
        self.assertIn(self.pallet, seen[-1])

    def test_pallet_line_removed_with_last_main_product(self):
        # WEBPALLET-002 (#3467)
        cart = self.empty_cart
        values = cart._cart_add(product_id=self.bricks.id, quantity=20)
        self.assertTrue(self._pallet_line(cart))

        cart._cart_update_line_quantity(line_id=values["line_id"], quantity=0)

        self.assertFalse(cart.order_line.filtered(lambda sol: sol.product_id == self.bricks))
        self.assertFalse(self._pallet_line(cart))

    def test_manual_pallet_line_kept(self):
        cart = self.empty_cart
        cart._cart_add(product_id=self.pallet.id, quantity=3)
        self.assertEqual(self._pallet_line(cart).product_uom_qty, 3)
