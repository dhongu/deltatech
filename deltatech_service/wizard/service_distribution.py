# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class service_distribution(models.TransientModel):
    _name = 'service.distribution'
    _description = "Service distribution"
 
    product_id = fields.Many2one('product.product', string='Product',required=True,  domain=[('type', '=', 'service')] )
    quantity = fields.Float(string='Quantity', required=True,digits= dp.get_precision('Product Unit of Measure') )
    mode = fields.Selection([
                             ('divide','Divide'),
                             ('fix','Fix'),
                             ], string = "Mode", required=True, default='fix')
          
    @api.model
    def default_get(self, fields):
        defaults = super(service_distribution, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', False) 
        if active_ids:
            cons = self.env['service.consumption'].browse(active_ids[0])
            defaults['product_id'] = cons.product_id.id
            defaults['quantity'] = cons.quantity
 
        return defaults   
    
    @api.multi
    def do_distribution(self):
        
        active_ids = self.env.context.get('active_ids', False)
        #print active_ids
        if active_ids:
            domain=[('invoice_id', '=', False),('product_id','=', self.product_id.id),('id','in', active_ids )]   
        else:
            domain=[('invoice_id', '=', False),('product_id','=', self.product_id.id)]
            

        consumptions = self.env['service.consumption'].search(domain)
        
        if not consumptions:
            raise except_orm(_('No consumptions!'),
                             _("There were no service consumption !"))
        if self.mode == 'divide':
            qty = self.quantity / len(consumptions)
        else:
            qty = self.quantity 
        consumptions.write({'quantity':qty  })
        
        return {
            'domain': "[('id','in', ["+','.join(map(str,[rec.id for rec in consumptions]))+"])]",
            'name': _('Service Consumption'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.consumption',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 