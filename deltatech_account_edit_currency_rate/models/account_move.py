# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    currency_rate_custom = fields.Float(digits=(6, 4))

    @api.depends("currency_rate_custom")
    def _compute_invoice_currency_rate(self):
        # The custom rate (company currency per document currency) drives the
        # native invoice rate, so the line rates, balances and taxes are
        # recomputed by the standard invoice synchronization on create/write
        # (RPC, import, ORM), not only by the form onchange.
        res = super()._compute_invoice_currency_rate()
        for move in self:
            if move.currency_rate_custom and move.is_invoice(include_receipts=True):
                move.invoice_currency_rate = 1 / move.currency_rate_custom
        return res

    def write(self, vals):
        if "currency_rate_custom" in vals and not self.env.context.get("skip_readonly_check"):
            new_rate = vals["currency_rate_custom"] or 0.0
            for move in self:
                if move.state == "posted" and float_compare(move.currency_rate_custom, new_rate, precision_digits=4):
                    raise UserError(
                        self.env._(
                            "You cannot change the custom currency rate of the posted entry %(move)s. "
                            "Reset it to draft first.",
                            move=move.display_name,
                        )
                    )
        return super().write(vals)

    @api.onchange("currency_rate_custom")
    def onchange_currency_rate_custome(self):
        # Invoices are handled server side through `invoice_currency_rate`;
        # journal entries keep the interactive recomputation of the balances.
        moves = self.filtered(lambda m: not m.is_invoice(include_receipts=True))
        moves.line_ids._compute_currency_rate()
        moves.line_ids._inverse_amount_currency()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("currency_id", "company_id", "move_id.date", "move_id.currency_rate_custom")
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
