# © 2021 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class ResPartner(models.Model):
    _inherit = "res.partner"

    discount = fields.Float("Proposed discount")

    def _can_modify_discount(self):
        return self.env.su or self.env.user.has_group("deltatech_partner_discount.group_partner_discount")

    @api.onchange("discount")
    def check_discount_group(self):
        # immediate feedback in the form; write() enforces the same rule for imports and RPC
        if not self._can_modify_discount():
            if self._origin and self._origin.discount != self.discount:
                raise UserError(self.env._("Your user cannot modify the discount."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self._can_modify_discount():
            for vals in vals_list:
                discount = vals.get("discount", self.env.context.get("default_discount"))
                if discount:
                    raise UserError(self.env._("Your user cannot create a partner with discount."))
        return super().create(vals_list)

    def write(self, vals):
        if "discount" in vals and not self._can_modify_discount():
            new_discount = vals["discount"] or 0.0
            if any(float_compare(partner.discount, new_discount, precision_digits=6) for partner in self):
                raise UserError(self.env._("Your user cannot modify the discount."))
        return super().write(vals)
