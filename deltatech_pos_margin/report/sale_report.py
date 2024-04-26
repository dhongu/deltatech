# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    margin = fields.Float(string="Margin")

    def _select_additional_fields(self):
        additional_fields_info = super()._select_additional_fields()
        additional_fields_info[
            "margin"
        ] = """
            SUM(l.margin / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END)
        """
        return additional_fields_info
