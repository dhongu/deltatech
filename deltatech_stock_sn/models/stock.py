# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging





class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
      
    active = fields.Boolean(string='Active', compute="_compute_stock_available", store = True,
                            help="By unchecking the active field, you may hide an Lot Number without deleting it.", defualt=True)

    stock_available =  fields.Float( string="Available", compute="_compute_stock_available", store = True,
            help="Current quantity of products with this Serial Number available in company warehouses",
            digits=dp.get_precision('Product Unit of Measure'))


    @api.multi
    @api.depends('quant_ids.qty','quant_ids.location_id')
    def _compute_stock_available(self):
        for lot in self:
            available = 0.0
            for quant in lot.quant_ids:
                if quant.location_id.usage == 'internal':
                    available += quant.qty
            if available <> 0:
                lot.active = True
            else:
                lot.active = False
            lot.stock_available = available
    

    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: