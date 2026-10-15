# © 2008-2025 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.delivery.tests.common import DeliveryCommon
from odoo.addons.payment.tests.common import PaymentCommon


@tagged("post_install", "-at_install")
class TestWebsiteDeliveryAndPayment(PaymentCommon, DeliveryCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider_a = cls.dummy_provider
        cls.provider_b = cls.dummy_provider.copy({"name": "Dummy Provider B", "is_published": True})

        cls.restricted_tag = cls.env["res.partner.category"].create({"name": "Restricted"})
        cls.partner_restricted = cls.env["res.partner"].create(
            {"name": "Customer Restricted", "category_id": [Command.set(cls.restricted_tag.ids)]}
        )

        cls.product.write({"list_price": 10.0, "weight": 2.0})
        cls.order = cls._create_so(order_line=[Command.create({"product_id": cls.product.id, "product_uom_qty": 1})])
        cls.order_restricted = cls._create_so(
            partner_id=cls.partner_restricted.id,
            order_line=[Command.create({"product_id": cls.product.id, "product_uom_qty": 1})],
        )

        carrier_product = cls._prepare_carrier_product()
        cls.carrier_a = cls._prepare_carrier(
            carrier_product, name="Carrier A", is_published=True, acquirer_allowed_ids=[Command.set(cls.provider_a.ids)]
        )
        cls.carrier_b = cls._prepare_carrier(
            carrier_product, name="Carrier B", is_published=True, acquirer_allowed_ids=[Command.set(cls.provider_b.ids)]
        )
        cls.carrier_any = cls._prepare_carrier(carrier_product, name="Carrier Any", is_published=True)

    def _available_providers(self, order):
        return (
            self.env["payment.provider"]
            .sudo()
            ._find_available_providers(
                order.company_id.id,
                order.partner_id.id,
                order.amount_total,
                currency_id=order.currency_id.id,
                sale_order_id=order.id,
            )
        )

    def test_is_restricted_helper(self):
        self.provider_b.restrict_label_ids = self.restricted_tag
        self.assertFalse(self.provider_b.is_restricted(self.partner))
        self.assertTrue(self.provider_b.is_restricted(self.partner_restricted))

    def test_without_carrier_all_providers_are_available(self):
        providers = self._available_providers(self.order)
        self.assertIn(self.provider_a, providers)
        self.assertIn(self.provider_b, providers)

    def test_carrier_limits_providers(self):
        """The payment methods offered change with the selected delivery method."""
        self.order.set_delivery_line(self.carrier_a, 5.0)
        providers = self._available_providers(self.order)
        self.assertIn(self.provider_a, providers)
        self.assertNotIn(self.provider_b, providers)

        self.order.set_delivery_line(self.carrier_b, 5.0)
        providers = self._available_providers(self.order)
        self.assertNotIn(self.provider_a, providers)
        self.assertIn(self.provider_b, providers)

        self.order.set_delivery_line(self.carrier_any, 5.0)
        providers = self._available_providers(self.order)
        self.assertIn(self.provider_a, providers)
        self.assertIn(self.provider_b, providers)

    def test_carrier_restriction_is_reported(self):
        self.order.set_delivery_line(self.carrier_a, 5.0)
        report = {}
        self.env["payment.provider"].sudo()._find_available_providers(
            self.order.company_id.id,
            self.order.partner_id.id,
            self.order.amount_total,
            currency_id=self.order.currency_id.id,
            sale_order_id=self.order.id,
            report=report,
        )
        self.assertFalse(report["providers"][self.provider_b]["available"])
        self.assertTrue(report["providers"][self.provider_a]["available"])

    def test_value_limit(self):
        self.provider_b.value_limit = 50.0
        self.assertIn(self.provider_b, self._available_providers(self.order))  # total 10

        self.order.order_line.product_uom_qty = 5  # total 50: the boundary is allowed
        self.assertEqual(self.order.amount_total, 50.0)
        self.assertIn(self.provider_b, self._available_providers(self.order))

        self.order.order_line.product_uom_qty = 6  # total 60
        providers = self._available_providers(self.order)
        self.assertNotIn(self.provider_b, providers)
        self.assertIn(self.provider_a, providers)

    def test_restrict_label_excludes_partner(self):
        self.provider_b.restrict_label_ids = self.restricted_tag
        self.assertIn(self.provider_b, self._available_providers(self.order))
        providers = self._available_providers(self.order_restricted)
        self.assertNotIn(self.provider_b, providers)
        self.assertIn(self.provider_a, providers)

    def test_without_order_no_filtering(self):
        self.provider_b.value_limit = 1.0
        providers = (
            self.env["payment.provider"]
            .sudo()
            ._find_available_providers(self.company_id, self.partner.id, 100.0, currency_id=self.currency.id)
        )
        self.assertIn(self.provider_b, providers)

    def test_carrier_restrict_label_excludes_for_tagged_partner(self):
        self.carrier_b.restrict_label_ids = self.restricted_tag
        self.assertIn(self.carrier_b, self.order._get_delivery_methods())
        methods = self.order_restricted._get_delivery_methods()
        self.assertNotIn(self.carrier_b, methods)
        self.assertIn(self.carrier_a, methods)

    def test_carrier_weight_limits(self):
        # order weight = 2.0
        self.carrier_a.weight_min = 3.0
        self.carrier_b.weight_max = 1.0
        self.carrier_any.write({"weight_min": 1.0, "weight_max": 2.0})
        methods = self.order._get_delivery_methods()
        self.assertNotIn(self.carrier_a, methods)
        self.assertNotIn(self.carrier_b, methods)
        self.assertIn(self.carrier_any, methods)
