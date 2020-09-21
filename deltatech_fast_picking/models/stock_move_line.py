# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def create(self, vals):
        vals["qty_done"] = vals.get("product_uom_qty")
        return super(StockMoveLine, self).create(vals)
