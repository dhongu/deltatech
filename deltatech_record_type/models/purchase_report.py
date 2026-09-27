# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    po_type = fields.Many2one("record.type", string="Order Type", readonly=True)

    def _select_list(self, table):
        return super()._select_list(table) + [SQL("%s AS po_type", table.order_id.po_type)]

    def _groupby_list(self, table):
        return super()._groupby_list(table) + [table.order_id.po_type]
