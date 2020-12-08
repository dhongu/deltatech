# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class PackOperationLot(models.Model):
    _inherit = "stock.pack.operation.lot"

    @api.model
    def create(self, vals):
        if vals.get("lot_name", False) == "/":
            vals["lot_name"] = self.env["ir.sequence"].next_by_code("stock.lot.serial")
        return super(PackOperationLot, self).create(vals)
