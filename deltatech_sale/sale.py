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


from openerp.osv import fields
from openerp.osv import osv
import openerp.pooler
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from openerp.tools.translate import _

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _prepare_procurement_group(self, cr, uid, order, context=None):
        rez = super(sale_order, self)._prepare_procurement_group(cr, uid, order, context)
        if order.client_order_ref:
            rez['name'] = rez['name'] + ' / ' + order.client_order_ref
        return rez


    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        rez = super(sale_order, self)._prepare_order_line_procurement(cr, uid, order, line, group_id, context)
        if order.client_order_ref:
            rez['origin'] = rez['origin'] + ' / ' + order.client_order_ref
        return rez

"""
    def action_ship_create(self, cr, uid, ids, context=None):

        res = super(sale_order, self).action_ship_create(cr, uid, ids, context)
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        for order in self.browse(cr, uid, ids, context):
            for line in order.order_line:
                date_planned = datetime.strptime(order.date_order , '%Y-%m-%d %H:%M:%S') + relativedelta(days=line.delay or 0.0)                
                date_planned = (date_planned - timedelta(days=company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
                for move in line.move_ids:
                    self.pool.get('stock.move').write(cr, uid, [move.id], {'date':date_planned, 'date_expected': date_planned}, context)
            for pick in order.picking_ids:
                self.pool.get('stock.picking').write(cr,uid,[pick.id],{'date':order.date_order}, context)
                
                
        return True
"""


sale_order()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    
    def button_confirm(self, cr, uid, ids, context=None):
        '''
            se verifica daca produsul are introdus un pret de lista (unul diferit de 1)
            se modifca pretul de lista a produsului cu pretul din comanda
        '''
        #TODO: de modificat daca lista de preturi are o anumita bifa!
        rez = super(sale_order_line, self).button_confirm(cr, uid, ids, context)
        product_obj = self.pool.get('product.product')       
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_id.list_price == 1:
                product_obj.write(cr,uid, [line.product_id.id],{'list_price':line.price_unit}, context={} )
            
        return rez
    
sale_order_line()    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
