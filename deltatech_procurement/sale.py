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


class sale_order(models.Model):
    _inherit = 'sale.order' 


    @api.one
    @api.depends('order_line.procurement_ids' )
    def _compute_procurement_count(self):           
        value = 0 
        procurements = self.env['procurement.order']
        for sale in self:
            for line in sale.order_line:
                for procurement in line.procurement_ids:
                    procurements = procurements | procurement 
                 
        self.procurement_count = len(procurements)


    @api.one
    def _compute_invoiced_rate(self):   

        if self.currency_id:
            to_currency = self.currency_id
        else:
            to_currency = self.env.user.company_id.currency_id
 
        if self.amount_untaxed:   
            invoice_tot = 0.0     
            for invoice in self.invoice_ids:
                if invoice.state not in ('draft','cancel'):
                    if invoice.currency_id:
                        from_currency = invoice.currency_id.with_context(date=invoice.date_invoice)
                    else:    
                        from_currency = self.env.user.company_id.currency_id.with_context(date=invoice.date_invoice)
                         
                    invoice_tot += from_currency.compute(invoice.amount_untaxed, to_currency )
                    
            self.invoiced_rate =   invoice_tot * 100.0 / (self.amount_untaxed) 
        else:
            self.invoiced_rate = 0.0


    procurement_count =  fields.Integer(string='Procurements',  compute='_compute_procurement_count')
    invoiced_rate = fields.Float(  string='Invoiced',compute='_compute_invoiced_rate' ) 

    def view_procurement(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing procurement of given purchase order ids.
        '''
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        dummy, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'procurement', 'procurement_action'))
        action = self.pool.get('ir.actions.act_window').read(cr, uid, action_id, context=context)

        procurement_ids = []
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.order_line:
                procurement_ids += [procurement.id for procurement in line.procurement_ids]

        action['context'] = {}
         
        if len(procurement_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, procurement_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'procurement', 'procurement_form_view')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = procurement_ids and procurement_ids[0] or False
        return action      
    
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
