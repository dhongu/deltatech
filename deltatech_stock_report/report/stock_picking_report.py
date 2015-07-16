# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 stock All Rights Reserved
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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import tools


class stock_picking_report(osv.osv):
    _name = "stock.picking.report"
    _description = "Stock picking report"
    _auto = False

    _columns = {

        'partner_id': fields.many2one(  'res.partner', 'Partner', readonly=True),
        'picking_type_id':fields.many2one( 'stock.picking.type', 'Picking Type', readonly=True),
        
        'picking_type_code': fields.related('picking_type_id', 'code', type='char', string='Picking Type Code',readonly=True),  
              
        'date': fields.datetime('Date',  readonly=True),

        'invoice_state': fields.selection([  ("invoiced", "Invoiced"), 
                                             ("2binvoiced", "To Be Invoiced"), 
                                             ("none", "Not Applicable")
                                         ], string="Invoice Control", readonly=True ),
                 
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        
        'categ_id': fields.many2one(  'product.category', 'Category', readonly=True),
        'product_id': fields.many2one( 'product.product', 'Product', readonly=True),
        'product_uom': fields.many2one( 'product.uom', 'Unit of Measure', required=True),
               
        'location_id': fields.many2one( 'stock.location', 'Location', readonly=True, select=True),
        'location_dest_id': fields.many2one( 'stock.location', 'Location Destination', readonly=True, select=True),
        


        'product_qty': fields.float(  'Quantity',   digits_compute=dp.get_precision('Product UoM'), readonly=True ),
        'amount': fields.float(   'Amount',  digits_compute=dp.get_precision('Account'), readonly=True ),

        

    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'stock_picking_report')
        cr.execute("""
         create or replace view stock_picking_report as (

select min(1000000*sp.id+1000*sm.id+sq.id) as id,
sp.partner_id, sp.picking_type_id,   sp.state, sp.date,  sp.invoice_state, sp.company_id,
pt.categ_id, sm.product_id,  pt.uom_id as product_uom,
sm.location_id,sm.location_dest_id,
sum(sq.qty) as product_qty, 
sum(sq.qty*sq.cost) as amount

from stock_picking as sp
 
join stock_move as sm on sp.id = sm.picking_id
join stock_quant_move_rel on sm.id = stock_quant_move_rel.move_id
join stock_quant as sq on stock_quant_move_rel.quant_id = sq.id
LEFT JOIN product_product pp ON  sm.product_id = pp.id
LEFT JOIN product_template pt ON  pp.product_tmpl_id = pt.id

where sm.state  = 'done'
group by sp.partner_id, sp.picking_type_id,   sp.state, sp.date,   sp.invoice_state,sp.company_id,
pt.categ_id, sm.product_id,  pt.uom_id ,
sm.location_id,sm.location_dest_id


        )""")

 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
