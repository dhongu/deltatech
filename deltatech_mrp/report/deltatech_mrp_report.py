# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

from openerp.osv import fields,osv
from openerp import tools
import openerp.addons.decimal_precision as dp


#TODO: de citit coeficientul  din BOM

 


class deltatech_mrp_report(osv.osv):
    _name = "deltatech.mrp.report"
    _description = "Production Cost Analysis"
    _auto = False



    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(deltatech_mrp_report, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        if context is None:
            context = {}
        
        prod_dict = {}
        if 'standard_price' in fields or 'product_val' in fields or 'consumed_raw_val'  in fields or 'consumed_pak_val'  in fields or 'consumed_sem_val'  in fields:
            for line in res:

                lines = self.search(cr, uid, line.get('__domain', []), context=context)
                standard_price = 0.0 
                itmes = 0
                product_val = 0
                consumed_sem_val = 0
                consumed_pak_val = 0
                consumed_raw_val = 0
                product_tmpl_obj = self.pool.get("product.template")
                lines_rec = self.browse(cr, uid, lines, context=context)
                for line_rec in lines_rec:
                    if line_rec.product_id.cost_method == 'real':
                        price = line_rec.price_unit_on_quant
                    else:
                        if not line_rec.product_id.id in prod_dict:
                            prod_dict[line_rec.product_id.id] = product_tmpl_obj.get_history_price(cr, uid, line_rec.product_id.product_tmpl_id.id, line_rec.company_id.id, date=line_rec.date, context=context)
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
                
                #line['consumed_sem_val'] = consumed_sem_val
                #line['consumed_pak_val'] = consumed_pak_val
                #line['consumed_raw_val'] = consumed_raw_val
        return res


    def _get_standard_price(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_tmpl_obj = self.pool.get("product.template")
            res[line.id] = product_tmpl_obj.get_history_price(cr, uid, line.product_id.product_tmpl_id.id,
                                                                       line.company_id.id, date=line.date, context=context)
        return res
 
    def _get_product_val(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_tmpl_obj = self.pool.get("product.template")
            res[line.id] = line.product_qty * product_tmpl_obj.get_history_price(cr, uid, line.product_id.product_tmpl_id.id,
                                                                       line.company_id.id, date=line.date, context=context)  
        return res
 
    def _get_consumed(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context): 
            res[line.id] = {'consumed_raw_val':0.0, 'consumed_pak_val':0.0, 'consumed_sem_val':0.0 }
            for cost in  line.production_id.cost_detail_ids:
                if cost.cost_categ == 'semi':
                    res[line.id]['consumed_sem_val'] = cost.amount
                elif cost.cost_categ == 'pak':
                    res[line.id]['consumed_pak_val'] = cost.amount
                else:
                    res[line.id]['consumed_raw_val'] = cost.amount
        return res

 

 
    _columns = {
        'production_id': fields.many2one('mrp.production', 'Production Order', select=True),
        'date': fields.date('Date', readonly=True),
  
        'categ_id': fields.many2one('product.category', 'Category', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),



        'product_qty': fields.float('Qty Plan', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'product_val': fields.function(_get_product_val, string="Val Plan", type='float', readonly=True ),
        'product_qty_ef': fields.float('Qty Efective',  digits_compute=dp.get_precision('Product UoM'),readonly=True),
        'product_val_ef': fields.float('Val Efective',digits_compute= dp.get_precision('Account'), readonly=True),

        'consumed_val': fields.float('Val Consumed', digits_compute= dp.get_precision('Account'),readonly=True),
        'consumed_raw_val': fields.float('Val Consumed Raw',digits_compute= dp.get_precision('Account'), readonly=True),
        'consumed_pak_val': fields.float('Val Consumed Packing',digits_compute= dp.get_precision('Account'), readonly=True),
        'consumed_sem_val': fields.float('Val Consumed Semifinish',digits_compute= dp.get_precision('Account'), readonly=True),
        #'consumed_raw_val': fields.function(_get_consumed, string='Val Consumed row',type='float', multi="cons", digits_compute= dp.get_precision('Account'), readonly=True),
        #'consumed_pak_val': fields.function(_get_consumed, string='Val Consumed pak',type='float',multi="cons", digits_compute= dp.get_precision('Account'), readonly=True),
        #'consumed_sem_val': fields.function(_get_consumed, string='Val Consumed Semifinish',type='float',multi="cons", digits_compute= dp.get_precision('Account'), readonly=True),

        'val_prod': fields.float('Value production', digits_compute= dp.get_precision('Account'), readonly=True),


        'standard_price': fields.function(_get_standard_price, string="Price Standard", type='float', readonly=True ),
       
        'actually_price': fields.float('Actually Price',digits_compute= dp.get_precision('Account'), readonly=True, group_operator="avg"),   

        'company_id': fields.many2one('res.company','Company',readonly=True),   
#        'origin': fields.char('Source Document', size=64),
        'nbr': fields.integer('# of Orders', readonly=True),

        'state': fields.selection([('draft','Draft'),
                                   ('picking_except', 'Picking Exception'),
                                   ('confirmed','Waiting Goods'),
                                   ('ready','Ready to Produce'),
                                   ('in_production','In Production'),
                                   ('cancel','Cancelled'),
                                   ('done','Done')],
                                    'State', readonly=True),
  
 
    }
    
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'deltatech_mrp_report')
        cr.execute("""
            create or replace view deltatech_mrp_report as (
 

 SELECT s.id, s.id as production_id, 
    pt.categ_id,
    to_date(to_char(s.date_planned, 'MM-dd-YYYY'::text), 'MM-dd-YYYY'::text) AS date,
 
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
     LEFT JOIN product_uom u ON ((u.id = s.product_uom)))
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
 
 to_date(to_char(s.date_planned, 'MM-dd-YYYY'::text), 'MM-dd-YYYY'::text),
 s.product_id, 
 pt.categ_id, pt.uom_id,  s.id, s.state, s.company_id
                                               
            )""")


deltatech_mrp_report()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

