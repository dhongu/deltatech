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



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


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


    @api.model
    def quants_move(self, quants, move, location_to, location_from=False, lot_id=False, owner_id=False, src_package_id=False, dest_package_id=False, entire_pack=False):
        """Moves all given stock.quant in the given destination location.  Unreserve from current move.
        :param quants: list of tuple(browse record(stock.quant) or None, quantity to move)
        :param move: browse record (stock.move)
        :param location_to: browse record (stock.location) depicting where the quants have to be moved
        :param location_from: optional browse record (stock.location) explaining where the quant has to be taken
                              (may differ from the move source location in case a removal strategy applied).
                              This parameter is only used to pass to _quant_create_from_move if a negative quant must be created
        :param lot_id: ID of the lot that must be set on the quants to move
        :param owner_id: ID of the partner that must own the quants to move
        :param src_package_id: ID of the package that contains the quants to move
        :param dest_package_id: ID of the package that must be set on the moved quant
        """


        if location_to.usage == 'internal' and location_to.value_limit > 0: 
            new_value = location_to.actual_value  
            for quant, qty in quants:
                if quant:
                    new_value += quant.inventory_value
            if new_value > location_to.value_limit:
                raise Warning(_('Exceeding the limit value stock!'))              
        super(stock_quant, self).quants_move( quants, move, location_to, location_from, lot_id, owner_id, src_package_id, dest_package_id, entire_pack)

    
   
    
          
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
