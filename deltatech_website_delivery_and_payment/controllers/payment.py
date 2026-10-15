# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError

from odoo.addons.website_sale.controllers.payment import PaymentPortal


class DeliveryPaymentPortal(PaymentPortal):
    def _validate_transaction_for_order(self, transaction, sale_order):
        """Override of `website_sale` to refuse a payment provider that is not allowed for the
        sales order: value limit, partner labels or the providers allowed by the delivery method.

        The payment form offers only the allowed providers; this check covers the express
        checkout (the delivery method is chosen in the wallet, after the provider) and forged
        requests.

        :raises ValidationError: If the provider of the transaction is not allowed.
        """
        res = super()._validate_transaction_for_order(transaction, sale_order)
        provider = transaction.provider_id.sudo()
        if not provider._filter_allowed_for_order(sale_order.sudo()):
            raise ValidationError(
                self.env._(
                    "The payment method %(provider)s is not allowed for this order"
                    " (delivery method %(carrier)s). Please choose another payment method"
                    " or another delivery method.",
                    provider=provider.name,
                    carrier=sale_order.carrier_id.sudo().name or "-",
                )
            )
        return res
