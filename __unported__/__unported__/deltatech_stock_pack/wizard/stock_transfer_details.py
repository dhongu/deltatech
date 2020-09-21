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

 
class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'
    

    weight = fields.Float('Gross Weight', digits=dp.get_precision('Stock Weight'), help="The gross weight in Kg.", related="result_package_id.weight")
    
    @api.multi
    def put_in_pack(self):
        newpack = None
        pack_no = 1
        for packop in self:           
            if not packop.result_package_id:
                if not newpack:
                    if packop.product_id.pack_items:
                        pack_no = int(packop.quantity / packop.product_id.pack_items)  
                    newpack = self.pool['stock.quant.package'].create(self._cr, self._uid, {'location_id': packop.destinationloc_id.id if packop.destinationloc_id else False}, self._context)
                    packop.result_package_id = newpack
                    quantity = packop.quantity 
                    packop.weight =  quantity * packop.product_id.pack_weight / packop.product_id.pack_items
                if pack_no>1:
                    
                    packop.quantity = packop.product_id.pack_items
                    packop.weight = packop.product_id.pack_weight
                    for x in range(0, pack_no):
                        quantity =  quantity - packop.product_id.pack_items
                        if quantity > 0:
                            newpack = self.pool['stock.quant.package'].create(self._cr, self._uid, {'location_id': packop.destinationloc_id.id if packop.destinationloc_id else False}, self._context) 
                            
                            if quantity > packop.product_id.pack_items:
                                new_id = packop.copy({'quantity':packop.product_id.pack_items,
                                                      'packop_id':False,
                                                      'weight': packop.product_id.pack_weight,
                                                      'result_package_id':newpack}, context=self.env.context)
                            else:
                            
                                new_id = packop.copy({'quantity':quantity, 'packop_id':False,
                                                      'weight': quantity * packop.product_id.pack_weight / packop.product_id.pack_items ,
                                                      'result_package_id':newpack}, context=self.env.context)
                           
                        
                    
        return super(stock_transfer_details_items, self).put_in_pack()
 