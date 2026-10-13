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
        """The route is public: confirm only a quotation backed by payment transactions that cover
        the amount required for confirmation, as the standard post-processing of the transaction
        does (`payment.transaction._check_amount_and_confirm_order`)."""
        if order.state not in ("draft", "sent") or order._has_to_be_signed():
            return False
        # Grouped payments (one transaction for several orders) are not supported, as in standard.
        txs = order.transaction_ids.filtered(
            lambda tx: tx.sale_order_ids == order
            and (
                tx.state in ("done", "authorized")
                or (tx.state == "pending" and tx.provider_code in OFFLINE_PROVIDER_CODES)
            )
        )
        if not txs:
            return False
        amount = sum(txs.mapped("amount"))
        return order.currency_id.compare_amounts(order._get_prepayment_required_amount(), amount) <= 0
