# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] in ['/', '', False]:
                journal = self.env['account.journal'].browse(vals['journal_id'])
                if journal.statement_sequence_id:
                    vals['name'] = journal.statement_sequence_id.next_by_id()
        return super(AccountBankStatement, self).create(vals_list)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    payment_id = fields.Many2one('account.payment')



    def get_move_lines_for_reconciliation(self, partner_id=None, excluded_ids=None, str=False, offset=0, limit=None, additional_domain=None, overlook_partner=False):
        """ Return account.move.line records which can be used for bank statement reconciliation.

            :param partner_id:
            :param excluded_ids:
            :param str:
            :param offset:
            :param limit:
            :param additional_domain:
            :param overlook_partner:
        """
        if partner_id is None:
            partner_id = self.partner_id.id

        # Blue lines = payment on bank account not assigned to a statement yet
        reconciliation_aml_accounts = [self.journal_id.default_credit_account_id.id, self.journal_id.default_debit_account_id.id]
        domain_reconciliation = ['&', '&', ('statement_line_id', '=', False), ('account_id', 'in', reconciliation_aml_accounts), ('payment_id','<>', False)]

        # Black lines = unreconciled & (not linked to a payment or open balance created by statement
        domain_matching = [('reconciled', '=', False)]
        if partner_id or overlook_partner:
            domain_matching = expression.AND([domain_matching, ['|', ('account_id.internal_type', 'in', ['payable', 'receivable']), '&', ('account_id.internal_type', '=', 'other'), ('account_id.reconcile', '=', True)]])
        else:
            # TODO : find out what use case this permits (match a check payment, registered on a journal whose account type is other instead of liquidity)
            domain_matching = expression.AND([domain_matching, [('account_id.reconcile', '=', True)]])

        # Let's add what applies to both
        domain = expression.OR([domain_reconciliation, domain_matching])
        if partner_id and not overlook_partner:
            domain = expression.AND([domain, [('partner_id', '=', partner_id)]])

        # Domain factorized for all reconciliation use cases
        if str:
            str_domain = self.env['account.move.line'].domain_move_lines_for_reconciliation(str=str)
            if not partner_id:
                str_domain = expression.OR([str_domain, [('partner_id.name', 'ilike', str)]])
            domain = expression.AND([domain, str_domain])
        if excluded_ids:
            domain = expression.AND([[('id', 'not in', excluded_ids)], domain])

        # Domain from caller
        if additional_domain is None:
            additional_domain = []
        else:
            additional_domain = expression.normalize_domain(additional_domain)
        domain = expression.AND([domain, additional_domain])

        return self.env['account.move.line'].search(domain, offset=offset, limit=limit, order="date_maturity , id desc")