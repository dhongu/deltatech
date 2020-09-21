# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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
import odoo.addons.decimal_precision as dp

class stock_quant_change_lot(models.TransientModel):
    _name = 'stock.quant.change.lot'
    _description = "Stock Quant Change Lot"

    product_id = fields.Many2one('product.product', readonly=True) 
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')


    
    @api.model
    def default_get(self, fields): 
        defaults = super(stock_quant_change_lot, self).default_get(fields)         
        active_id = self.env.context.get('active_id', False)
        if active_id:
            quant = self.env['stock.quant'].browse(active_id)
            if quant.lot_id:
                defaults['lot_id'] = quant.lot_id.id
            defaults['product_id'] =  quant.product_id.id
        return defaults
    
    
    @api.multi
    def do_change_number(self):
        active_id = self.env.context.get('active_id', False)
        if active_id:
            quant = self.env['stock.quant'].browse(active_id)
            quant.write({'lot_id':self.lot_id.id })



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
