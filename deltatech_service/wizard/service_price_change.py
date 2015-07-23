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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class service_price_change(models.TransientModel):
    _name = 'service.price.change'
    _description = "Service price change"
 
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
 
    product_id = fields.Many2one('product.product', string='Product',required=True,  domain=[('type', '=', 'service')] )

    price_unit = fields.Float(string='Unit Price', required=True, digits= dp.get_precision('Product Price') ) 

    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=_default_currency) 


    @api.model
    def default_get(self, fields):
        defaults = super(service_price_change, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', False) 
        if active_ids:
            cons = self.env['service.consumption'].browse(active_ids[0])
            defaults['product_id'] = cons.product_id.id
            defaults['price_unit'] = cons.price_unit
            defaults['currency_id'] = cons.currency_id.id
        return defaults   


    @api.onchange('product_id')
    def onchange_scanned_ean(self):
        price_unit = self.product_id.list_price
        self.price_unit = self.env.user.company_id.currency_id.compute(price_unit, self.currency_id )
         

    @api.multi
    def do_price_change(self):
        active_ids = self.env.context.get('active_ids', False)
        print active_ids
        if active_ids:
            domain=[('invoice_id', '=', False),('product_id','=', self.product_id.id),('id','in', active_ids )]   
        else:
            domain=[('invoice_id', '=', False),('product_id','=', self.product_id.id)]
            
        consumptions = self.env['service.consumption'].search(domain)
        
        if not consumptions:
            raise except_orm(_('No consumptions!'),
                             _("There were no service consumption !"))
            
        consumptions.write({'price_unit':self.price_unit, 'currency_id':self.currency_id.id  })
        
        price_unit = self.currency_id.compute(self.price_unit, self.env.user.company_id.currency_id )
       
        self.product_id.write({'list_price':price_unit})
        
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