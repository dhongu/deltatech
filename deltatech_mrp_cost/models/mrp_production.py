# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    amount = fields.Float(digits="Account", string="Production Amount", compute="_compute_amount")
    calculate_price = fields.Float(digits="Account", string="Calculate Price", compute="_compute_amount")

    duration = fields.Float(string="Duration")

    overhead_amount = fields.Float(string="Overhead", default="0.0")

    utility_consumption = fields.Float(string="Utility consumption", help="Utilities consumption per hour")
    net_salary_rate = fields.Float(string="Net Salary Rate")
    salary_contributions = fields.Float(string="Salary Contributions")

    def _compute_amount(self):

        for production in self:
            amount = 0.0
            if not production.qty_produced:
                for move in production.move_raw_ids:
                    if move.product_id.type == "product":
                        amount += move.product_id.standard_price * move.product_qty
                product_qty = production.product_qty
                amount += (
                    production.overhead_amount
                    + production.utility_consumption * production.duration
                    + production.net_salary_rate * production.duration
                    + production.salary_contributions * production.duration
                )

                calculate_price = amount / product_qty
                production.calculate_price = calculate_price
                production.amount = amount
            else:
                amount = sum(production.move_finished_ids.mapped("stock_valuation_layer_ids.value"))
                calculate_price = amount / production.qty_produced
                production.calculate_price = calculate_price
                production.amount = amount

    def _cal_price(self, consumed_moves):

        if self.product_qty:
            costs = (
                self.overhead_amount
                + self.utility_consumption * self.duration
                + self.net_salary_rate * self.duration
                + self.salary_contributions * self.duration
            )
            if costs:
                self.extra_cost = costs / self.product_qty

        return super(MrpProduction, self)._cal_price(consumed_moves)
