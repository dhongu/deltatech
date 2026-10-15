# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.addons.website_sale.controllers.delivery import Delivery


class DeliveryRestrictedPayment(Delivery):
    @classmethod
    def _get_delivery_methods_express_checkout(cls, order_sudo):
        """Override of `website_sale` to hide, in the express checkout, the delivery methods
        that allow only payment providers without express checkout.

        The transaction would be refused anyway (see `_validate_transaction_for_order`).
        """
        res = super()._get_delivery_methods_express_checkout(order_sudo)
        return {
            dm: price
            for dm, price in res.items()
            if not dm.acquirer_allowed_ids or dm.acquirer_allowed_ids.filtered("allow_express_checkout")
        }
