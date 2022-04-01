# ©  2008-2022 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductionLot(models.Model):
    _inherit = "stock.production.lot"

    inventory_value = fields.Float("Inventory value")
    unit_price = fields.Float("Unit Price")
    input_price = fields.Float("Input Price")
    input_date = fields.Date(string="Input date")
    location_id = fields.Many2one("stock.location", compute="_compute_location", store=True)

    @api.depends("quant_ids")
    def _compute_location(self):
        for lot in self:
            quants = lot.quant_ids.filtered(lambda x: x.quantity > 0)
            if len(quants) > 1:  # multiple quants, can be in different locations
                lot.location_id = False
            else:
                lot.location_id = quants.location_id
