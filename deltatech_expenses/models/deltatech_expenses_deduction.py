# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

import odoo.addons.decimal_precision as dp

from odoo import api
from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _


class deltatech_expenses_deduction(models.Model):
    _name = 'deltatech.expenses.deduction'
    _inherit = ['mail.thread']
    _description = 'Expenses Deduction'
    _order = "date_expense desc, id desc"
    _rec_name = "number"

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency_id or journal.company_id.currency_id or self.env.user.company_id.currency_id

    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))

        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [('type', '=', 'cash'), ('company_id', '=', company_id), ]
        return self.env['account.journal'].search(domain, limit=1)

    @api.model
    def _default_account_diem(self):
        account_pool = self.env['account.account']
        try:
            account_id = account_pool.search([('code', '=ilike', '625%')], limit=1)  ## Cheltuieli cu deplasari
        except:
            try:
                account_id = account_pool.search(
                    [('user_type_id.name', '=', 'expense'), ('internal_type', '!=', 'view')], limit=1)
            except:
                account_id = False
        return account_id

    """
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        return [(r['id'], (r['number'] + str("%.2f" % r['amount']) or '')) 
                for r in self.read(cr, uid, ids, ['number','amount'], context, load='_classic_write')]
    """

    number = fields.Char(string='Number', size=32, readonly=True, )
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled'), ], string='Status',
                             index=True, readonly=True, track_visibility='onchange', default='draft', help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed expenses deduction. \
            \n* The \'Done\' status is set automatically when the expenses deduction is confirm.  \
            \n* The \'Cancelled\' status is used when user cancel expenses deduction.')
    date_expense = fields.Date(string='Expense Date', readonly=True, states={'draft': [('readonly', False)]},
                               index=True)
    date_advance = fields.Date(string='Advance Date', readonly=True, states={'draft': [('readonly', False)]}, )
    travel_order = fields.Char(string='Travel Order', readonly=True, states={'draft': [('readonly', False)]})

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    employee_id = fields.Many2one('res.partner', string="Employee", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]}, domain=[('is_company', '=', False)])

    expenses_line_ids = fields.One2many('deltatech.expenses.deduction.line', 'expenses_deduction_id', string='Vouchers',
                                        readonly=True, states={'draft': [('readonly', False)]})

    voucher_ids = fields.One2many('account.voucher', 'expenses_deduction_id', string='Vouchers',
                                  domain=[('voucher_type', '=', 'purchase')],
                                  context={'default_voucher_type': 'purchase'},
                                  readonly=True, states={'draft': [('readonly', False)]})

    payment_ids = fields.One2many('account.payment', 'expenses_deduction_id', string='Payments',
                                  domain=[('payment_type', '=', 'outbound')], context={'default_type': 'outbound'},
                                  readonly=True)

    note = fields.Text(string='Note')
    amount = fields.Monetary(string='Total Amount', digits=dp.get_precision('Account'), compute="_compute_amount")
    amount_vouchers = fields.Monetary(string='Vouchers Amount', digits=dp.get_precision('Account'),
                                      compute="_compute_amount")
    advance = fields.Monetary(string='Advance', digits=dp.get_precision('Account'), readonly=True,
                              states={'draft': [('readonly', False)]})

    difference = fields.Monetary(string='Difference', digits=dp.get_precision('Account'), compute="_compute_amount")

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, required=True,
                                  default=_default_currency, compute="_compute_currency")

    journal_id = fields.Many2one('account.journal', string='Cash Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, default=_default_journal)
    journal_payment_id = fields.Many2one('account.journal', string='Journal Expenses Deduction',
                                         required=True)  # readonly=True, states={'draft':[('readonly',False)]}),
    # 'account_id':fields.many2one('account.account','Account', required=True, readonly=True, states={'draft':[('readonly',False)]}),
    account_diem_id = fields.Many2one('account.account', string='Account', required=True, readonly=True,
                                      states={'draft': [('readonly', False)]}, default=_default_account_diem)
    move_id = fields.Many2one('account.move', string='Account Entry', readonly=True)

    move_ids = fields.One2many('account.move.line', related='move_id.line_ids', string='Journal Items', readonly=True)

    diem = fields.Monetary(string='Diem', digits=dp.get_precision('Account'), readonly=True,
                           states={'draft': [('readonly', False)]}, default=42.5)
    days = fields.Integer(string='Days', readonly=True, states={'draft': [('readonly', False)]})

    total_diem = fields.Monetary(string='Total Diem', digits=dp.get_precision('Account'), compute="_compute_amount")

    """
    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        account_obj = self.pool.get('account.account')
        values = super(deltatech_expenses_deduction, self).default_get(cr, uid, fields_list, context=context)
        if 'account_id' in fields_list:
            try:
                account_id  = account_obj.search(cr, uid, [('code','ilike','542')])[0]
            except (orm.except_orm, ValueError):
                account_id = False
            values.update({'account_id': account_id})     
        return values   
    """

    @api.onchange('date_advance')
    def onchange_date_advance(self):
        if not self.date_expense or self.date_advance > self.date_expense:
            self.date_expense = self.date_advance

    @api.multi
    @api.depends('expenses_line_ids', 'days', 'diem', 'advance')
    def _compute_amount(self):
        for expense in self:
            total = 0.0
            for line in expense.expenses_line_ids:
                total += line.tax_amount + line.price_subtotal

            expense.amount_vouchers = total
            expense.total_diem = expense.days * expense.diem
            expense.amount = expense.amount_vouchers + expense.total_diem

            expense.difference = expense.amount - expense.advance

    @api.multi
    def _compute_currency(self):
        for expense in self:
            expense.currency_id = expense.company_id.currency_id.id

    @api.multi
    def unlink(self):
        for t in self:
            if t.state not in ('draft', 'cancel'):
                raise UserError(_('Cannot delete Expenses Deduction(s) which are already done.'))
        return super(deltatech_expenses_deduction, self).unlink()

    @api.multi
    def invalidate_expenses(self):

        moves = self.env['account.move']
        for expenses in self:
            if expenses.move_id:
                moves |= expenses.move_id
            for voucher in expenses.voucher_ids:
                moves |= voucher.move_id

        self.write({'state': 'draft', 'move_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            for move in moves:
                move.line_ids.remove_move_reconcile()
            moves.unlink()

        # anulare plati inregistrate
        for expenses in self:


            expenses.voucher_ids.cancel_voucher()
            expenses.voucher_ids.unlink()

            # expenses.payment_ids.cancel_voucher()
            expenses.payment_ids.cancel()
            expenses.payment_ids.action_draft()
            # domain = [('voucher_id', 'in', expenses.payment_ids.ids)]
            # statement_lines = self.env['account.bank.statement.line'].search(domain)
            # if statement_lines:
            #     statement_lines.unlink()
            expenses.payment_ids.write({'move_name': False, 'state': 'draft'})
            expenses.payment_ids.unlink()

            # anulare postare chitante.

        # todo: de facut cancel dupa expenses_line_ids
        # for expenses in self:
        #    expenses.line_ids.cancel_voucher()
        #    expenses.line_ids.action_cancel_draft()

        statement_lines = self.env['account.bank.statement.line'].search([('expenses_deduction_id', '=', expenses.id)])
        if statement_lines:
            statement_lines.unlink()

        return True

    @api.multi
    def validate_expenses(self):

        # poate ar fi bine daca  bonurile fiscale de la acelasi furnizor sa fie unuite intr-o singura chitanta.

        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [('type', '=', 'purchase'), ('company_id', '=', company_id), ]
        purchase_journal = self.env['account.journal'].search(domain, limit=1)
        generic_parnter = self.env.ref('deltatech_partner_generic.partner_generic', raise_if_not_found=False)

        for expenses in self:

            if not expenses.number:
                name = expenses.journal_id.sequence_id.next_by_id()
            else:
                name = expenses.number

            vouchers = self.env['account.voucher']
            payments = self.env['account.payment']

            # reconcile = self.env['account.full.reconcile'].create({'name':name})

            for line in expenses.expenses_line_ids:
                partner_id = line.partner_id or generic_parnter

                voucher_value = {
                    'partner_id': partner_id.id,
                    'voucher_type': 'purchase',
                    'pay_now': 'pay_now',
                    'date': line.date,
                    'name': line.name,
                    'reference': line.name,
                    'journal_id': purchase_journal.id,
                    'payment_journal_id':expenses.journal_payment_id.id,  # plata prin jurnalu de decont chelturili
                    'expenses_deduction_id': expenses.id,
                    #'account_id': expenses.journal_payment_id.default_debit_account_id.id,  # 542
                    'account_id': partner_id.property_account_receivable_id.id,
                    # aici trebuie sa fie contul din care se face plata furnizorului
                    'line_ids': [(0, 0, {'name': line.name,
                                         'price_unit': line.price_subtotal,
                                         'tax_ids': [(6, 0, line.tax_ids.ids)],
                                         'account_id': line.expense_account_id.id})]
                }
                vouchers |= self.env['account.voucher'].create(voucher_value)
                payment_methods = expenses.journal_payment_id.outbound_payment_method_ids

                # payment_value = {
                #     'payment_type': 'outbound',
                #     'payment_date': line.date,
                #     'partner_type': 'supplier',
                #     'partner_id': partner_id.id,
                #     'journal_id': expenses.journal_payment_id.id,
                #     'payment_method_id': payment_methods and payment_methods[0].id or False,
                #     'amount': line.tax_amount + line.price_subtotal ,
                #     'expenses_deduction_id': expenses.id,
                # }
                # payments |= self.env['account.payment'].create(payment_value)
            vouchers.with_context(expenses_deduction_id=expenses.id).proforma_voucher()  # validare
            payments.post()

            move_lines = self.env['account.move.line']
            for voucher in vouchers:
                for aml in voucher.move_id.line_ids:
                    if aml.account_id.internal_type == 'payable':
                        move_lines |= aml

            for payment in payments:
                for aml in payment.move_line_ids:
                    if aml.account_id.internal_type == 'payable':
                        move_lines |= aml

            move_lines.reconcile()
            # Create the account move record.
            line_ids = []
            # nota contabila prin care banii au iesit din casa
            if expenses.advance:
                #todo: de ce nu tine cont de data avansului ?
                move_line_dr = {'name': name or '/', 'debit': expenses.advance, 'credit': 0.0,
                                'account_id': expenses.journal_payment_id.default_debit_account_id.id,  # 542
                                'journal_id': expenses.journal_id.id, 'partner_id': expenses.employee_id.id,
                                'date': expenses.date_advance, 'date_maturity': expenses.date_advance}
                move_line_cr = {'name': name or '/', 'debit': 0.0, 'credit': expenses.advance,
                                'account_id': expenses.journal_id.default_credit_account_id.id,  # 512
                                'journal_id': expenses.journal_id.id, 'partner_id': expenses.employee_id.id,
                                'date': expenses.date_advance, 'date_maturity': expenses.date_advance}
                line_ids.append([0, False, move_line_dr])
                line_ids.append([0, False, move_line_cr])

            if expenses.difference < 0:
                move_line_cr = {'name': name or '/', 'debit': 0.0, 'credit': abs(expenses.difference),
                                'account_id': expenses.journal_payment_id.default_credit_account_id.id,
                                'journal_id': expenses.journal_id.id, 'partner_id': expenses.employee_id.id,
                                'date': expenses.date_expense, 'date_maturity': expenses.date_expense}
                move_line_dr = {'name': name or '/', 'debit': abs(expenses.difference), 'credit': 0.0,
                                'account_id': expenses.journal_id.default_debit_account_id.id,
                                'journal_id': expenses.journal_id.id,
                                'partner_id': expenses.employee_id.id, 'date': expenses.date_expense,
                                'date_maturity': expenses.date_expense}
                line_ids.append([0, False, move_line_dr])
                line_ids.append([0, False, move_line_cr])

            if expenses.difference > 0:
                move_line_cr = {'name': name or '/', 'debit': expenses.difference, 'credit': 0.0,
                                'account_id': expenses.journal_payment_id.default_credit_account_id.id,
                                'journal_id': expenses.journal_id.id, 'partner_id': expenses.employee_id.id,
                                'date': expenses.date_expense, 'date_maturity': expenses.date_expense}
                move_line_dr = {'name': name or '/', 'debit': 0.0, 'credit': expenses.difference,
                                'account_id': expenses.journal_id.default_debit_account_id.id,
                                'journal_id': expenses.journal_id.id,
                                'partner_id': expenses.employee_id.id, 'date': expenses.date_expense,
                                'date_maturity': expenses.date_expense}
                line_ids.append([0, False, move_line_dr])
                line_ids.append([0, False, move_line_cr])

            if expenses.total_diem:
                move_line_dr = {'name': name or '/', 'debit': expenses.total_diem, 'credit': 0.0,
                                'account_id': expenses.account_diem_id.id, 'journal_id': expenses.journal_id.id,
                                'partner_id': expenses.employee_id.id, 'date': expenses.date_expense,
                                'date_maturity': expenses.date_expense}
                move_line_cr = {'name': name or '/', 'debit': 0.0, 'credit': expenses.total_diem,
                                'account_id': expenses.journal_payment_id.default_credit_account_id.id,  # 542
                                'journal_id': expenses.journal_id.id, 'partner_id': expenses.employee_id.id,
                                'date': expenses.date_expense, 'date_maturity': expenses.date_expense}
                line_ids.append([0, False, move_line_dr])
                line_ids.append([0, False, move_line_cr])

            expenses_vals = {'state': 'done', 'number': name}
            if line_ids:
                move = self.env['account.move'].create({'name': name or '/',
                                                        'journal_id': expenses.journal_id.id,
                                                        'date': expenses.date_expense,
                                                        'ref': name or '',
                                                        'line_ids': line_ids, })
                expenses_vals['move_id'] = move.id

            expenses.write(expenses_vals)
            expenses.write_to_statement_line()

    @api.multi
    def write_to_statement_line(self):

        def get_statement(journal_id, date):
            statement = self.env['account.bank.statement'].search(
                [('journal_id', '=', journal_id.id), ('date', '=', date)])
            if not statement:
                vals = {'journal_id': journal_id.id, 'state': 'open', 'date': date, }
                statement = self.env['account.bank.statement'].create(vals)
                statement.onchange_journal_id()
                statement.button_open()
            else:
                statement = statement[0]

            if statement.state != 'open':
                raise UserError(_('The cash statement of journal %s from date is not in open state, please open it \n'
                                  'to create the line in  it "%s".') % (journal_id.name, date))
            return statement

        for expenses in self:
            if expenses.journal_id.type == 'cash':
                if expenses.advance:
                    statement = get_statement(expenses.journal_id, expenses.date_advance)
                    args = {'amount': - expenses.advance, 'date': expenses.date_advance, 'name': _("Decont cheltuieli"),
                            'account_id': False, 'partner_id': expenses.employee_id.id, 'statement_id': statement.id,
                            'journal_id': expenses.journal_id.id, 'ref': str(expenses.number),
                            # 'voucher_id': voucher.id,
                            'journal_entry_id': expenses.move_id.id, 'expenses_deduction_id': expenses.id}
                    self.env['account.bank.statement.line'].create(args)
                if expenses.difference:
                    statement = get_statement(expenses.journal_id, expenses.date_expense)
                    args = {'amount': - expenses.difference, 'date': expenses.date_expense,
                            'name': _("Decont cheltuieli"), 'account_id': False, 'partner_id': expenses.employee_id.id,
                            'statement_id': statement.id, 'journal_id': expenses.journal_id.id,
                            'ref': str(expenses.number),
                            # 'voucher_id': voucher.id,
                            'journal_entry_id': expenses.move_id.id, 'expenses_deduction_id': expenses.id}
                    self.env['account.bank.statement.line'].create(args)

        return True

    @api.multi
    def cancel_expenses(self):
        self.write({'state': 'cancel'})
        return True


class deltatech_expenses_deduction_line(models.Model):
    _name = 'deltatech.expenses.deduction.line'
    _description = 'Expenses Deduction Line'

    @api.model
    def _default_expense_account(self):
        account_pool = self.env['account.account']
        account = account_pool.search([('code', '=ilike', '623%')], limit=1)  ## cheltuieli de protocol
        if not account:
            account = account_pool.search([('user_type_id.name', '=', 'expense'),
                                           ('internal_type', '!=', 'view')], limit=1)
        return account

    expenses_deduction_id = fields.Many2one('deltatech.expenses.deduction', string='Expenses Deduction', required=False)
    date = fields.Date("Bill Date", index=True, copy=False, default=fields.Date.context_today)
    name = fields.Text(string='Reference', required=True)
    tax_ids = fields.Many2many('account.tax', string='Tax', help="Only for tax excluded from price")

    amount = fields.Float(string='Total')  # e cu tot cu tva ?
    tax_amount = fields.Float(readonly=True, store=True, compute='_compute_subtotal')
    price_subtotal = fields.Float(readonly=True, store=True, compute='_compute_subtotal') # valoare subtotal

    # todo: de scos required si de acompletat cu partner_generic in situatia in care nu se completeaza nimic
    partner_id = fields.Many2one('res.partner', string='Partner')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, default=lambda self: self._get_currency())

    expense_account_id = fields.Many2one('account.account',
                                         default=_default_expense_account,
                                         string='Default Expense Account')

    state = fields.Selection(related='expenses_deduction_id.state')

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(self._context.get('journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        return self.env.user.company_id.currency_id.id

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    @api.one
    @api.depends('amount', 'tax_ids')
    def _compute_subtotal(self):
        tax_amount = 0.0
        price_subtotal = self.amount
        if self.tax_ids:
            tax_info = self.tax_ids.compute_all(self.amount, self.currency_id, quantity=1, partner=self.partner_id)
            tax_amount += sum([t.get('amount', 0.0) for t in tax_info.get('taxes', False)])
            price_subtotal = tax_info['total_excluded']
        self.tax_amount = tax_amount
        self.price_subtotal = price_subtotal
