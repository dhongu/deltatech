# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    margin = fields.Float(string="Margin")

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        if fields is None:
            fields = {}
        fields["margin"] = (
            ", SUM(l.margin / CASE COALESCE(s.currency_rate, 0) " "WHEN 0 THEN 1.0 ELSE s.currency_rate END) AS margin"
        )
        sql = super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        margin_field = (
            ", SUM(l.margin / CASE COALESCE(pos.currency_rate, 0) "
            "WHEN 0 THEN 1.0 ELSE pos.currency_rate END) AS margin"
        )
        sql = sql.replace(", NULL AS margin", margin_field)
        return sql
