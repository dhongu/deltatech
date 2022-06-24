# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, tools


class DeltatechCostDetail(models.Model):
    _name = "deltatech.cost.detail"
    _description = "Cost Detail"
    _auto = False

    production_id = fields.Many2one("mrp.production", string="Production Order")
    cost_categ = fields.Selection(
        [("raw", "Raw materials"), ("semi", "Semi-products"), ("pak", "Packing Material")], string="Cost Category"
    )
    amount = fields.Float(string="Amount", digits="Account")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, "deltatech_cost_detail")
        self.env.cr.execute(
            """
            create or replace view deltatech_cost_detail as (

                SELECT max(sm.id) AS id,
                    sm.raw_material_production_id AS production_id,
                    SUM (-svl.value) AS amount,
                    pc.cost_categ
                FROM
                    stock_move sm
                    LEFT JOIN product_product pr ON pr.id = sm.product_id
                    LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
                    LEFT JOIN product_category pc ON pc.id = pt.categ_id
                    LEFT JOIN stock_valuation_layer svl on sm.id = svl.stock_move_id
                WHERE
                     raw_material_production_id IS NOT NULL
                     AND sm.state = 'done' :: TEXT
                GROUP BY
                    sm.raw_material_production_id, pc.cost_categ
        )"""
        )


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    cost_detail_ids = fields.One2many("deltatech.cost.detail", "production_id", compute="_compute_cost_detail")

    def recompute_cost_detail(self):
        for production in self:
            production._compute_cost_detail()

    @api.depends("move_raw_ids")
    def _compute_cost_detail(self):
        for production in self:
            domain = [("production_id", "=", production.id)]
            cost_detail_ids = self.env["deltatech.cost.detail"].search(domain)
            production.cost_detail_ids = cost_detail_ids
