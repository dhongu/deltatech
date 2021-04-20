# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        partner_generic = self.env.ref("deltatech_partner_generic.partner_generic")
        if partner_generic.id in self.ids:
            raise UserError(_("You cannot change Generic partner data"))
        return super(ResPartner, self).write(vals)
