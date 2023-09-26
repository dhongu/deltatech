# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    hide_lot = fields.Boolean(string="Hide Lot", default=True)  # ascunde loturile ce se afla in aceasta locatie

    @api.onchange("usage", "hide_lot")
    def onchange_hide_lot(self):
        if self.usage == "internal":
            self.hide_lot = False


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    active = fields.Boolean(
        string="Active",
        compute="_compute_stock_available",
        store=True,
        help="By unchecking the active field, you may hide an Lot Number without deleting it.",
        default=True,
    )

    stock_available = fields.Float(
        string="Available",
        compute="_compute_stock_available",
        store=True,
        help="Current quantity of products with this Serial Number available in company warehouses",
        digits="Product Unit of Measure",
    )

    @api.depends("quant_ids.quantity", "quant_ids.location_id")
    def _compute_stock_available(self):
        for lot in self:
            available = 0.0
            show_lots = 0.0
            for quant in lot.quant_ids:
                if quant.location_id.usage == "internal" or not quant.location_id.hide_lot:
                    show_lots += quant.quantity
                    if quant.location_id.usage == "internal":
                        available += quant.quantity
            if show_lots > 0:
                lot.active = True
            else:
                lot.active = False
            lot.stock_available = available
