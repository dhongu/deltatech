# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models

DEFAULT_PRIORITY_KEY = "stock.removal_priority.default"


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def _recompute_default_removal_priority(self, old_default):
        # doar cuantele care au luat valoarea implicita veche depind de parametru
        quants = self.env["stock.quant"].sudo().search([("removal_priority", "=", old_default)])
        if quants:
            quants._compute_removal_priority()

    @api.model_create_multi
    def create(self, vals_list):
        touched = any(vals.get("key") == DEFAULT_PRIORITY_KEY for vals in vals_list)
        old_default = touched and self.env["stock.quant"]._get_default_removal_priority()
        res = super().create(vals_list)
        if touched:
            self._recompute_default_removal_priority(old_default)
        return res

    def write(self, vals):
        touched = DEFAULT_PRIORITY_KEY in self.mapped("key") or vals.get("key") == DEFAULT_PRIORITY_KEY
        old_default = touched and self.env["stock.quant"]._get_default_removal_priority()
        res = super().write(vals)
        if touched:
            self._recompute_default_removal_priority(old_default)
        return res

    def unlink(self):
        touched = DEFAULT_PRIORITY_KEY in self.mapped("key")
        old_default = touched and self.env["stock.quant"]._get_default_removal_priority()
        res = super().unlink()
        if touched:
            self._recompute_default_removal_priority(old_default)
        return res
