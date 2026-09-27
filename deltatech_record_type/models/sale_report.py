from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    so_type = fields.Many2one("record.type", string="Order Type", readonly=True)

    def _select_dict(self, table):
        return super()._select_dict(table) | {"so_type": table.order_id.so_type}

    def _groupby_list(self, table):
        return super()._groupby_list(table) + [table.order_id.so_type]
