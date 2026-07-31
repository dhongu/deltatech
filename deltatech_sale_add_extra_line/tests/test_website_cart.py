# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteCartExtraLine(WebsiteSaleCommon):
    """The extra line is generated on the e-commerce cart flow as well.

    The cart calls `_cart_add` and `_cart_update_line_quantity`, which both end on the
    `_verify_cart_after_update` hook this module extends.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.extra_product = cls._create_product(name="Test Extra Product", list_price=50.0)
        cls.main_product = cls._create_product(
            name="Test Main Product",
            list_price=100.0,
            extra_product_id=cls.extra_product.id,
            extra_percent=10.0,
        )

    def _lines_of(self, cart, product):
        return cart.order_line.filtered(lambda li, product=product: li.product_id == product)

    def test_cart_add_creates_extra_line(self):
        """Adding the main product to the cart brings the extra line along."""
        cart = self.empty_cart
        values = cart._cart_add(product_id=self.main_product.id, quantity=2)

        main_line = cart.order_line.filtered(lambda li, line_id=values["line_id"]: li.id == line_id)
        self.assertEqual(main_line.product_id, self.main_product)

        extra_line = self._lines_of(cart, self.extra_product)
        self.assertEqual(len(extra_line), 1, "the cart flow generates exactly one extra line")
        self.assertEqual(extra_line.product_uom_qty, 2)
        # 10% of the price of the main line
        self.assertAlmostEqual(extra_line.price_unit, main_line.price_unit * 0.10)
        self.assertFalse(extra_line._has_manual_price())

    def test_cart_add_twice_keeps_one_extra_line(self):
        """A second add updates the existing lines instead of duplicating them."""
        cart = self.empty_cart
        cart._cart_add(product_id=self.main_product.id, quantity=2)
        cart._cart_add(product_id=self.main_product.id, quantity=3)

        self.assertEqual(self._lines_of(cart, self.main_product).product_uom_qty, 5)
        extra_line = self._lines_of(cart, self.extra_product)
        self.assertEqual(len(extra_line), 1)
        self.assertEqual(extra_line.product_uom_qty, 5)

    def test_cart_update_quantity_syncs_extra_line(self):
        """Changing the quantity in the cart syncs the extra line."""
        cart = self.empty_cart
        values = cart._cart_add(product_id=self.main_product.id, quantity=2)

        cart._cart_update_line_quantity(line_id=values["line_id"], quantity=7)

        extra_line = self._lines_of(cart, self.extra_product)
        self.assertEqual(len(extra_line), 1)
        self.assertEqual(extra_line.product_uom_qty, 7)

    def test_cart_extra_qty_multiplier(self):
        """The extra quantity multiplier applies on the cart flow too."""
        self.main_product.extra_qty = 6.0
        cart = self.empty_cart

        cart._cart_add(product_id=self.main_product.id, quantity=10)

        self.assertEqual(self._lines_of(cart, self.extra_product).product_uom_qty, 60)

    def test_cart_remove_main_line_removes_extra_line(self):
        """Emptying the main line of the cart takes the extra line with it."""
        cart = self.empty_cart
        values = cart._cart_add(product_id=self.main_product.id, quantity=2)
        self.assertTrue(self._lines_of(cart, self.extra_product))

        cart._cart_update_line_quantity(line_id=values["line_id"], quantity=0)

        self.assertFalse(self._lines_of(cart, self.main_product))
        self.assertFalse(self._lines_of(cart, self.extra_product))

    def test_cart_manual_price_on_extra_line_is_kept(self):
        """A price set on the extra line survives the next cart update."""
        cart = self.empty_cart
        values = cart._cart_add(product_id=self.main_product.id, quantity=2)
        extra_line = self._lines_of(cart, self.extra_product)
        extra_line.price_unit = 7.0
        self.assertTrue(extra_line._has_manual_price())

        cart._cart_update_line_quantity(line_id=values["line_id"], quantity=4)

        self.assertEqual(extra_line.product_uom_qty, 4, "the quantity keeps following the main line")
        self.assertEqual(extra_line.price_unit, 7.0)

    def test_cart_add_product_without_extra_product(self):
        """A product with no extra product configured does not add any line."""
        cart = self.empty_cart

        cart._cart_add(product_id=self.product.id, quantity=2)

        self.assertEqual(len(cart.order_line), 1)
