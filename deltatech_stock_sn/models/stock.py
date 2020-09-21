# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, Warning, except_orm
from odoo.tools import float_compare

import odoo.addons.decimal_precision as dp


class stock_location(models.Model):
    _inherit = "stock.location"

    hide_lot = fields.Boolean(string="Hide Lot", default=True)  # ascunde loturile ce se afla in aceasta locatie

    @api.onchange("usage", "hide_lot")
    def onchange_hide_lot(self):
        if self.usage == "internal":
            self.hide_lot = False

        # pentru poturile existente trebuie rulat
        # quants = self.env['stock.qunat'].search([('location_id', '=', self.id), ('lot_id', '!=', False)])


class stock_production_lot(models.Model):
    _inherit = "stock.production.lot"

    active = fields.Boolean(
        string="Active",
        compute="_compute_stock_available",
        store=True,
        help="By unchecking the active field, you may hide an Lot Number without deleting it.",
        defualt=True,
    )

    stock_available = fields.Float(
        string="Available",
        compute="_compute_stock_available",
        store=True,
        help="Current quantity of products with this Serial Number available in company warehouses",
        digits=dp.get_precision("Product Unit of Measure"),
    )

    @api.multi
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
