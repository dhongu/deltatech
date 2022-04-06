# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    price_unit = fields.Monetary(compute="_compute_value")

    @api.depends("company_id", "location_id", "owner_id", "product_id", "quantity", "lot_id")
    def _compute_value(self):
        quants = self.env["stock.quant"]
        for quant in self:
            value = 0
            quant.price_unit = quant.product_id.standard_price
            if quant.lot_id:
                if quant.product_id.tracking == "serial":
                    value = quant.lot_id.inventory_value
                else:
                    value = quant.lot_id.unit_price * quant.quantity

                quant.currency_id = quant.company_id.currency_id
                quant.value = value
                if quant.quantity:
                    quant.price_unit = value / quant.quantity
            else:
                quants += quant
            quant.currency_id = quant.company_id.currency_id
        res = super(StockQuant, quants)._compute_value()
        for quant in quants:
            if quant.quantity:
                quant.price_unit = quant.value / quant.quantity
        return res

    # @api.depends("company_id", "location_id", "owner_id", "product_id", "quantity", "lot_id")
    # def _compute_value(self):
    #     quants = self.env["stock.quant"]
    #     for quant in self:
    #     if quant.product_id.tracking == "lot" and quant.lot_id.inventory_value == 0:
    #         quant.lot_id.inventory_value = quant.price_unit * quant.quantity
    #     if quant.lot_id:
    #         # super(StockQuant, quant.with_context(lot_ids=quant.lot_id))._compute_value()
    #         if quant.lot_id.product_qty:
    #             unit_price = quant.lot_id.inventory_value / quant.lot_id.product_qty
    #             quant.value = unit_price * quant.quantity
    #         else:
    #             quant.value = quant.lot_id.inventory_value
    #     else:
    #         quants += quant
    # return super(StockQuant, quants)._compute_value()
    #     quant.value = quant.price_unit *  quant.quantity
