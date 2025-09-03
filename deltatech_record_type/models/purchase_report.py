# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    po_type = fields.Many2one("record.type", string="Order Type", readonly=True)

    def _select(self):
        select_str = super()._select().code
        select_str += ", po_type"
        return SQL(select_str)

    def _group_by(self):
        group_str = super()._group_by().code
        group_str += ", po_type"
        return SQL(group_str)
