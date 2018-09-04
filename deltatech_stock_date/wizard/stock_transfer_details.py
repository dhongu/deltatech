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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'
    
    date = fields.Datetime(string="Date",related='picking_id.date', store=False)
    
    """
    @api.model
    def default_get(self, fields):      
        res = super(stock_transfer_details, self).default_get(fields)
        if res['picking_id']:
            picking = self.env['stock.picking'].browse(res['picking_id'])
            if picking:
                res['date'] = picking.date
        return res
    """

    @api.one
    def do_detailed_transfer(self):   
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                prod.write({'date':self.date})
            
            
        res =  super(stock_transfer_details, self).do_detailed_transfer() 
        return   res 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
