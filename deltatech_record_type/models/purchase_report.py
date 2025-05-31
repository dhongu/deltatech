# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    po_type = fields.Many2one("record.type", string="Order Type", readonly=True)

    def _select(self):
        return super()._select() + ", po_type"

    def _group_by(self):
        return super()._group_by() + ", po_type"
