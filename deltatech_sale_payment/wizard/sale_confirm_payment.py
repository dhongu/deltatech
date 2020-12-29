# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleConfirmPayment(models.TransientModel):
    _name = "sale.confirm.payment"
    _description = "Sale Confirm Payment"

    transaction_id = fields.Many2one("payment.transaction", readonly=True)
    acquirer_id = fields.Many2one("payment.acquirer", required=True)
    amount = fields.Monetary(string="Amount", required=True)
    currency_id = fields.Many2one("res.currency")
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)

    @api.model
    def default_get(self, fields_list):
        defaults = super(SaleConfirmPayment, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if not active_id:
            raise UserError(_("Please select a sale order"))

        order = self.env["sale.order"].browse(active_id)
        defaults["currency_id"] = order.currency_id.id

        tx = order.sudo().transaction_ids.get_last_transaction()
        if tx and tx.state in ["pending", "authorized"]:
            defaults["transaction_id"] = tx.id
            defaults["acquirer_id"] = tx.acquirer_id.id
            defaults["amount"] = tx.amount

        return defaults

    def do_confirm(self):

        active_id = self.env.context.get("active_id", False)
        order = self.env["sale.order"].browse(active_id)

        if self.amount <= 0:
            raise UserError(_("Then amount must be positive"))

        if self.transaction_id and self.transaction_id.amount == self.amount:
            transaction = self.transaction_id
        else:
            transaction = self.env["payment.transaction"].create(
                {
                    "amount": self.amount,
                    "acquirer_id": self.acquirer_id.id,
                    "acquirer_reference": order.name,
                    "partner_id": order.partner_id.id,
                    "sale_order_ids": [(4, order.id, False)],
                    "currency_id": self.currency_id.id,
                    "date": self.payment_date,
                    "state": "draft",
                }
            )

        if transaction.state != "done":
            transaction = transaction.with_context(payment_date=self.payment_date)
            transaction._set_transaction_pending()
            transaction._set_transaction_done()
            transaction._post_process_after_done()

            # transaction._reconcile_after_transaction_done()
            # transaction.write({'is_processed':True})
