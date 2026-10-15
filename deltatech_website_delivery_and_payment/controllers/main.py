# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDeliveryPayment(WebsiteSale):
    def _get_shop_payment_values(self, order, **kwargs):
        """Override of `website_sale` to preselect the payment method of the partner's preferred
        payment provider (`res.partner.provider_id`, read on the commercial partner).

        Only the displayed payment methods are considered: if the preferred provider is not
        allowed for the order, nothing is preselected.
        """
        values = super()._get_shop_payment_values(order, **kwargs)
        provider = order.partner_id.commercial_partner_id.sudo().provider_id
        payment_methods = values.get("payment_methods_sudo")
        if provider and payment_methods:
            preferred_method = payment_methods.filtered(lambda pm: pm.provider_id == provider)[:1]
            values["preferred_payment_method_id"] = preferred_method.id
        return values
