from odoo import Command, _, api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.line.purchase.exist"
    _inherit = "account.move.line"

    purchase_exist = fields.Boolean(string="Purchase Exist", compute="_compute_purchase_exist")

    def _compute_purchase_exist(self):
        for move in self:
            if move.purchase_line_id:
                move.purchase_exist = True
            else:
                move.purchase_exist = False
