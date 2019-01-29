# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details
 

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
