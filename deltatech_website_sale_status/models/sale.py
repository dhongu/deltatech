# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_status = fields.Selection(
        [("without", "Without"), ("initiated", "Initiated"), ("authorized", "Authorized"), ("done", "Done")],
        default="without",
        compute="_compute_payment_status",
        store=True,
    )

    @api.depends("transaction_ids", "invoice_ids")
    def _compute_payment_status(self):
        for order in self:
            order.payment_status = "without"
            if order.transaction_ids:
                order.payment_status = "initiated"
                authorized_transaction_ids = order.transaction_ids.filtered(lambda t: t.state == "authorized")
                if authorized_transaction_ids:
                    order.payment_status = "authorized"
                done_transaction_ids = order.transaction_ids.filtered(lambda t: t.state == "done")
                if done_transaction_ids:
                    order.payment_status = "done"
            if order.payment_status != "done" and order.invoice_ids:
                paid = True
                for invoice in order.invoice_ids:
                    if invoice.invoice_payment_state != "paid":
                        paid = False
                        break
                if paid:
                    order.payment_status = "done"
