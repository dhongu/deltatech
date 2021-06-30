from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Restrict Journals"

    partner_id_check = fields.Integer(compute="_compute_value")

    @api.onchange("partner_id")
    def _compute_value(self):
        if self.partner_id.name == "Generic":
            self.partner_id_check = 1
        else:
            self.partner_id_check = 0
