# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    amount = fields.Monetary(string="Amount", compute="_compute_amount")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)

    def _compute_amount(self):
        for picking in self:
            amount = 0
            for move in picking.move_ids:
                for valuation in move.stock_valuation_layer_ids:
                    amount += valuation.value
            picking.amount = amount
