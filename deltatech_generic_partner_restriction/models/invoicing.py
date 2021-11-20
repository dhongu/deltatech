from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange("journal_id")
    def _onchange_journal(self):
        res = super(AccountPayment, self)._onchange_journal()
        customer_id = self.partner_id.id

        partner_generic = self.company_id.generic_partner_id
        if not partner_generic:
            partner_generic = self.env.ref("deltatech_partner_generic.partner_generic")
        generic_partner_id = partner_generic.id
        # generic_partner_id = int(self.env["ir.config_parameter"].sudo().get_param("sale.partner_generic_id"))
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
