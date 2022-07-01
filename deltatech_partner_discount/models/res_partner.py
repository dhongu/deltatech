# © 2021 Terrabit
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    discount = fields.Float("Proposed discount")

    @api.onchange("discount")
    def check_discount_group(self):
        if not self.env.user.has_group("deltatech_partner_discount.group_partner_discount"):
            if self._origin and self._origin.discount != self.discount:
                raise UserError(_("Your user cannot modify the discount."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group("deltatech_partner_discount.group_partner_discount"):
            for vals in vals_list:
                if "discount" in vals and vals["discount"] > 0.0:
                    raise UserError(_("Your user cannot create a partner with discount."))
        return super(ResPartner, self).create(vals_list)
