# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("lot_name", False) == "/":
                vals["lot_name"] = self.env["ir.sequence"].next_by_code("stock.lot.serial")

        return super().create(vals_list)

    def write(self, vals):
        if vals.get("lot_name", False) == "/":
            vals["lot_name"] = self.env["ir.sequence"].next_by_code("stock.lot.serial")
        return super().write(vals)
