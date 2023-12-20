from odoo import api, fields, models, Command, _


class AccountMoveLine(models.Model):
    _name = 'account.line.purchase.exist'
    _inherit = 'account.move.line'

    purchase_exist = fields.Boolean(string='Purchase Exist', compute='_compute_purchase_exist', store=True)

    def _compute_purchase_exist(self):
        for move in self:
            if move.purchase_line_id:
                move.purchase_exist = True
            else:
                move.purchase_exist = False

    def action_post(self):
        return

    def action_invoice_sent(self):
        return

    def action_register_payment(self):
        return
