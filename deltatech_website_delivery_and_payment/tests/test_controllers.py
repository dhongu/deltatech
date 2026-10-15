# © 2008-2026 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.deltatech_website_delivery_and_payment.controllers.delivery import DeliveryRestrictedPayment
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
