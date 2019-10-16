# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models, fields, _, tools
import odoo.addons.decimal_precision as dp


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
                consumed_sem_val = 0
                consumed_pak_val = 0
                consumed_raw_val = 0

                for line_rec in lines:
                    if line_rec.product_id.cost_method == 'real':
                        price = line_rec.price_unit_on_quant
                    else:
                        if not line_rec.product_id.id in prod_dict:
                            prod_dict[line_rec.product_id.id] = line_rec.product_id.get_history_price(
                                line_rec.company_id.id, date=line_rec.date)
                        price = prod_dict[line_rec.product_id.id]
                    standard_price += price
                    product_val += line_rec.product_qty * price
                    itmes += 1
                '''
                for cost in  line_rec.production_id.cost_detail_ids:
                    if cost.cost_categ == 'semi':
                        consumed_sem_val += cost.amount
                    elif cost.cost_categ == 'pak':
                        consumed_pak_val += cost.amount
                    else:
                        consumed_raw_val += cost.amount                           
                '''
                if itmes > 0:
                    line['standard_price'] = standard_price / itmes
                    line['product_val'] = product_val

                    # line['consumed_sem_val'] = consumed_sem_val
                # line['consumed_pak_val'] = consumed_pak_val
                # line['consumed_raw_val'] = consumed_raw_val
        return res

    def _get_standard_price(self):
        res = {}
        for line in self:
            res[line.id] = line.product_id.get_history_price(line.company_id.id, date=line.date)
        return res

    def _get_product_val(self):
        res = {}
        for line in self:
            res[line.id] = line.product_qty * line.product_id.get_history_price(line.company_id.id, date=line.date)
        return res

    def _get_consumed(self):
        res = {}
        for line in self:
            res[line.id] = {'consumed_raw_val': 0.0, 'consumed_pak_val': 0.0, 'consumed_sem_val': 0.0}
            for cost in line.production_id.cost_detail_ids:
                if cost.cost_categ == 'semi':
                    res[line.id]['consumed_sem_val'] = cost.amount
                elif cost.cost_categ == 'pak':
                    res[line.id]['consumed_pak_val'] = cost.amount
                else:
                    res[line.id]['consumed_raw_val'] = cost.amount
        return res

    production_id = fields.Many2one('mrp.production', 'Production Order', index=True)
    date = fields.Date('Date', readonly=True)

    categ_id = fields.Many2one('product.category', 'Category', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True)

    product_qty = fields.Float('Qty Plan', digits=dp.get_precision('Product UoM'), readonly=True)
    product_val = fields.Float(compute='_get_product_val', string="Val Plan", readonly=True)
    product_qty_ef = fields.Float('Qty Efective', digits=dp.get_precision('Product UoM'), readonly=True)
    product_val_ef = fields.Float('Val Efective', digits=dp.get_precision('Account'), readonly=True)

    consumed_val = fields.Float('Val Consumed', digits=dp.get_precision('Account'), readonly=True)
    consumed_raw_val = fields.Float('Val Consumed Raw', digits=dp.get_precision('Account'), readonly=True)
    consumed_pak_val = fields.Float('Val Consumed Packing', digits=dp.get_precision('Account'), readonly=True)
    consumed_sem_val = fields.Float('Val Consumed Semifinish', digits=dp.get_precision('Account'), readonly=True)

    val_prod = fields.Float('Value production', digits=dp.get_precision('Account'), readonly=True)

    standard_price = fields.Float(compute="_get_standard_price", string="Price Standard", readonly=True)

    actually_price = fields.Float('Actually Price', digits_=dp.get_precision('Account'), readonly=True,
                                  group_operator="avg")

    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    #        origin = fields.char('Source Document', size=64)
    nbr = fields.Integer('# of Orders', readonly=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('picking_except', 'Picking Exception'),
                              ('confirmed', 'Waiting Goods'),
                              ('ready', 'Ready to Produce'),
                              ('in_production', 'In Production'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done')], 'State', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'deltatech_mrp_report')
        self.env.cr.execute("""
            create or replace view deltatech_mrp_report as (
 

SELECT s.id, s.id as production_id, 
    pt.categ_id,
    to_date(to_char(s.date_planned_start, 'MM-dd-YYYY'::text), 'MM-dd-YYYY'::text) AS date,
 
    s.product_id,
    pt.uom_id AS product_uom,
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
     LEFT JOIN uom_uom u ON ((u.id = s.product_uom_id)))
     LEFT JOIN ( SELECT sm.production_id,
            sum(sm.product_qty) AS product_qty_ef,
            sum(sm.value) AS product_val_ef,
            sm.procure_method
           FROM  stock_move sm
            
          WHERE ((sm.state)::text = 'done'::text)
          GROUP BY sm.production_id, sm.procure_method) sub_prod_ef ON ((sub_prod_ef.production_id = s.id)))

left join (
SELECT 
    sm.raw_material_production_id AS production_id,
   SUM (sm.value) AS consumed_val,
      CASE WHEN pc.cost_categ='semi' THEN SUM (sm.value) else 0.0 end as  consumed_sem_val,
      CASE WHEN pc.cost_categ='pak' THEN SUM (sm.value) else 0.0 end as  consumed_pak_val,
        CASE WHEN pc.cost_categ='raw' THEN SUM (sm.value) else 0.0 end as  consumed_raw_val
    FROM
        stock_move sm
        LEFT JOIN product_product pr ON pr. ID = sm.product_id
        LEFT JOIN product_template pt ON pt. ID = pr.product_tmpl_id
        LEFT JOIN product_category pc ON pc. ID = pt.categ_id
    WHERE
        raw_material_production_id IS NOT NULL
        AND sm.state = 'done' :: TEXT
    GROUP BY
        sm.raw_material_production_id, pc.cost_categ
    
    
    ) sub_consumed ON ((sub_consumed.production_id = s.id)))

)
    
)
 
 GROUP BY
 
  to_date(to_char(s.date_planned_start, 'MM-dd-YYYY'::text), 'MM-dd-YYYY'::text),  
 s.product_id, 
 pt.categ_id, pt.uom_id,  s.id, s.state, s.company_id
                                               
            )""")


