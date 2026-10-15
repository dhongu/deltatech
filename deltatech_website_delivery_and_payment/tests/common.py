# © 2008-2026 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.fields import Command

from odoo.addons.payment.tests.common import PaymentCommon
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


class DeliveryPaymentCommon(PaymentCommon, WebsiteSaleCommon):
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
