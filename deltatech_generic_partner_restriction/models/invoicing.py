from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends("payment_type", "partner_id")
    def _compute_available_journal_ids(self):
        res = super()._compute_available_journal_ids()
        # mai are sens modulul asta?
        # refacut cu logica de compute, versiunea anterioara nu facea nimic
        for rec in self:
            customer_id = rec.partner_id.id

            get_param = self.env["ir.config_parameter"].sudo().get_param
            generic_partner_id = int(safe_eval(get_param("sale.partner_generic_id", default="False")))

            if customer_id == generic_partner_id:
                rec.available_journal_ids = rec.available_journal_ids.filtered(
                    lambda x: not x.restriction and x.type in ["bank", "cash"]
                )
        return res


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restriction = fields.Boolean(string="Generic Restriction")
