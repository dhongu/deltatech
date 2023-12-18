# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for move in self:
            for line in move.line_ids:
                if line.product_id and line.account_id.stock_valuation:
                    if not line.valuation_area_id:
                        line.set_valuation_area_id()

                    valuation_area = line.valuation_area_id
                    valuation = self.env["product.valuation"].get_valuation(
                        line.product_id.id, valuation_area.id, line.account_id.id, line.company_id.id
                    )
                    valuation.recompute_amount()

                    valuation_history = self.env["product.valuation.history"].get_valuation(
                        line.product_id.id, valuation_area.id, line.account_id.id, move.date, line.company_id.id
                    )
                    valuation_history.recompute_amount()
        return res
