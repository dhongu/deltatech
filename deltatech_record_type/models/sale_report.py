from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    so_type = fields.Many2one("record.type", string="Order Type", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["so_type"] = " so_type"
        return res

    def _group_by_sale(self):
        group_by_ = super()._group_by_sale()
        group_by_ += ", so_type"
        return group_by_
