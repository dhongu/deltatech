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
        'picking_id':fields.many2one('stock.picking', 'Picking', readonly=True),
        
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
        'price': fields.float(   'Price Unit',  digits_compute=dp.get_precision('Account'), readonly=True, group_operator="avg"),
        'amount': fields.float(   'Amount',  digits_compute=dp.get_precision('Account'), readonly=True ),

        'commercial_partner_id' : fields.many2one('res.partner', string='Commercial Entity')
        

    }


    def _select(self):
        select_str = """
            SELECT min(sm.id) as id, sp.id as picking_id,
            sp.partner_id, rp.commercial_partner_id, sp.picking_type_id,   sp.state, sp.date,  sp.invoice_state, sp.company_id,
            pt.categ_id, sm.product_id,  pt.uom_id as product_uom,
            sm.location_id,sm.location_dest_id,
            sum(sq.qty) as product_qty, 
            avg(sq.cost) as price,
            sum(sq.qty*sq.cost) as amount
        """
        return select_str



    def _from(self):
        from_str = """
            FROM stock_picking as sp
            LEFT JOIN res_partner as rp ON rp.id = sp.partner_id 
            LEFT JOIN stock_move as sm ON sp.id = sm.picking_id
            LEFT JOIN stock_quant_move_rel ON sm.id = stock_quant_move_rel.move_id
            LEFT JOIN stock_quant as sq ON stock_quant_move_rel.quant_id = sq.id
            LEFT JOIN product_product as pp ON  sm.product_id = pp.id
            LEFT JOIN product_template as pt ON  pp.product_tmpl_id = pt.id

        """
        return from_str


    def _group_by(self):
        group_by_str = """
            GROUP BY sp.id, sp.partner_id,rp.commercial_partner_id, sp.picking_type_id,   sp.state, sp.date,   sp.invoice_state,sp.company_id,
            pt.categ_id, sm.product_id,  pt.uom_id ,
            sm.location_id,sm.location_dest_id
        """
        return group_by_str


    def init(self, cr):

        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            %s 
            WHERE sm.state  = 'done'
            %s
        )""" % ( self._table,  self._select(), self._from(), self._group_by() ) )
                   
        
        

 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
