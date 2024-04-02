##############################################################################
#
# Copyright (c) 2008 stock All Rights Reserved
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

from odoo import fields, models, tools


class StockBalance(models.Model):
    _name = "stock.balance"
    _description = "stock Stock balance"
    _auto = False

    date = fields.Datetime("Date", readonly=True)
    location_id = fields.Many2one("stock.location", "Location", readonly=True, index=True)
    categ_id = fields.Many2one("product.category", "Category", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", required=True)
    qty_in = fields.Float("Qty In", digits="Product Unit of Measure", readonly=True)
    amount_in = fields.Float("Amount In", digits="Account", readonly=True)
    qty_out = fields.Float("Qty Out", digits="Product Unit of Measure", readonly=True)
    amount_out = fields.Float("Amount Out", digits="Account", readonly=True)
    product_qty = fields.Float("Quantity", digits="Product Unit of Measure", readonly=True)
    amount = fields.Float("Amount", digits="Account", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
         create or replace view stock_balance as (

            SELECT
             min(smg.id) AS id, smg.date,
             smg.location_id, smg.categ_id, smg.product_id,  smg.product_uom,
             sum(smg.qty_in) AS qty_in,
             sum(smg.amount_in) AS amount_in,
             sum(smg.qty_out) AS qty_out,
             sum(smg.amount_out) AS amount_out,
             sum((smg.qty_in - smg.qty_out)) AS product_qty,
             sum((smg.amount_in - smg.amount_out)) AS amount,
             smg.company_id
             FROM (
              SELECT min(sm.id) AS id,
                sm.date  AS date,
                sm.location_id, pt.categ_id, sm.product_id, pu.id AS product_uom,
                0 AS qty_in, 0 AS amount_in,
                COALESCE(sum(((sm.product_qty * pu.factor) / pu2.factor)), 0.0) AS qty_out,
                sum(sm.value) AS amount_out, sm.company_id
              FROM stock_move sm
                LEFT JOIN stock_move_line sml  ON   sml.move_id = sm.id
                    LEFT JOIN stock_quant_package ON  stock_quant_package.id = sml.result_package_id
                        LEFT JOIN stock_quant q ON  stock_quant_package.id = q.package_id
                LEFT JOIN product_product pp ON  sm.product_id = pp.id
                    LEFT JOIN product_template pt ON  pp.product_tmpl_id = pt.id
                        LEFT JOIN uom_uom pu ON  pt.uom_id = pu.id
                LEFT JOIN uom_uom pu2 ON  sm.product_uom = pu2.id

              WHERE ( sm.state  = 'done' )
              GROUP BY pt.categ_id, sm.product_id, pu.id, sm.location_id, sm.date,
                  sm.company_id
                UNION ALL
                SELECT min(- sm.id) AS id,
                    sm.date AS date,
                    sm.location_dest_id AS location_id, pt.categ_id, sm.product_id,
                    pu.id AS product_uom,
                    COALESCE(sum(((sm.product_qty*pu.factor)/pu2.factor)), 0.0) AS qty_in,
                    sum( sm.value ) AS amount_in,

                    0 AS qty_out, 0 AS amount_out, sm.company_id
                FROM  stock_move sm
                    LEFT JOIN stock_move_line sml  ON   sml.move_id = sm.id
                    LEFT JOIN stock_quant_package ON  stock_quant_package.id = sml.result_package_id
                        LEFT JOIN stock_quant q ON  stock_quant_package.id = q.package_id
                    LEFT JOIN product_product pp ON  sm.product_id = pp.id
                    LEFT JOIN product_template pt ON  pp.product_tmpl_id = pt.id
                    LEFT JOIN uom_uom pu ON  pt.uom_id = pu.id
                    LEFT JOIN uom_uom pu2 ON  sm.product_uom = pu2.id

              WHERE ( sm.state   = 'done')
              GROUP BY pt.categ_id, sm.product_id, pu.id, sm.location_dest_id, sm.date,
                  sm.company_id) smg
             GROUP BY smg.date,  smg.categ_id, smg.product_id,
             smg.location_id, smg.product_uom, smg.company_id
        )"""
        )

        # amount_in era calculat din sum((q.quantity * q.cost)) AS amount_in
