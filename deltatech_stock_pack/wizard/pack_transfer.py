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



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp

 

class stock_pack_transfer(models.TransientModel):
    _name = 'stock.pack.transfer'
    _description = "Transfer Pack"
    
    # data ? pentru data la care sa se faca transferul?
    location_dest_id = fields.Many2one('stock.location', required=True, string="Destination Location Zone" )
    picking_type_id = fields.Many2one('stock.picking.type', required=True, string="Picking Type")
    date            = fields.Datetime(string="Date", default=fields.Datetime.now())
 
    @api.multi
    def do_transfer(self):
        active_ids = self.env.context.get('active_ids', False)
        packages = self.env['stock.quant.package'].browse(active_ids)
        location_dest_id =  self.location_dest_id
        picking = self.env['stock.picking'].create({'picking_type_id':self.picking_type_id.id,
                                                    'date':self.date,
                                                    'min_date':self.date,
                                                    'state':'assigned'})
        for package in packages:
            for quant in package.quant_ids:
                move = self.env['stock.move'].create({  
                                             'picking_id':picking.id,
                                             'state':'assigned',
                                             'product_id':quant.product_id.id,
                                             'product_uom_qty':quant.qty,
                                             'package_id':quant.package_id.id,
                                             'location_id':quant.location_id.id,
                                             'location_dest_id':location_dest_id.id,
                                             'name':quant.product_id.name,
                                             'product_uom':quant.product_id.uom_id.id,
                                             'date':self.date,
                                             'date_expected':self.date,
                                             #'quant_ids':[(6,0,[quant.id])]
                                             })
                quant.write({'reservation_id':move.id})
        

        #wizard = self.env['stock.transfer_details'].with_context(active_model='stock.picking',
        #                                                         active_ids=[picking.id]).create({'picking_id':picking.id})
 
 
        picking.do_prepare_partial()
        picking.do_transfer()
                
            
        return {
            'domain': "[('id','=', "+str(picking.id)+")]",
            'name': _('Pack Transfer'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
               






# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: