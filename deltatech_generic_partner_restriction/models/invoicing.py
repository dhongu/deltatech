from odoo import api, fields, models
from odoo.tools import safe_eval


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange("journal_id")
    def _onchange_journal(self):
        res = super(AccountPayment, self)._onchange_journal()
        customer_id = self.partner_id.id

        get_param = self.env["ir.config_parameter"].sudo().get_param
        generic_partner_id = int(safe_eval(get_param("sale.partner_generic_id", default="False")))

        if customer_id == generic_partner_id:
            if "domain" in res:
                res["domain"].update(
                    {
                        "journal_id": [("restriction", "=", False), ("type", "in", ("bank", "cash"))],
                    }
                )
        return res


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restriction = fields.Boolean(string="Generic Restriction")
