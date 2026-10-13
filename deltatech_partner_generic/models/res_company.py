# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

# Changing one of these invalidates res.partner._get_protected_generic_partner_ids
PROTECTION_FIELDS = frozenset({"generic_partner_id", "lock_generic_partner"})


class ResCompany(models.Model):
    _inherit = "res.company"

    generic_partner_id = fields.Many2one("res.partner", "Generic Partner")
    lock_generic_partner = fields.Boolean(
        string="Protect Generic Partner",
        help="Prevent users from modifying or deleting the generic partner. "
        "Members of the Generic Partner: Editor group are not affected.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        if any(PROTECTION_FIELDS & set(vals) for vals in vals_list):
            self.env.registry.clear_cache()
        return companies

    def write(self, vals):
        result = super().write(vals)
        if PROTECTION_FIELDS & set(vals):
            self.env.registry.clear_cache()
        return result

    def unlink(self):
        clear = any(self.mapped("generic_partner_id"))
        result = super().unlink()
        if clear:
            self.env.registry.clear_cache()
        return result
