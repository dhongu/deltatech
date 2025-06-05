# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    provider_id = fields.Many2one("payment.provider", compute="_compute_payment")
    payment_amount = fields.Monetary(string="Amount Payment", compute="_compute_payment")

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
        search="_search_payment_status",
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

    def _compute_payment(self):
        for order in self:
            amount = 0
            payment_status = "without"

            provider = self.env["payment.provider"]
            all_transactions = order.sudo().transaction_ids
            if all_transactions:
                provider = all_transactions[-1].provider_id

            transactions = all_transactions.filtered(lambda a: a.state == "done")

            for invoice in order.invoice_ids.filtered(lambda a: a.state == "posted"):
                amount += invoice.amount_total_signed - invoice.amount_residual_signed
                transactions = transactions - invoice.transaction_ids
            for transaction in transactions:
                amount += transaction.amount
                provider = transaction.provider_id

            order.payment_amount = amount
            if amount:
                if amount < order.amount_total:
                    payment_status = "partial"
                else:
                    payment_status = "done"

            if not amount:
                payment_status = "without"
                if order.transaction_ids:
                    payment_status = "initiated"
                    for transaction in all_transactions:
                        provider = transaction.provider_id

                    authorized_transaction_ids = order.transaction_ids.filtered(lambda t: t.state == "authorized")
                    if authorized_transaction_ids:
                        payment_status = "authorized"
                        for transaction in authorized_transaction_ids:
                            provider = transaction.provider_id

            order.payment_status = payment_status
            order.provider_id = provider

    def _search_payment_status(self, operator, value):
        if operator == "=":
            if value == "without":
                return [("transaction_ids", "=", False)]
            if value == "initiated":
                return [("transaction_ids.state", "!=", "done")]
            if value == "authorized":
                return [("transaction_ids.state", "=", "authorized")]
            if value == "done":
                return [("transaction_ids.state", "=", "done")]
        return []
