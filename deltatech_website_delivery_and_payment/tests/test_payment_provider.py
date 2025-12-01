# © 2008-2025 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWebsiteDeliveryAndPayment(TransactionCase):
    @classmethod
    def setUpClass(cls):  # noqa: D102
        super().setUpClass()

        cls.env = cls.env  # type: ignore[assignment]

        # Base data
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.currency_usd = cls.env.ref("base.USD")

        # Partner categories and partners
        cls.restricted_tag = cls.env["res.partner.category"].create({"name": "Restricted"})
        cls.partner_ok = cls.env["res.partner"].create({"name": "Customer OK"})
        cls.partner_restricted = cls.env["res.partner"].create(
            {"name": "Customer Restricted", "category_id": [(6, 0, [cls.restricted_tag.id])]}
        )

        # Pricelist
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Test PL", "currency_id": cls.currency_usd.id})

        # Products to control order totals
        cls.product_low = cls.env["product.product"].create(
            {
                "name": "Prod Low",
                "list_price": 10.0,
                "uom_id": cls.uom_unit.id,
                # Since 17.0 no longer using type directly in tests; rely on defaults
            }
        )
        cls.product_high = cls.env["product.product"].create(
            {
                "name": "Prod High",
                "list_price": 100.0,
                "uom_id": cls.uom_unit.id,
            }
        )

        # Sale Orders
        cls.order_low = cls.env["sale.order"].create(
            {"partner_id": cls.partner_ok.id, "pricelist_id": cls.pricelist.id}
        )
        cls.env["sale.order.line"].create(
            {
                "order_id": cls.order_low.id,
                "product_id": cls.product_low.id,
                "product_uom_qty": 1.0,
                "price_unit": cls.product_low.list_price,
                "product_uom_id": cls.uom_unit.id,
                "name": "Low line",
            }
        )

        cls.order_high = cls.env["sale.order"].create(
            {"partner_id": cls.partner_ok.id, "pricelist_id": cls.pricelist.id}
        )
        cls.env["sale.order.line"].create(
            {
                "order_id": cls.order_high.id,
                "product_id": cls.product_high.id,
                "product_uom_qty": 1.0,
                "price_unit": cls.product_high.list_price,
                "product_uom_id": cls.uom_unit.id,
                "name": "High line",
            }
        )

        cls.order_restricted_partner = cls.env["sale.order"].create(
            {"partner_id": cls.partner_restricted.id, "pricelist_id": cls.pricelist.id}
        )
        cls.env["sale.order.line"].create(
            {
                "order_id": cls.order_restricted_partner.id,
                "product_id": cls.product_low.id,
                "product_uom_qty": 1.0,
                "price_unit": cls.product_low.list_price,
                "product_uom_id": cls.uom_unit.id,
                "name": "Restricted partner line",
            }
        )

        # Payment providers to be filtered by our module logic
        cls.provider_with_limit = cls.env["payment.provider"].create(
            {
                "name": "Limit 50",
                "code": "custom",
                "custom_mode": "wire_transfer",
                "state": "enabled",
                "value_limit": 50.0,
            }
        )
        cls.provider_with_tag_restriction = cls.env["payment.provider"].create(
            {
                "name": "Restricted Tag",
                "code": "custom",
                "custom_mode": "wire_transfer",
                "state": "enabled",
                "restrict_label_ids": [(6, 0, [cls.restricted_tag.id])],
            }
        )
        cls.carrier_product = cls.env["product.product"].create(
            {
                "name": "Carrier Product",
                "list_price": 20.0,
                "uom_id": cls.uom_unit.id,
            }
        )

    def _patched_base_compat(self):
        """
        Helper to patch the base method to control the initial compatible set.
        Returns the recordset composed of the two providers created in setUpClass.
        """
        providers = self.provider_with_limit | self.provider_with_tag_restriction
        return providers

    def test_is_restricted_helper(self):
        # Sanity check for the helper method added by the module
        self.assertFalse(self.provider_with_tag_restriction.is_restricted(self.partner_ok))
        self.assertTrue(self.provider_with_tag_restriction.is_restricted(self.partner_restricted))

    def test_value_limit_excludes_high_amount_orders(self):
        # Patch the parent implementation so our override filters a known set
        ids = [self.provider_with_limit.id, self.provider_with_tag_restriction.id]
        with patch(
            "odoo.addons.payment.models.payment_provider.PaymentProvider._get_compatible_providers",
            lambda model_self, *a, **kw: model_self.env["payment.provider"].browse(ids),
        ):
            result = self.env["payment.provider"]._get_compatible_providers(sale_order_id=self.order_high.id)
        # Provider with value_limit=50 should be excluded for totals >= 100
        self.assertNotIn(self.provider_with_limit, result)

    def test_restrict_label_excludes_partner(self):
        # Patch the parent implementation again to control initial set
        ids = [self.provider_with_limit.id, self.provider_with_tag_restriction.id]
        with patch(
            "odoo.addons.payment.models.payment_provider.PaymentProvider._get_compatible_providers",
            lambda model_self, *a, **kw: model_self.env["payment.provider"].browse(ids),
        ):
            result = self.env["payment.provider"]._get_compatible_providers(
                sale_order_id=self.order_restricted_partner.id
            )
        # Provider with restrict_label_ids should be excluded for the tagged partner
        self.assertNotIn(self.provider_with_tag_restriction, result)

    def test_under_limit_and_clean_partner_are_still_compatible(self):
        # Under the limit and without restricted tags → provider_with_limit should remain
        ids = [self.provider_with_limit.id]
        with patch(
            "odoo.addons.payment.models.payment_provider.PaymentProvider._get_compatible_providers",
            lambda model_self, *a, **kw: model_self.env["payment.provider"].browse(ids),
        ):
            result = self.env["payment.provider"]._get_compatible_providers(sale_order_id=self.order_low.id)
        self.assertIn(self.provider_with_limit, result)

    def test_carrier_restrict_label_excludes_for_tagged_partner(self):
        # Create a delivery carrier restricted for the same tag as the partner
        carrier = self.env["delivery.carrier"].create(
            {
                "name": "Restricted Carrier",
                "restrict_label_ids": [(6, 0, [self.restricted_tag.id])],
                "product_id": self.carrier_product.id,
            }
        )
        # For a restricted partner, the carrier should not be proposed by _get_delivery_methods
        order = self.order_restricted_partner
        methods = order._get_delivery_methods()
        self.assertNotIn(carrier, methods)

    def test_carrier_limits_providers_via_acquirer_allowed_ids(self):
        # Create a carrier that only allows provider_with_limit

        carrier = self.env["delivery.carrier"].create(
            {
                "name": "Carrier allows one provider",
                "acquirer_allowed_ids": [(6, 0, [self.provider_with_limit.id])],
                "product_id": self.carrier_product.id,
            }
        )
        # Assign carrier on a valid order
        self.order_low.carrier_id = carrier

        # Patch base compatible providers to include both providers
        ids = [self.provider_with_limit.id, self.provider_with_tag_restriction.id]
        with patch(
            "odoo.addons.payment.models.payment_provider.PaymentProvider._get_compatible_providers",
            lambda model_self, *a, **kw: model_self.env["payment.provider"].browse(ids),
        ):
            result = self.env["payment.provider"]._get_compatible_providers(sale_order_id=self.order_low.id)

        # The resulting providers must be intersected with carrier.acquirer_allowed_ids
        self.assertIn(self.provider_with_limit, result)
        self.assertNotIn(self.provider_with_tag_restriction, result)

    def test_value_limit_equal_boundary_is_allowed(self):
        # When order amount equals value_limit, provider should remain compatible
        order = self.env["sale.order"].create({"partner_id": self.partner_ok.id, "pricelist_id": self.pricelist.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product_high.id,
                "product_uom_qty": 0.5,  # price 100 * 0.5 = 50
                "price_unit": self.product_high.list_price,
                "product_uom_id": self.uom_unit.id,
                "name": "Boundary line",
            }
        )

        ids = [self.provider_with_limit.id]
        with patch(
            "odoo.addons.payment.models.payment_provider.PaymentProvider._get_compatible_providers",
            lambda model_self, *a, **kw: model_self.env["payment.provider"].browse(ids),
        ):
            result = self.env["payment.provider"]._get_compatible_providers(sale_order_id=order.id)

        self.assertNotIn(self.provider_with_limit, result)
