# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models

REFRESH_FIELDS = {"name", "email", "phone", "function", "mobile_phone"}


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        result = super().write(vals)
        if REFRESH_FIELDS & set(vals):
            self.sudo().user_ids._refresh_generated_signature()
        return result
