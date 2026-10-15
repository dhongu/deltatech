# © 2008-2026 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.deltatech_website_delivery_and_payment.controllers.delivery import DeliveryRestrictedPayment
from odoo.addons.deltatech_website_delivery_and_payment.controllers.main import WebsiteSaleDeliveryPayment
from odoo.addons.deltatech_website_delivery_and_payment.controllers.payment import DeliveryPaymentPortal

from .common import DeliveryPaymentCommon


@tagged("post_install", "-at_install")
class TestDeliveryPaymentControllers(DeliveryPaymentCommon):
    def _validate_transaction(self, provider, order):
        tx = self._create_transaction(flow="redirect", provider_id=provider.id, reference=f"{order.name}-{provider.id}")
        with self.mock_request(sale_order_id=order.id):
            DeliveryPaymentPortal()._validate_transaction_for_order(tx, order.sudo())

    def test_transaction_with_provider_not_allowed_by_carrier(self):
        self.order.set_delivery_line(self.carrier_a, 5.0)
        with self.assertRaises(ValidationError):
            self._validate_transaction(self.provider_b, self.order)

    def test_transaction_with_provider_allowed_by_carrier(self):
        self.order.set_delivery_line(self.carrier_a, 5.0)
        self._validate_transaction(self.provider_a, self.order)  # no error

        self.order.set_delivery_line(self.carrier_any, 5.0)
        self._validate_transaction(self.provider_b, self.order)  # no error

    def test_transaction_over_value_limit(self):
        self.provider_b.value_limit = 5.0
        with self.assertRaises(ValidationError):
            self._validate_transaction(self.provider_b, self.order)

    def test_express_checkout_hides_carrier_without_express_provider(self):
        (self.provider_a + self.provider_b).allow_express_checkout = False
        self.provider_b.allow_express_checkout = True
        with self.mock_request(sale_order_id=self.order.id):
            methods = DeliveryRestrictedPayment._get_delivery_methods_express_checkout(self.order.sudo())
        self.assertNotIn(self.carrier_a, methods)
        self.assertIn(self.carrier_b, methods)
        self.assertIn(self.carrier_any, methods)

    def _shop_payment_values(self, order):
        with self.mock_request(sale_order_id=order.id):
            return WebsiteSaleDeliveryPayment()._get_shop_payment_values(order.sudo())

    def test_preferred_payment_method(self):
        self.partner.provider_id = self.provider_b
        values = self._shop_payment_values(self.order)
        preferred = self.env["payment.method"].browse(values["preferred_payment_method_id"])
        self.assertTrue(preferred)
        self.assertEqual(preferred.provider_id, self.provider_b)
        self.assertIn(preferred, values["payment_methods_sudo"])

        html = str(self.env["ir.qweb"]._render("payment.form", values))
        self.assertRegex(html, rf'<input[^>]*\bchecked=[^>]*data-payment-option-id="{preferred.id}"')

    def test_preferred_payment_method_of_the_company(self):
        company = self.env["res.partner"].create({"name": "Company", "provider_id": self.provider_b.id})
        self.partner.parent_id = company
        values = self._shop_payment_values(self.order)
        preferred = self.env["payment.method"].browse(values["preferred_payment_method_id"])
        self.assertEqual(preferred.provider_id, self.provider_b)

    def test_preferred_payment_method_not_allowed(self):
        """The preferred provider is not allowed by the delivery method: nothing is preselected."""
        self.partner.provider_id = self.provider_b
        self.order.set_delivery_line(self.carrier_a, 5.0)
        values = self._shop_payment_values(self.order)
        self.assertFalse(values.get("preferred_payment_method_id"))
        self.assertFalse(values["payment_methods_sudo"].filtered(lambda pm: pm.provider_id == self.provider_b))

    def test_without_preferred_provider(self):
        values = self._shop_payment_values(self.order)
        self.assertNotIn("preferred_payment_method_id", values)

    def test_delivery_method_logo(self):
        self.carrier_a.logo = self._create_image("red")
        with self.mock_request(sale_order_id=self.order.id):
            html_a = str(self.env["ir.qweb"]._render("website_sale.delivery_method", {"dm": self.carrier_a}))
            html_b = str(self.env["ir.qweb"]._render("website_sale.delivery_method", {"dm": self.carrier_b}))
        self.assertIn("o_delivery_method_logo", html_a)
        self.assertIn('src="data:image/', html_a)
        self.assertNotIn("o_delivery_method_logo", html_b)
