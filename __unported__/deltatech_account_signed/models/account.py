# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_signed = fields.Monetary(compute='_amount_compute_signed', store=True)


    @api.depends('line_ids.debit', 'line_ids.credit')
    def _amount_compute_signed(self):
        for move in self:
            total_debit = 0.0
            total_credit = 0.0
            move.amount_signed = move.amount

            if move.journal_id.type in ['cash', 'bank']:
                for line in move.line_ids:
                    if line.account_id.internal_type == 'liquidity':
                        total_credit += line.credit
                        total_debit += line.debit

                move.amount_signed = total_debit - total_credit

            if move.journal_id.type in ['sale']:
                for line in move.line_ids:
                    if line.account_id.internal_type == 'receivable':
                        total_credit += line.credit
                        total_debit += line.debit

                move.amount_signed = total_debit - total_credit

            if move.journal_id.type in ['purchase']:
                for line in move.line_ids:
                    if line.account_id.internal_type == 'payable':
                        total_credit += line.credit
                        total_debit += line.debit

                move.amount_signed = total_credit - total_debit

