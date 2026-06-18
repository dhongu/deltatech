from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestSaleMultipleWebsite(WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product.qty_multiple = 5.0
        cls.product.qty_minim = 10.0
        cls.product.product_tmpl_id.check_min_website = True

    def test_cart_quantity_is_rounded_on_website(self):
        line = self.cart.order_line.filtered(lambda item: item.product_id == self.product)
        cart = self.cart.with_context(website_id=self.website.id)

        cart._cart_update_order_line(line, 7.0)

        self.assertEqual(line.product_uom_qty, 10.0)

    def test_internal_quantity_is_not_rounded_for_website_only_product(self):
        line = self.cart.order_line.filtered(lambda item: item.product_id == self.product)

        self.cart._cart_update_order_line(line, 7.0)

        self.assertEqual(line.product_uom_qty, 7.0)

    def test_global_quantity_rule_is_applied_outside_website(self):
        self.product.product_tmpl_id.check_min_website = False
        line = self.cart.order_line.filtered(lambda item: item.product_id == self.product)

        self.cart._cart_update_order_line(line, 7.0)

        self.assertEqual(line.product_uom_qty, 10.0)
