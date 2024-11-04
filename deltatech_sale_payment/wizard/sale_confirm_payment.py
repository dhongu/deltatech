# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
            payment_method_line = self.provider_id.payment_method_ids[0]
            self.payment_method_id = payment_method_line.id

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if not active_id:
            raise UserError(_("Please select a sale order"))

        order = self.env["sale.order"].browse(active_id)
        defaults["currency_id"] = order.currency_id.id

        tx = order.sudo().transaction_ids._get_last()
        if tx and tx.state in ["pending", "authorized"]:
            defaults["transaction_id"] = tx.id
            defaults["provider_id"] = tx.provider_id.id
            defaults["payment_method_id"] = tx.payment_method_id.id
            defaults["amount"] = tx.amount

        return defaults

    def do_add_payment(self):
        active_id = self.env.context.get("active_id", False)
        order = self.env["sale.order"].browse(active_id)

        if self.amount <= 0:
            raise UserError(_("Then amount must be positive"))

        if self.transaction_id:
            self.update_transaction()

        if self.transaction_id:
            return self.transaction_id

        transaction = self.env["payment.transaction"].create(
            {
                "amount": self.amount,
                "provider_id": self.provider_id.id,
                "provider_reference": order.name,
                "payment_method_id": self.payment_method_id.id,
                "partner_id": order.partner_id.id,
                "sale_order_ids": [(4, order.id, False)],
                "currency_id": self.currency_id.id,
                # "date": self.payment_date,
                "state": "draft",
            }
        )
        transaction._set_pending()
        self.transaction_id = transaction

        return transaction

    def update_transaction(self):
        if not self.transaction_id:
            return
        if self.transaction_id.state in ["pending", "draft"]:
            self.transaction_id.write(
                {
                    "amount": self.amount,
                    "provider_id": self.provider_id.id,
                    "payment_method_id": self.payment_method_id.id,
                }
            )
        else:
            self.transaction_id.sudo()._set_canceled()
            self.transaction_id = False

    def do_confirm(self):
        self.do_add_payment()
        transaction = self.transaction_id
        if transaction.state != "done":
            transaction = transaction.with_context(payment_date=self.payment_date)
            transaction._set_pending()
            transaction._set_done()
            if transaction.provider_id.code not in ["none", "custom"]:
                transaction._finalize_post_processing()

            # transaction._reconcile_after_transaction_done()
            # transaction.write({'is_post_processed':True})
