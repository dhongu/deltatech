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

from openerp.osv import fields,osv
from openerp import tools
import openerp.addons.decimal_precision as dp


class deltatech_sale_report(osv.osv):
    _name = "deltatech.sale.report"
    _description = "Deltatech sale report"
    _auto = False



    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(deltatech_sale_report, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        if context is None:
            context = {}
        
        prod_dict = {}
        if 'stock_val' in fields or 'profit_val' in fields:
            for line in res:
                lines = self.search(cr, uid, line.get('__domain', []), context=context)
                inv_value = 0.0
                sale_val = 0.0 
                product_tmpl_obj = self.pool.get("product.template")
                lines_rec = self.browse(cr, uid, lines, context=context)
                for line_rec in lines_rec:
                    if line_rec.product_id.cost_method == 'real':
                        #price = line_rec.price_unit_on_quant
                        # trbuie sa determin care este miscare cu care a fost facuta iesire din stoc si de acolo sa gasesc care e quntul din care sa citesc pretul!!! fack!
                        if not line_rec.product_id.id in prod_dict:
                            prod_dict[line_rec.product_id.id] = product_tmpl_obj.get_history_price(cr, uid, line_rec.product_id.product_tmpl_id.id, line_rec.company_id.id, date=line_rec.date, context=context)
                        price = prod_dict[line_rec.product_id.id]
                    else:
                        if not line_rec.product_id.id in prod_dict:
                            prod_dict[line_rec.product_id.id] = product_tmpl_obj.get_history_price(cr, uid, line_rec.product_id.product_tmpl_id.id, line_rec.company_id.id, date=line_rec.date, context=context)
                        price = prod_dict[line_rec.product_id.id]
                    inv_value += price * line_rec.product_uom_qty
                    sale_val += line_rec.sale_val
                line['stock_val'] = inv_value
                line['profit_val'] = sale_val - inv_value
        return res

    def _get_stock_val(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_tmpl_obj = self.pool.get("product.template")
            price_unit = product_tmpl_obj.get_history_price(cr, uid, line.product_id.product_tmpl_id.id,
                                                                      line.company_id.id, date=line.date, context=context)
            res[line.id] = line.product_uom_qty * price_unit
        return res

    def _get_profit_val(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.sale_val - line.stock_val
        return res

 
    _columns = {
        
        'date': fields.datetime('Date',size=6,readonly=True),
         
        'categ_id': fields.many2one('product.category', 'Category', readonly=True), 
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True),
        'product_uom_qty': fields.float('Quantity', readonly=True),
        'sale_val': fields.float('Sale value', readonly=True),
 
        'stock_val': fields.function(_get_stock_val, string="Stock value", type='float', readonly=True),
        'profit_val': fields.function(_get_profit_val, string="Profit", type='float', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),
        'company_id': fields.many2one('res.company','Company',readonly=True), 
        'nbr': fields.integer('# of Lines', readonly=True),
        'state': fields.selection([
            ('draft', 'Quotation'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'Manual In Progress'),
            ('progress', 'In Progress'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
            ], 'Order Status', readonly=True),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True),  
 
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'deltatech_sale_report')
        cr.execute("""

         create or replace view deltatech_sale_report as (
                select
                    min(l.id) as id,
                    s.date_order as date,               

                                     
                    t.categ_id as categ_id,                    
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as sale_val,
                    
                    count(*)  as nbr,

                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.warehouse_id as warehouse_id,
                    s.company_id as company_id,
                   
                    s.state,
                   
                    s.pricelist_id as pricelist_id
                  
                from
                    sale_order s
                    left join sale_order_line l on (s.id=l.order_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)



                group by
                    l.product_id,
                    l.product_uom_qty,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.warehouse_id,
                    s.company_id,
                    s.state,
                    s.pricelist_id,
                    s.project_id
 
       ) """)
 




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

