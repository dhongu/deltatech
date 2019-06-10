# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] in ['/', '', False]:
            journal = self.env['account.journal'].browse(vals['journal_id'])
            if journal.statement_sequence_id:
                vals['name'] = journal.statement_sequence_id.next_by_id()
        return super(AccountBankStatement, self).create(vals)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    payment_id = fields.Many2one('account.payment')


    # standard se face ordonarea dupa: date_maturity desc, id desc
    def get_move_lines_for_reconciliation(self, partner_id=None, excluded_ids=None, str=False, offset=0, limit=None, additional_domain=None, overlook_partner=False):
        aml = super(AccountBankStatementLine, self).get_move_lines_for_reconciliation(partner_id, excluded_ids, str, offset, limit, additional_domain, overlook_partner)
        aml.sorted(key=lambda r: r.date_maturity)
        return aml