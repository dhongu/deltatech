# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleReport(models.Model):
    _inherit = "sale.report"

    price_unit = fields.Float(string="Price Unit", digits="Product Price", group_operator="avg")

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        if fields is None:
            fields = {}
        fields[
            "price_unit"
        ] = """,
            CASE WHEN l.product_id IS NOT NULL
                THEN sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) /
                    CASE COALESCE(sum(l.qty_invoiced / u.factor * u2.factor), 0)
                     WHEN 0
                     THEN 1.0
                     ELSE sum(l.qty_invoiced / u.factor * u2.factor)
                     END
                ELSE 0
            END as price_unit




            """
        sql = super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        return sql

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        new_fields = []
        new_fields += fields

        price_unit_field = next((field for field in fields if re.search(r"\bprice_unit\b", field)), False)
        amount_field = next((field for field in fields if re.search(r"\buntaxed_amount_invoiced\b", field)), False)
        qty_field = next((field for field in fields if re.search(r"\bqty_invoiced\b", field)), False)

        get_param = self.env["ir.config_parameter"].sudo().get_param
        price_coef = safe_eval(get_param("sale_pallet.price_coef", "1"))

        if price_unit_field:

            # new_fields.remove('payment_days')
            if not amount_field:
                new_fields.append("untaxed_amount_invoiced")
            if not qty_field:
                new_fields.append("qty_invoiced")

        res = super(SaleReport, self).read_group(
            domain, new_fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

        if price_unit_field:
            for line in res:
                amount = line.get("untaxed_amount_invoiced", 0.0)
                qty = line.get("qty_invoiced", 0.0)
                if amount and qty:
                    line["price_unit"] = price_coef * amount / qty
                else:
                    line["price_unit"] = 0.0

        return res
