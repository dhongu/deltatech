# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models, tools

# TODO: de citit coeficientul  din BOM


class DeltatechMrpReport(models.Model):
    _name = "deltatech.mrp.report"
    _description = "Production Cost Analysis"
    _auto = False

    def _compute_consumed(self):
        for line in self:
            line.consumed_raw_val = 0.0
            line.consumed_pak_val = 0.0
            line.consumed_sem_val = 0.0
            for cost in line.production_id.cost_detail_ids:
                if cost.cost_categ == "semi":
                    line.consumed_sem_val += cost.amount
                elif cost.cost_categ == "pak":
                    line.consumed_pak_val += cost.amount
                else:
                    line.consumed_raw_val += cost.amount

    production_id = fields.Many2one("mrp.production", "Production Order", index=True)
    date = fields.Date("Date", readonly=True)

    categ_id = fields.Many2one("product.category", "Category", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", required=True)

    product_qty = fields.Float("Qty Plan", digits="Product Unit of Measure", readonly=True)
    product_val = fields.Float(compute="_compute_product_val", string="Val Plan", readonly=True)
    product_qty_ef = fields.Float("Qty Efective", digits="Product Unit of Measure", readonly=True)
    product_val_ef = fields.Float("Val Efective", digits="Account", readonly=True)

    consumed_val = fields.Float("Val Consumed", digits="Account", readonly=True)
    consumed_raw_val = fields.Float("Val Consumed Raw", digits="Account", readonly=True)
    consumed_pak_val = fields.Float("Val Consumed Packing", digits="Account", readonly=True)
    consumed_sem_val = fields.Float("Val Consumed Semifinish", digits="Account", readonly=True)

    val_prod = fields.Float("Value production", digits="Account", readonly=True)

    standard_price = fields.Float(
        related="product_id.standard_price", string="Price Standard", readonly=True, group_operator="avg"
    )

    actually_price = fields.Float("Actually Price", digits="Account", readonly=True, group_operator="avg")

    company_id = fields.Many2one("res.company", "Company", readonly=True)
    #        origin = fields.char('Source Document', size=64)
    nbr = fields.Integer("# of Orders", readonly=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("picking_except", "Picking Exception"),
            ("confirmed", "Waiting Goods"),
            ("ready", "Ready to Produce"),
            ("in_production", "In Production"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        "State",
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, "deltatech_mrp_report")
        self.env.cr.execute(
            """
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
    ((sum(COALESCE(sub_consumed.consumed_val, (0)::double precision)) * (1.20)::double precision) /
                        (sum(sub_prod_ef.product_qty_ef))::double precision) AS actually_price,
    s.company_id,
    ( SELECT 1) AS nbr,
    s.state
   FROM ((((((mrp_production s

     JOIN product_product  pr ON s.product_id = pr.id
         JOIN product_template pt ON pr.product_tmpl_id = pt.id )
     LEFT JOIN uom_uom u ON ((u.id = s.product_uom_id)))
     LEFT JOIN ( SELECT sm.production_id,
            sum(sm.product_qty) AS product_qty_ef,
            sum(svl.value) AS product_val_ef,
            sm.procure_method
           FROM  stock_move sm
            LEFT JOIN stock_valuation_layer svl on sm.id = svl.stock_move_id

          WHERE ((sm.state)::text = 'done'::text)
          GROUP BY sm.production_id, sm.procure_method) sub_prod_ef ON ((sub_prod_ef.production_id = s.id)))

left join (
SELECT
    sm.raw_material_production_id AS production_id,
   SUM (-svl.value) AS consumed_val,
      CASE WHEN pc.cost_categ='semi' THEN SUM (-svl.value) else 0.0 end as  consumed_sem_val,
      CASE WHEN pc.cost_categ='pak' THEN SUM (-svl.value) else 0.0 end as  consumed_pak_val,
      CASE WHEN pc.cost_categ='raw' THEN SUM (-svl.value) else 0.0 end as  consumed_raw_val
    FROM
        stock_move sm
        LEFT JOIN stock_valuation_layer svl on sm.id = svl.stock_move_id
        LEFT JOIN product_product pr ON pr.id = sm.product_id
        LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
        LEFT JOIN product_category pc ON pc.id = pt.categ_id
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

            )"""
        )
