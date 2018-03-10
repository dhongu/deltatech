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

from odoo import models, fields, api, _
from odoo import tools
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError


# TODO: de citit coeficientul  din BOM




class deltatech_mrp_report(models.Model):
    _name = "deltatech.mrp.report"
    _description = "Production Cost Analysis"
    _auto = False

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        res = super(deltatech_mrp_report, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                           orderby=orderby, lazy=lazy)

        prod_dict = {}
        if 'standard_price' in fields or 'product_val' in fields or 'consumed_raw_val' in fields or 'consumed_pak_val' in fields or 'consumed_sem_val' in fields:
            for line in res:

                lines = self.search(line.get('__domain', []))
                standard_price = 0.0
                itmes = 0
                product_val = 0


                lines_rec = lines
                for line_rec in lines_rec:
                    if line_rec.product_id.cost_method == 'fifo':
                        price = line_rec.price_unit_on_quant
                    else:
                        if not line_rec.product_id.id in prod_dict:
                            prod_dict[line_rec.product_id.id] = line_rec.product_id.get_history_price(

                                line_rec.company_id.id,
                                date=line_rec.date)

                        price = prod_dict[line_rec.product_id.id]
                    standard_price += price
                    product_val += line_rec.product_qty * price
                    itmes += 1

                if itmes > 0:
                    line['standard_price'] = standard_price / itmes
                    line['product_val'] = product_val

        return res






    production_id = fields.Many2one('mrp.production', 'Production Order', select=True)
    date = fields.Date('Date', readonly=True)

    categ_id = fields.Many2one('product.category', 'Category', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', required=True)

    product_qty = fields.Float('Qty Plan', digits=dp.get_precision('Product UoM'), readonly=True)
    product_val = fields.Float(compute="_compute_product_val", string="Val Plan", readonly=True)
    product_qty_ef = fields.Float('Qty Efective', digits=dp.get_precision('Product UoM'), readonly=True)
    product_val_ef = fields.Float('Val Efective', digits=dp.get_precision('Account'), readonly=True)

    consumed_val = fields.Float('Val Consumed', digits=dp.get_precision('Account'), readonly=True)
    consumed_raw_val = fields.Float('Val Consumed Raw', digits=dp.get_precision('Account'), readonly=True)
    consumed_pak_val = fields.Float('Val Consumed Packing', digits=dp.get_precision('Account'), readonly=True)
    consumed_sem_val = fields.Float('Val Consumed Semifinish', digits=dp.get_precision('Account'),
                                    readonly=True)


    val_prod = fields.Float('Value production', digits=dp.get_precision('Account'), readonly=True)

    standard_price = fields.Float(compute="_compute_product_val", string="Price Standard", type='float', readonly=True)

    actually_price = fields.Float('Actually Price', digits=dp.get_precision('Account'), readonly=True,
                                  group_operator="avg")

    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    #        'origin': fields.char('Source Document', size=64)
    nbr = fields.Integer('# of Orders', readonly=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('picking_except', 'Picking Exception'),
                              ('confirmed', 'Waiting Goods'),
                              ('ready', 'Ready to Produce'),
                              ('in_production', 'In Production'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done')],
                             'State', readonly=True)

    @api.multi
    def _compute_product_val(self):
        for line in self:
            price =  line.product_id.get_history_price(line.company_id.id, date=line.date)
            line.standard_price = price
            line.product_val = line.product_qty * price

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'deltatech_mrp_report')
        self.env.cr.execute("""
            create or replace view deltatech_mrp_report as (
 

 SELECT s.id, s.id as production_id, 
    pt.categ_id,
    to_date(to_char(s.date_planned_start, 'MM-dd-YYYY'::text), 'MM-dd-YYYY'::text) AS date,
 
    s.product_id,
    pt.uom_id AS product_uom_id,
    sum((s.product_qty / u.factor)) AS product_qty,
    sum(sub_prod_ef.product_qty_ef) AS product_qty_ef,
    sum(sub_prod_ef.product_val_ef) AS product_val_ef,
    sum(COALESCE(sub_consumed.consumed_val, (0)::double precision)) AS consumed_val,

    sum(COALESCE(sub_consumed.consumed_pak_val, (0)::double precision)) AS consumed_pak_val,
    sum(COALESCE(sub_consumed.consumed_raw_val, (0)::double precision)) AS consumed_raw_val,
    sum(COALESCE(sub_consumed.consumed_sem_val, (0)::double precision)) AS consumed_sem_val,

    (sum(COALESCE(sub_consumed.consumed_val, (0)::double precision)) * (1.20)::double precision) AS val_prod,
    ((sum(COALESCE(sub_consumed.consumed_val, (0)::double precision)) * (1.20)::double precision) / (COALESCE(sum(sub_prod_ef.product_qty_ef), 0.0000001))::double precision) AS actually_price,
    s.company_id,
    ( SELECT 1) AS nbr,
    s.state
   FROM ((((((mrp_production s
     
     JOIN product_product  pr ON s.product_id = pr.id 
         JOIN product_template pt ON pr.product_tmpl_id = pt.id )            
     LEFT JOIN product_uom u ON ((u.id = s.product_uom_id)))
     LEFT JOIN ( SELECT sm.production_id,
            sum(sm.product_qty) AS product_qty_ef,
            sum((q.qty * q.cost)) AS product_val_ef,
            sm.procure_method
           FROM ((stock_move sm
             LEFT JOIN stock_quant_move_rel ON ((stock_quant_move_rel.move_id = sm.id)))
             LEFT JOIN stock_quant q ON ((stock_quant_move_rel.quant_id = q.id)))
          WHERE ((sm.state)::text = 'done'::text)
          GROUP BY sm.production_id, sm.procure_method) sub_prod_ef ON ((sub_prod_ef.production_id = s.id)))




left join (
SELECT 
    sm.raw_material_production_id AS production_id,
    SUM (q.qty * q.COST) AS consumed_val,
      CASE WHEN pc.cost_categ='semi' THEN SUM (q.qty * q.COST) else 0.0 end as  consumed_sem_val,
      CASE WHEN pc.cost_categ='pak' THEN SUM (q.qty * q.COST) else 0.0 end as  consumed_pak_val,
        CASE WHEN pc.cost_categ='raw' THEN SUM (q.qty * q.COST) else 0.0 end as  consumed_raw_val
FROM
    stock_move sm
    LEFT JOIN stock_quant_move_rel ON stock_quant_move_rel.move_id = sm.id
    LEFT JOIN stock_quant q ON stock_quant_move_rel.quant_id = q.id
    LEFT JOIN product_product pr ON pr. ID = sm.product_id
    LEFT JOIN product_template pt ON pt. ID = pr.product_tmpl_id
    LEFT JOIN product_category pc ON pc. ID = pt.categ_id
WHERE
    q.qty > 0
    AND raw_material_production_id IS NOT NULL

    AND sm.state = 'done' :: TEXT
GROUP BY
    sm.raw_material_production_id, pc.cost_categ) sub_consumed ON ((sub_consumed.production_id = s.id)))

)
    
)
 
 GROUP BY
 
 to_date(to_char(s.date_planned_start, 'MM-dd-YYYY'::text), 'MM-dd-YYYY'::text),
 s.product_id, 
 pt.categ_id, pt.uom_id,  s.id, s.state, s.company_id
                                               
            )""")
