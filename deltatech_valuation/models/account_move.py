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
                if not line.valuation_area_id:
                    line.set_valuation_area_id()

        return res
