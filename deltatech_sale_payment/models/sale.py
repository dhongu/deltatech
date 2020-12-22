# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    acquirer_id = fields.Many2one("payment.acquirer", related="transaction_ids.acquirer_id", store=True)

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
