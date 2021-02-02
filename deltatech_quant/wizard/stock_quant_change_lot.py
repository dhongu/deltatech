# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class StockQuantChangeLot(models.TransientModel):
    _name = "stock.quant.change.lot"
    _description = "Stock Quant Change Lot"

    product_id = fields.Many2one("product.product", readonly=True)
    lot_id = fields.Many2one("stock.production.lot", string="Lot/Serial Number")

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockQuantChangeLot, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            quant = self.env["stock.quant"].browse(active_id)
            if quant.lot_id:
                defaults["lot_id"] = quant.lot_id.id
            defaults["product_id"] = quant.product_id.id
        return defaults

    @api.multi
    def do_change_number(self):
        active_id = self.env.context.get("active_id", False)
        if active_id:
            quant = self.env["stock.quant"].browse(active_id)
            quant.write({"lot_id": self.lot_id.id})
