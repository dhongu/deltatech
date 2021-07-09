from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Restrict Journals"

    @api.onchange("journal_id")
    def _onchange_journal(self):
        customer_id = self.partner_id.id
        generic_partner_id = int(self.env["ir.config_parameter"].sudo().get_param("sale.partner_generic_id"))
        if customer_id == generic_partner_id:
            return {"domain": {"journal_id": [("restriction", "=", False), ("type", "in", ("bank", "cash"))]}}
        else:
            return {"domain": {"journal_id": [("type", "in", ("bank", "cash"))]}}


class AccountJournal(models.Model):
    _inherit = "account.journal"
    _description = ""

    restriction = fields.Boolean(string="Generic Restriction")
