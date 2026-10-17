# ©  2008-2022 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductionLot(models.Model):
    _inherit = "stock.lot"

    location_id = fields.Many2one("stock.location", compute="_compute_location", store=True)

    @api.depends("quant_ids", "quant_ids.quantity", "quant_ids.location_id")
    def _compute_location(self):
        for lot in self:
            locations = lot.quant_ids.filtered(lambda x: x.quantity > 0).location_id
            # several quants (owner, package) can share one location
            lot.location_id = locations if len(locations) == 1 else False
