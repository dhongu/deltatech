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


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def create(self, vals):
        if vals.get("lot_name", False) == "/":
            vals["lot_name"] = self.env["ir.sequence"].next_by_code("stock.lot.serial")
        return super(StockMoveLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("lot_name", False) == "/":
            vals["lot_name"] = self.env["ir.sequence"].next_by_code("stock.lot.serial")
        return super(StockMoveLine, self).write(vals)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
