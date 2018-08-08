# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def create(self, vals):
        if vals.get('lot_name', False) == '/':
            vals['lot_name'] = self.env['ir.sequence'].next_by_code('stock.lot.serial')
        return super(StockMoveLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('lot_name', False) == '/':
            vals['lot_name'] = self.env['ir.sequence'].next_by_code('stock.lot.serial')
        return super(StockMoveLine, self).write(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
