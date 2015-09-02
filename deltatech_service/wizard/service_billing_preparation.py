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

class service_billing_preparation(models.TransientModel):
    _name = 'service.billing.preparation'
    _description = "Service Billing Preparation"
    
    
    period_id = fields.Many2one('account.period', string='Period', domain=[('state', '!=', 'done')],required=True,) 
    
    
    agreement_ids = fields.Many2many('service.agreement', 'service_billing_agreement', 'billing_id','agreement_id', 
        string='Agreements', domain=[('state', '=', 'open')])
    
  
    @api.model
    def default_get(self, fields):      
        defaults = super(service_billing_preparation, self).default_get(fields)
          
        active_ids = self.env.context.get('active_ids', False)
         
        if active_ids:
            domain=[('state', '=', 'open'),('id','in', active_ids )]   
        else:
            domain=[('state', '=', 'open')]
        res = self.env['service.agreement'].search(domain)
        defaults['agreement_ids'] = [ (6,0,[rec.id for rec in res]) ]
        return defaults
        

    @api.multi
    def do_billing_preparation(self):
        res = []
        for agreement in self.agreement_ids:
            for line in agreement.agreement_line:
                cons_value = line.get_value_for_consumption()
                if cons_value:
                    cons_value.update({
                          'partner_id' : agreement.partner_id.id,
                          'period_id':   self.period_id.id,   
                          'agreement_id': agreement.id,
                          'agreement_line_id': line.id,
                    }) 
                    consumption = self.env['service.consumption'].create(cons_value) 
                    res.append(consumption.id)  
        return {
            'domain': "[('id','in', ["+','.join(map(str,res))+"])]",
            'name': _('Service Consumption'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.consumption',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 