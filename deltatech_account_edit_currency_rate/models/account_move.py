# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    currency_rate_custom = fields.Float(
        digits=(6, 4),
        copy=False,
        help="Use only a rate allowed by Art. 290 of the Fiscal Code: the NBR rate, the ECB rate, "
        "or the rate of the settlement bank when the contract provides for it.",
    )

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

    @api.constrains("currency_rate_custom", "move_type")
    def _check_currency_rate_custom_invoice_only(self):
        # CUSTOMRATE-002: the custom rate is applied only on invoices; on a
        # journal entry it would be shown without being applied to the amounts.
        for move in self:
            if move.currency_rate_custom and not move.is_invoice(include_receipts=True):
                raise ValidationError(
                    self.env._(
                        "The custom currency rate can only be set on invoices, not on the journal entry %(move)s.",
                        move=move.display_name,
                    )
                )

    def _reverse_moves(self, default_values_list=None, cancel=False):
        # Not copied on duplicate, but a reversal (credit note) is regularized
        # at the rate of the original document, so the custom rate is kept.
        if not default_values_list:
            default_values_list = [{} for _move in self]
        for move, default_values in zip(self, default_values_list, strict=False):
            if (
                move.currency_rate_custom
                and move.is_invoice(include_receipts=True)
                and "currency_rate_custom" not in default_values
            ):
                default_values["currency_rate_custom"] = move.currency_rate_custom
        return super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("currency_id", "company_id", "move_id.date", "move_id.currency_rate_custom")
    def _compute_currency_rate(self):
        res = super()._compute_currency_rate()
        for line in self:
            if line.move_id.currency_rate_custom and line.move_id.is_invoice(include_receipts=True):
                line.currency_rate = 1 / line.move_id.currency_rate_custom
        return res

    @api.onchange("amount_currency", "currency_id", "currency_rate")
    def _inverse_amount_currency(self):
        res = super()._inverse_amount_currency()

        for line in self:
            if (
                line.move_id.currency_rate_custom
                and line.move_id.is_invoice(include_receipts=True)
                and not self.env.is_protected(self._fields["balance"], line)
            ):
                line.balance = line.company_id.currency_id.round(line.amount_currency / line.currency_rate)
        return res
