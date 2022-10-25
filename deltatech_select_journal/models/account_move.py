# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    currency_rate_custom = fields.Float(digits=(6, 4))

    def action_post(self):
        res = super(AccountMove, self).action_post()
        line_ids = self.mapped("line_ids").filtered(lambda line: line.sale_line_ids.is_downpayment)
        for line in line_ids:
            try:
                line.sale_line_ids.tax_id = line.tax_ids
                invoice = line.move_id
                date_eval = invoice.invoice_date
                from_currency = invoice.currency_id
                for sale_line in line.sale_line_ids:
                    to_currency = sale_line.order_id.currency_id
                    price_unit = from_currency.with_context(currency_rate=1 / self.currency_rate_custom)._convert(
                        line.price_unit, to_currency, invoice.company_id, date_eval
                    )
                    sale_line.write({"price_unit": price_unit})

            except UserError:
                pass
        return res


class Currency(models.Model):
    _inherit = "res.currency"

    def _convert(self, from_amount, to_currency, company, date, round=True):
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
