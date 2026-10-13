# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools import SQL
from odoo.tools.safe_eval import safe_eval


class SaleReport(models.Model):
    _inherit = "sale.report"

    # `price_unit` (cu aggregator="avg") e declarat nativ în O19 și inclus în
    # select-ul de bază al raportului. Nu mai redefinim câmpul și nici nu mai
    # adăugăm o coloană prin `_select_additional_fields` (redundant cu nativul);
    # calculul cu `sale_pallet.price_coef` se face la citire în `_read_group_select`.

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
