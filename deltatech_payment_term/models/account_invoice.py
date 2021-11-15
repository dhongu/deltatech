# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    in_rates = fields.Boolean(string="In Rates", compute="_compute_in_rates", store=True)

    def view_rate(self):
        action = self.env.ref("deltatech_payment_term.action_account_moves_sale").read()[0]
        action["domain"] = "['|',('move_id','='," + str(self.id) + " ),('name','ilike','" + str(self.name) + "')]"
        return action

    @api.depends("invoice_payment_term_id")
    def _compute_in_rates(self):
        for invoice in self:
            in_rates = False
            if invoice.invoice_payment_term_id:
                if len(invoice.invoice_payment_term_id.line_ids) > 1:
                    in_rates = True

            invoice.in_rates = in_rates
