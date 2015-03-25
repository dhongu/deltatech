# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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



from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


class stock_location(models.Model):
    _inherit = "stock.location"

    @api.one
    def _compute_actual_value(self):
        value = 0
        quants = self.env['stock.quant'].search([('location_id','=',self.id)]) 
        for quant in quants:
            value +=  quant.inventory_value
        self.actual_value = value

    value_limit = fields.Float(string='Value Limit', digits= dp.get_precision('Product Price'))  
    actual_value = fields.Float(string='Actual Value', digits= dp.get_precision('Product Price'), compute='_compute_actual_value')   


class stock_quant(models.Model):
    _inherit = "stock.quant"


    def quants_move(self, cr, uid, quants, move, location_to, location_from=False, lot_id=False, owner_id=False, src_package_id=False, dest_package_id=False, context=None):
        """Moves all given stock.quant in the given destination location.  Unreserve from current move.
        """
        if location_to.usage == 'internal' and location_to.value_limit > 0: 
            new_value = location_to.actual_value  
            for quant, qty in quants:
                new_value += quant.inventory_value
            if new_value > location_to.value_limit:
                raise Warning(_('Exceeding the limit value stock!'))              
        super(stock_quant, self).quants_move(cr, uid, quants, move, location_to, location_from, lot_id, owner_id, src_package_id, dest_package_id, context)
        return       
    
   
    
          
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
