# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.tools import SQL
from odoo.tools.safe_eval import safe_eval


class SaleReport(models.Model):
    _inherit = "sale.report"

    price_unit = fields.Float(string="Price Unit", digits="Product Price", aggregator="avg")

    def _select_additional_fields(self):
        additional_fields_info = super()._select_additional_fields()
        additional_fields_info["price_unit"] = """
            CASE WHEN l.product_id IS NOT NULL
                THEN sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0
                THEN 1.0 ELSE s.currency_rate END) / CASE COALESCE(sum(l.qty_invoiced / u.factor * u2.factor), 0)
                     WHEN 0
                     THEN 1.0
                     ELSE sum(l.qty_invoiced / u.factor * u2.factor)
                     END
                ELSE 0
            END
        """
        return additional_fields_info

    def _read_group_select(self, aggregate_spec, query):
        if aggregate_spec == "price_unit:avg":
            get_param = self.env["ir.config_parameter"].sudo().get_param
            price_coef = safe_eval(get_param("sale_pallet.price_coef", "1"))
            untaxed_amount_invoiced_sum = self._read_group_select("untaxed_amount_invoiced:sum", query)
            qty_invoiced_sum = self._read_group_select("qty_invoiced:sum", query)
            return SQL(
                "CASE WHEN %s = 0 THEN 0 ELSE %s * %s / %s END",
                qty_invoiced_sum,
                price_coef,
                untaxed_amount_invoiced_sum,
                qty_invoiced_sum,
            )
        return super()._read_group_select(aggregate_spec, query)
