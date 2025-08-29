# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    currency_rate_custom = fields.Float(digits=(6, 4))

    @api.onchange("currency_rate_custom")
    def onchange_currency_rate_custome(self):
        self.line_ids._compute_currency_rate()
        self.line_ids._inverse_amount_currency()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("currency_id", "company_id", "move_id.date")
    def _compute_currency_rate(self):
        res = super()._compute_currency_rate()
        for line in self:
            if line.move_id.currency_rate_custom:
                line.currency_rate = 1 / line.move_id.currency_rate_custom
        return res

    @api.onchange("amount_currency", "currency_id", "currency_rate")
    def _inverse_amount_currency(self):
        res = super()._inverse_amount_currency()

        for line in self:
            if line.move_id.currency_rate_custom and not self.env.is_protected(self._fields["balance"], line):
                line.balance = line.company_id.currency_id.round(line.amount_currency / line.currency_rate)
        return res
