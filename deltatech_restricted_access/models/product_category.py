# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class ProductCategory(models.Model):
    _inherit = "product.category"

    def write(self, vals):
        disallowed_fields = ["property_valuation", "property_cost_method"]
        if any(field for field in vals.keys() if field in disallowed_fields):
            if not self.env.user.has_group("deltatech_restricted_access.group_edit_sensible_data"):
                raise UserError(_("Editing is restricted, you can't do this operation."))

        return super().write(vals)
