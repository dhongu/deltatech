# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.depends("company_id", "location_id", "owner_id", "product_id", "quantity", "lot_id")
    def _compute_value(self):
        quants = self.env["stock.quant"]
        for quant in self:
            if quant.product_id.tracking == "lot" and quant.lot_id.inventory_value == 0:
                quant.lot_id.inventory_value = quant.price_unit * quant.quantity
            if quant.lot_id:
                # super(StockQuant, quant.with_context(lot_ids=quant.lot_id))._compute_value()
                quant.value = quant.lot_id.inventory_value
            else:
                quants += quant
        return super(StockQuant, quants)._compute_value()
