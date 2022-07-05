# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    acquirer_id = fields.Many2one("payment.acquirer", compute="_compute_payment", store=True)
    payment_amount = fields.Monetary(string="Amount Payment", compute="_compute_payment", store=True)

    payment_status = fields.Selection(
        [
            ("without", "Without"),
            ("initiated", "Initiated"),
            ("authorized", "Authorized"),
            ("partial", "Partial"),
            ("done", "Done"),
        ],
        default="without",
        compute="_compute_payment",
        store=True,
    )

    def action_payment_link(self):
        payment_link = self.env["payment.link.wizard"].create(
            {
                "res_id": self.id,
                "res_model": "sale.order",
                "description": self.name,
                "amount": self.amount_total - sum(self.invoice_ids.mapped("amount_total")),
                "currency_id": self.currency_id.id,
                "partner_id": self.partner_id.id,
                "amount_max": self.amount_total,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": payment_link.link,
            "target": "new",
        }

    @api.depends("transaction_ids", "invoice_ids.payment_state")
    def _compute_payment(self):
        for order in self:

            amount = 0
            transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")

            acquirer = self.env["payment.acquirer"]

            for invoice in order.invoice_ids:
                amount += invoice.amount_total - invoice.amount_residual
                transactions = transactions - invoice.transaction_ids
            for transaction in transactions:
                amount += transaction.amount
                acquirer = transaction.acquirer_id

            order.payment_amount = amount
            if amount:
                if amount < order.amount_total:
                    order.payment_status = "partial"
                else:
                    order.payment_status = "done"

            if not amount:
                order.payment_status = "without"
                if order.transaction_ids:
                    order.payment_status = "initiated"
                    for transaction in order.sudo().transaction_ids:
                        acquirer = transaction.acquirer_id

                    authorized_transaction_ids = order.transaction_ids.filtered(lambda t: t.state == "authorized")
                    if authorized_transaction_ids:
                        order.payment_status = "authorized"
                        for transaction in authorized_transaction_ids:
                            acquirer = transaction.acquirer_id

            order.acquirer_id = acquirer
