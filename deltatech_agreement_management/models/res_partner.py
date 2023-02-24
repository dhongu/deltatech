# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    agreement_id = fields.Many2one("service.agreement", string="Agreement")

    def create_agreement(self):
        self.ensure_one()
        action = {
            "name": _("Agreement"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "service.agreement",
            "context": {"default_partner_id": self.id},
        }
        return action
