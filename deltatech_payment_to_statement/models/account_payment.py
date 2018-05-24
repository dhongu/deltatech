# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class account_payment(models.Model):
    _inherit = "account.payment"

    statement_id = fields.Many2one('account.bank.statement', string='Statement',
                                   domain="[('journal_id','=',journal_id)]")

    statement_line_id = fields.Many2one('account.bank.statement.line', string='Statement Line',readonly=True,
                                        domain="[('statement_id','=',statement_id)]")

    @api.onchange('payment_date', 'journal_id')
    def onchange_date_journal(self):
        domain = [('date', '=', self.payment_date), ('journal_id', '=', self.journal_id.id)]
        statement = self.env['account.bank.statement'].search(domain, limit=1)
        if statement:
            self.statement_id = statement
        else:
            # daca tipul este numerar trebuie generat
            if self.journal_id.type == 'cash':
                name = False

                values = {'journal_id': self.journal_id.id,
                          'date': self.payment_date,
                          'name': '/'}

                self.statement_id = self.env['account.bank.statement'].create(values)

    @api.multi
    def post(self):
        lines = self.env['account.bank.statement.line']
        for payment in self:
            if not payment.statement_line_id and payment.statement_id:
                values = {
                    'name': payment.communication or '/',
                    'statement_id': payment.statement_id.id,
                    'date': payment.payment_date,
                    'partner_id': payment.partner_id.id,
                    'amount': payment.amount,
                    'payment_id': payment.id,

                }
                if payment.payment_type == 'outbound':
                    values['amount'] = -1 * payment.amount

                line = self.env['account.bank.statement.line'].create(values)
                lines |= line
                payment.write({'statement_line_id': line.id})
        res = super(account_payment, self).post()
        if lines:
            for line in lines:
                if line.name == '/':
                    line.write({'name': line.payment_id.name})
        for payment in self:
            for move_line in payment.move_line_ids:
                if not move_line.statement_id:
                    move_line.write({'statement_id':payment.statement_id.id})
                    move_line.move_id.write({'statement_line_id':payment.statement_line_id.id})
        return res


    @api.multi
    def add_statement_line(self):
        lines = self.env['account.bank.statement.line']
        for payment in self:
            if payment.journal_id.type == 'cash' and not payment.statement_id:
                domain = [('date', '=', self.payment_date), ('journal_id', '=', self.journal_id.id)]
                statement = self.env['account.bank.statement'].search(domain, limit=1)
                if not statement:
                    values = {'journal_id': payment.journal_id.id,
                              'date': payment.payment_date,
                              'name': '/'}
                    statement = payment.env['account.bank.statement'].create(values)
                payment.write({'statement_id':statement.id})

            if payment.state == 'posted' and not payment.statement_line_id and payment.statement_id:
                values = {
                    'name': payment.communication or payment.name,
                    'statement_id': payment.statement_id.id,
                    'date': payment.payment_date,
                    'partner_id': payment.partner_id.id,
                    'amount': payment.amount,
                    'payment_id': payment.id,
                }
                if payment.payment_type == 'outbound':
                    values['amount'] = -1 * payment.amount

                line = self.env['account.bank.statement.line'].create(values)
                lines |= line
                payment.write({'statement_line_id': line.id})

                for move_line in payment.move_line_ids:
                    if not move_line.statement_id:
                        move_line.write({'statement_id': payment.statement_id.id})
                        move_line.move_id.write({'statement_line_id': payment.statement_line_id.id})
