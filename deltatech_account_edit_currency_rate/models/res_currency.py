# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class Currency(models.Model):
    _inherit = "res.currency"

    def _convert(self, from_amount, to_currency, company=None, date=None, round=True):  # noqa:W0622
        if self._context.get("currency_rate"):
            self, to_currency = self or to_currency, to_currency or self
            assert self, "convert amount from unknown currency"
            assert to_currency, "convert amount to unknown currency"
            assert company, "convert amount from unknown company"
            assert date, "convert amount from unknown date"

            if self == to_currency:
                to_amount = from_amount
            else:
                to_amount = from_amount * self._context["currency_rate"]
            return to_currency.round(to_amount) if round else to_amount

        return super()._convert(from_amount, to_currency, company, date, round=round)
