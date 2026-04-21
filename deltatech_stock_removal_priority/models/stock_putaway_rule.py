# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    def _invalidate_removal_priority(self):
        loc_ids = self.mapped("location_out_id").ids
        if loc_ids:
            self.env["stock.quant"].search([("location_id", "in", loc_ids)])._compute_removal_priority()

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        rules._invalidate_removal_priority()
        return rules

    def write(self, vals):
        if any(f in vals for f in ("sequence", "product_id", "category_id", "location_out_id")):
            old_loc_ids = self.mapped("location_out_id").ids
        else:
            old_loc_ids = []
        res = super().write(vals)
        if old_loc_ids:
            new_loc_ids = self.mapped("location_out_id").ids
            all_loc_ids = list(set(old_loc_ids + new_loc_ids))
            self.env["stock.quant"].search([("location_id", "in", all_loc_ids)])._compute_removal_priority()
        return res

    def unlink(self):
        loc_ids = self.mapped("location_out_id").ids
        res = super().unlink()
        if loc_ids:
            self.env["stock.quant"].search([("location_id", "in", loc_ids)])._compute_removal_priority()
        return res
