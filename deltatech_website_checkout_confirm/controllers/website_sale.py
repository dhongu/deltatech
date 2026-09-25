from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

# Providers without online processing: the transaction stays `pending` until the money arrives
# (wire transfer, cash on delivery), so a pending transaction is enough to confirm the order.
OFFLINE_PROVIDER_CODES = ("custom", "on_delivery")


class WebsiteSaleCheckout(WebsiteSale):
    @http.route()
    def shop_payment_confirmation(self, **post):
        sale_order_id = request.session.get("sale_last_order_id")
        if sale_order_id:
            order = request.env["sale.order"].sudo().browse(sale_order_id).exists()
            if order and self._checkout_confirm_can_confirm(order):
                order.action_confirm()
        return super().shop_payment_confirmation(**post)

    def _checkout_confirm_can_confirm(self, order):
        """The route is public: confirm only a quotation backed by a payment transaction."""
        if order.state not in ("draft", "sent"):
            return False
        for tx in order.transaction_ids:
            if tx.state in ("done", "authorized"):
                return True
            if tx.state == "pending" and tx.provider_code in OFFLINE_PROVIDER_CODES:
                return True
        return False
