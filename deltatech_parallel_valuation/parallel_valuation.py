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

from openerp import models, fields, api, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment


class stock_history(models.Model):
    _inherit = "stock.history"

    @api.one
    @api.depends('inventory_value', 'date' )
    def _compute_parallel_inventory_value(self):           
 
        date_eval = self._context.get('history_date') # self.date or fields.Date.context_today(self) 
        from_currency = self.env.user.company_id.currency_id.with_context(date=date_eval)
        
        value =  from_currency.compute(self.inventory_value, self.env.user.company_id.parallel_currency_id )
        self.parallel_inventory_value = value


    parallel_inventory_value = fields.Float(string="Parallel Inventory Value", digits= dp.get_precision('Product Price'),
                                             readonly=True, compute='_compute_parallel_inventory_value')
    
     
    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(stock_history, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)

        if 'parallel_inventory_value' in fields and 'inventory_value' in fields:
            context['date'] = context.get('history_date')
            for line in res:
                
                with Environment.manage(): # class function
                    env = Environment(cr, uid, context)
                 
                line['parallel_inventory_value'] =  env.user.company_id.currency_id.compute( line['inventory_value'],  env.user.company_id.parallel_currency_id )
                
        return res    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





