# Copyright 2009-2022 Noviat.
# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class Currency(models.Model):
    _inherit = "res.currency"

    def _convert(self, from_amount, to_currency, company, date, round=True):
        use_date = self.env.context.get("force_period_date", False)
        if use_date:
            return super()._convert(from_amount, to_currency, company, use_date, round)
        else:
            return super()._convert(from_amount, to_currency, company, date, round)
