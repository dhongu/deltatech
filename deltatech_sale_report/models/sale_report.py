from odoo import fields, models
from odoo.tools import SQL, Query


class SaleReport(models.Model):
    _inherit = "sale.report"

    # Add the new field to the report
    partner_email = fields.Char(string="Partner Email")
    order_value_mean = fields.Float(string="Order Value Mean", readonly=True, group_operator="avg")
    product_value_mean = fields.Float(string="Product Value Mean", readonly=True, group_operator="avg")

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["partner_email"] = " partner.email"
        res["order_value_mean"] = "SUM(l.price_total) / NULLIF(COUNT(DISTINCT l.order_id), 0)"
        res["product_value_mean"] = "SUM(l.price_total) / NULLIF(SUM(l.qty_invoiced), 0)"
        return res

    # def _select_sale(self):
    #     # Extend the original _select_sale method to include partner_email
    #     select_ = super()._select_sale()
    #     select_ += ", partner.email AS partner_email"
    #     return select_

    def _group_by_sale(self):
        # Extend the original _group_by_sale method to include partner_email
        group_by_ = super()._group_by_sale()
        group_by_ += ", partner.email"
        return group_by_

    # Adăugați metoda _read_group_select pentru a personaliza calculul la grupare
    def _read_group_select(self, aggregate_spec: str, query: Query) -> tuple[SQL, list[str]]:
        if aggregate_spec == "order_value_mean:avg":
            # Calculează indicatorul de supliment din valorile agregate de vânzări și stoc
            price_total_sql, price_total_params = self._read_group_select("price_total:sum", query)
            order_reference_sql, order_reference_params = self._read_group_select(
                "order_reference:count_distinct", query
            )
            sql_expr = SQL(
                "CASE WHEN %s = 0 THEN 0 ELSE %s / %s END",
                order_reference_sql,
                price_total_sql,
                order_reference_sql,
            )
            return sql_expr, price_total_params + order_reference_params
        elif aggregate_spec == "product_value_mean:avg":
            # Calculează indicatorul de profit din valorile agregate de vânzări și stoc
            price_total_sql, price_total_params = self._read_group_select("price_total:sum", query)
            qty_invoiced_sql, qty_invoiced_params = self._read_group_select("qty_invoiced:sum", query)
            sql_expr = SQL(
                "CASE WHEN %s = 0 THEN 0 ELSE %s / %s END",
                qty_invoiced_sql,
                price_total_sql,
                qty_invoiced_sql,
            )
            return sql_expr, price_total_params + qty_invoiced_params

        return super()._read_group_select(aggregate_spec, query)
