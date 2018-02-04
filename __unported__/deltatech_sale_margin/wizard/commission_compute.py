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

class commission_compute(models.TransientModel):
    _name = 'commission.compute'
    _description = "Compute commission"

    
    invoice_line_ids = fields.Many2many('sale.margin.report', 'commission_compute_inv_rel', 'compute_id','invoice_line_id', 
                                        string='Account invoice line')    


   
    @api.model
    def default_get(self, fields):      
        defaults = super(commission_compute, self).default_get(fields)
          
        active_ids = self.env.context.get('active_ids', False)
        
        if active_ids:
            domain=[('id','in', active_ids )]   
        else:
            domain=[('state', '=', 'paid'),('commission','=',0.0)]
        res = self.env['sale.margin.report'].search(domain)
        defaults['invoice_line_ids'] = [ (6,0,[rec.id for rec in res]) ]
        return defaults   
     

    @api.multi
    def do_compute(self):
        res = []
        for line in self.invoice_line_ids:
            value = {'commission':line.commission_computed}
            #if line.purchase_price == 0 and line.product_id:
            #    value['purchase_price'] = line.product_id.standard_price
            
            line.write(value)
            res.append(line.id)  
        return {
            'domain': "[('id','in', ["+','.join(map(str,res))+"])]",
            'name': _('Commission'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.margin.report',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
