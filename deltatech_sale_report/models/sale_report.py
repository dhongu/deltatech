from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    # Add the new field to the report
    partner_email = fields.Char(string="Partner Email", readonly=True)

    def _select_dict(self, table):
        return super()._select_dict(table) | {
            "partner_email": table.order_id.partner_id.email,
        }

    def _groupby_list(self, table):
        return super()._groupby_list(table) + [table.order_id.partner_id.email]
