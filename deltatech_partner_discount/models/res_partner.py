# © 2021 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class ResPartner(models.Model):
    _inherit = "res.partner"

    discount = fields.Float("Proposed discount")

    @api.onchange("discount")
    def check_discount_group(self):
        if not self.env.user.has_group("deltatech_partner_discount.group_partner_discount"):
            if self._origin and self._origin.discount != self.discount:
                raise UserError(self.env._("Your user cannot modify the discount."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group("deltatech_partner_discount.group_partner_discount"):
            for vals in vals_list:
                if "discount" in vals and vals["discount"] > 0.0:
                    raise UserError(self.env._("Your user cannot create a partner with discount."))
        return super().create(vals_list)

    def write(self, vals):
        # The onchange above is only UI feedback: import, RPC and server-side writes bypass it.
        if "discount" in vals and not self.env.su:
            new_discount = vals["discount"] or 0.0
            changed = any(float_compare(partner.discount, new_discount, precision_digits=6) for partner in self)
            if changed and not self.env.user.has_group("deltatech_partner_discount.group_partner_discount"):
                raise UserError(self.env._("Your user cannot modify the discount."))
        return super().write(vals)
