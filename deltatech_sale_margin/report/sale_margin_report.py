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


class _sale_margin_report(osv.osv):
    _name = "sale.margin.report"
    _description = "Sale margin report"
    _auto = False


    _columns = {
        
        'date': fields.date('Date', readonly=True),
         
        'categ_id': fields.many2one('product.category', 'Category', readonly=True), 
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True),
        'product_uom_qty': fields.float('Quantity', readonly=True),
        'sale_val': fields.float('Sale value', readonly=True),
 
        'stock_val': fields.float("Stock value",  readonly=True),
        'profit_val': fields.float("Profit",   readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'commercial_partner_id': fields.many2one('res.partner', 'Commercial Partner', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),
        'company_id': fields.many2one('res.company','Company',readonly=True), 
        
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Done'),
            ('cancel','Cancelled')
            ], 'Invoice Status', readonly=True),
 
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_margin_report')
        cr.execute("""

         create or replace view sale_margin_report as (
                select
                    min(l.id) as id,
                    s.date_invoice as date,               
                                     
                    t.categ_id as categ_id,                    
                    l.product_id as product_id,
                    t.uom_id as product_uom,
      
                    sum(l.quantity / u.factor * u2.factor) as product_uom_qty,
                    sum(l.quantity * l.price_unit * (100.0-l.discount) / 100.0) as sale_val,
                    sum(l.quantity * l.purchase_price ) as stock_val,    
                                   
                    sum ( (l.quantity * l.price_unit * (100.0-l.discount) / 100.0) - (l.quantity * l.purchase_price )) as profit_val,  
                    
                    s.partner_id as partner_id,
                    s.commercial_partner_id as commercial_partner_id,
                    s.user_id as user_id,
                     
                    s.company_id as company_id,
                    s.type,
                    s.state 

                from
                    account_invoice s
                    left join account_invoice_line l on (s.id=l.invoice_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.uos_id)
                    left join product_uom u2 on (u2.id=t.uom_id)

                where s.type in ( 'out_invoice', 'out_refund')

                group by
                    l.product_id,
                    l.invoice_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_invoice,
                    s.partner_id,
                    s.commercial_partner_id,
                    s.user_id,
                    s.company_id,
                    s.type,
                    s.state
 
       ) """)
 




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

