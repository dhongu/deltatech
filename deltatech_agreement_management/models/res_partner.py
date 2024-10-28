# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    agreement_count = fields.Integer(
        string="Agreements",
        compute="_compute_agreements_no",
        search="_search_agreement",
    )

    def view_agreements(self):
        self.ensure_one()
        action = {
            "name": _("Agreement"),
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "general.agreement",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
        return action

    @api.model
    def _search_agreement(self, operator, value):
        agreements = self.env["general.agreement"].search([])
        domain = [("id", "in", agreements.partner_id.ids)]
        return domain

    def _compute_agreements_no(self):
        for partner in self:
            agreement_count = self.env["general.agreement"].sudo().search_count([("partner_id", "=", partner.id)])
            partner.agreement_count = agreement_count
