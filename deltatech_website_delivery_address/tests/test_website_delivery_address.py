# ©  2008-2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteDeliveryAddress(HttpCase, WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = new_test_user(
            cls.env, login="dt_delivery_portal", groups="base.group_portal", name="Portal Delivery"
        )
        cls.portal_user.partner_id.write(cls.dummy_partner_address_values)
        # the standard checkout preselects the first delivery address of the customer: the
        # default one of the user is another one
        cls.standard_address, cls.delivery_address = cls.env["res.partner"].create(
            [
                {
                    **cls.dummy_partner_address_values,
                    "name": "Shop",
                    "type": "delivery",
                    "street": "9 Main Street",
                    "parent_id": cls.portal_user.partner_id.id,
                },
                {
                    **cls.dummy_partner_address_values,
                    "name": "Warehouse",
                    "type": "delivery",
                    "street": "1 Dock Road",
                    "parent_id": cls.portal_user.partner_id.id,
                },
            ]
        )

    def _add_to_cart(self):
        self.make_jsonrpc_request(
            "/shop/cart/add",
            {"product_template_id": self.product.product_tmpl_id.id, "product_id": self.product.id, "quantity": 1},
        )
        return self.env["sale.order"].search(
            [("partner_id", "=", self.portal_user.partner_id.id), ("website_id", "=", self.website.id)],
            order="id desc",
            limit=1,
        )

    def test_default_delivery_address_preselected(self):
        self.portal_user.sudo().delivery_address_id = self.delivery_address
        self.authenticate(self.portal_user.login, self.portal_user.login)
        order = self._add_to_cart()
        self.assertEqual(order.partner_shipping_id, self.delivery_address)

        response = self.url_open("/shop/checkout")
        self.assertEqual(response.status_code, 200)
        self.assertIn("1 Dock Road", response.text)
        self.assertEqual(order.partner_shipping_id, self.delivery_address)

    def test_without_default_delivery_address(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        order = self._add_to_cart()
        self.assertEqual(order.partner_shipping_id, self.standard_address)

    def test_public_visitor_cart(self):
        """The public user has no default delivery address: the anonymous cart is unchanged."""
        self.make_jsonrpc_request(
            "/shop/cart/add",
            {"product_template_id": self.product.product_tmpl_id.id, "product_id": self.product.id, "quantity": 1},
        )
        response = self.url_open("/shop/cart")
        self.assertEqual(response.status_code, 200)
