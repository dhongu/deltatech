# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date


class SaleConfirmPayment(models.TransientModel):
    _name = "sale.confirm.payment"
    _description = "Sale Confirm Payment"

    transaction_id = fields.Many2one("payment.transaction", readonly=True)
    provider_id = fields.Many2one("payment.provider", required=True, domain=[("state", "!=", "disabled")])
    amount = fields.Monetary(string="Amount", required=True)
    currency_id = fields.Many2one("res.currency")
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    payment_method_id = fields.Many2one("payment.method")

    @api.onchange("provider_id")
    def _onchange_provider_id(self):
        if self.provider_id:
            if self.provider_id.payment_method_ids:
                payment_method_line = self.provider_id.payment_method_ids[0]
                self.payment_method_id = payment_method_line.id

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if not active_id:
            raise UserError(self.env._("Please select a sale order"))

        order = self.env["sale.order"].browse(active_id)
        defaults["currency_id"] = order.currency_id.id

        # Only a transaction still waiting for the money is taken over: a confirmed one already
        # has its accounting payment, and an authorized one must be captured at the provider.
        tx = order.sudo().transaction_ids.filtered(lambda t: t.state in ("draft", "pending")).sorted("id")[-1:]
        if tx:
            defaults["transaction_id"] = tx.id
            defaults["provider_id"] = tx.provider_id.id
            defaults["payment_method_id"] = tx.payment_method_id.id
            defaults["amount"] = tx.amount
        else:
            defaults["amount"] = max(order.amount_total - order.payment_amount, 0.0)

        return defaults

    def _get_order(self):
        order = self.env["sale.order"].browse(self.env.context.get("active_id", False))
        # The wizard writes the transactions as superuser: whoever may change the order may record
        # its payment, without needing the Invoicing rights Odoo asks for on payment.transaction.
        order.check_access("write")
        authorized = order.sudo().transaction_ids.filtered(lambda t: t.state == "authorized")
        if authorized:
            raise UserError(
                self.env._(
                    "The order has an authorized payment (%(reference)s, %(provider)s). "
                    "Capture or void it from the payment provider.",
                    reference=", ".join(authorized.mapped("reference")),
                    provider=", ".join(authorized.provider_id.mapped("name")),
                )
            )
        return order

    def _get_payment_method(self):
        # The method is required on the transaction, and a provider such as "none" has none
        return (
            self.payment_method_id
            or self.provider_id.payment_method_ids[:1]
            or self.env.ref("payment.payment_method_unknown", raise_if_not_found=False)
        )

    def do_add_payment(self):
        order = self._get_order()

        if self.amount < 0:
            raise UserError(self.env._("Then amount must be positive"))

        if self.transaction_id:
            self.update_transaction()
            return self.transaction_id

        if not self.amount:
            return self.env["payment.transaction"]

        transaction = (
            self.env["payment.transaction"]
            .sudo()
            .create(
                {
                    "amount": self.amount,
                    "provider_id": self.provider_id.id,
                    "provider_reference": order.name,
                    "payment_method_id": self._get_payment_method().id,
                    "partner_id": order.partner_id.id,
                    "sale_order_ids": [(4, order.id, False)],
                    "currency_id": self.currency_id.id,
                    "state": "draft",
                }
            )
        )
        transaction._set_pending()
        self.transaction_id = transaction

        return transaction

    def update_transaction(self):
        if not self.transaction_id:
            return
        transaction = self.transaction_id.sudo()
        if transaction.state not in ("pending", "draft"):
            raise UserError(
                self.env._(
                    "The transaction %(reference)s is no longer waiting for the payment.",
                    reference=transaction.reference,
                )
            )
        transaction.write(
            {
                "amount": self.amount,
                "provider_id": self.provider_id.id,
                "payment_method_id": self._get_payment_method().id,
            }
        )

    def do_confirm(self):
        order = self._get_order()
        self.do_add_payment()
        transaction = self.transaction_id.sudo()
        if transaction.state != "done" and transaction.amount > 0:
            transaction._set_pending()
            transaction._set_done(
                state_message=self.env._(
                    "Payment received on %(date)s, confirmed by %(user)s.",
                    date=format_date(self.env, self.payment_date),
                    user=self.env.user.name,
                )
            )
            # Post-process now instead of waiting for the cron: the accounting payment (when the
            # provider has a payment method line) is dated with the payment date of the wizard.
            transaction.with_context(payment_date=self.payment_date)._post_process()
            order.message_post(
                body=self.env._(
                    "Payment of %(amount)s by %(provider)s received on %(date)s.",
                    amount=transaction.currency_id.format(transaction.amount),
                    provider=transaction.provider_id.name,
                    date=format_date(self.env, self.payment_date),
                )
            )
