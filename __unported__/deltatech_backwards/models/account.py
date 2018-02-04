# coding=utf-8



from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.osv import expression


class AccountMove(models.Model):
    _inherit = "account.move"

    period_id = fields.Many2one('account.period')
    # line_ids = fields.One2many('account.move.line', related='line_id')


class AccountFiscalYear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"

    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], 'Status', readonly=True, copy=False,
                             default='draft')
    end_journal_period_id = fields.Many2one(  'account.journal.period', 'End of Year Entries Journal',
        readonly=True, copy=False)

    _order = "date_start, id"

    @api.constrains('date_stop', 'date_stop')
    def _check_duration(self):
        obj_fy = self
        if obj_fy.date_stop < obj_fy.date_start:
            raise UserError('Error!\nThe start date of a fiscal year must precede its end date.')
        return True

    @api.multi
    def create_period3(self):
        return self.create_periods(3)

    @api.multi
    def create_period(self):
        return self.create_periods(interval=1)

    @api.multi
    def create_periods(self, interval=1):
        period_obj = self.env['account.period']
        for fy in self:
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            period_obj.create({
                'name': "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_start': ds,
                'date_stop': ds,
                'special': True,
                'fiscalyear_id': fy.id,
            })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:

                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    @api.model
    def find(self, dt=None, exception=True):
        res = self.finds(dt, exception)
        return res and res[0] or False

    @api.model
    def finds(self, dt=None, exception=True):

        if not dt:
            dt = fields.Date.context_today(self)
        args = [('date_start', '<=', dt), ('date_stop', '>=', dt)]
        context = self.env.context
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.env.user.company_id.id
        args.append(('company_id', '=', company_id))
        ids = self.search(args)
        if not ids:
            if exception:
                model, action_id = self.env['ir.model.data'].get_object_reference('deltatech_backwards',
                                                                                  'action_account_fiscalyear')
                msg = _( 'There is no period defined for this date: %s.\nPlease go to Configuration/Periods and configure a fiscal year.') % dt
                raise RedirectWarning(msg, action_id, _('Go to the configuration panel'))
            else:
                return []
        return ids

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('code', operator, name), ('name', operator, name)]
        else:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        res = self.search(expression.AND([domain, args]), limit=limit)
        return res.name_get()


class AccountPeriod(models.Model):
    _name = "account.period"
    _description = "Account period"

    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    special = fields.Boolean('Opening/Closing Period', help="These periods can overlap.")
    date_start = fields.Date('Start of Period', required=True, states={'done': [('readonly', True)]})
    date_stop = fields.Date('End of Period', required=True, states={'done': [('readonly', True)]})
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True,
                                    states={'done': [('readonly', True)]}, index=True)
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], 'Status', readonly=True, copy=False,
                             default="draft",
                             help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')
    company_id = fields.Many2one('res.company', related='fiscalyear_id.company_id', string='Company', store=True,
                                 readonly=True)

    _order = "date_start, special desc"
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]

    @api.multi
    def _check_duration(self):
        obj_period = self
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    @api.multi
    def _check_year_limit(self):
        for obj_period in self:
            if obj_period.special:
                continue

            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
                            obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
                            obj_period.fiscalyear_id.date_start > obj_period.date_start or \
                            obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                return False

            pids = self.search([('date_stop', '>=', obj_period.date_start), ('date_start', '<=', obj_period.date_stop),
                                ('special', '=', False), ('id', '<>', obj_period.id)])
            for period in pids:
                if period.fiscalyear_id.company_id.id == obj_period.fiscalyear_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
        (_check_year_limit,
         'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.',
         ['date_stop'])
    ]

    """
    @api.returns('self')
    def next(self, cr, uid, period, step, context=None):
        ids = self.search(cr, uid, [('date_start','>',period.date_start)])
        if len(ids)>=step:
            return ids[step-1]
        return False
    """

    @api.model
    @api.returns('self')
    def find(self, dt=None):

        if not dt:
            dt = fields.Date.context_today()
        args = [('date_start', '<=', dt), ('date_stop', '>=', dt)]
        context = self.env.context
        if context.get('company_id', False):
            args.append(('company_id', '=', context['company_id']))
        else:
            company_id = self.env.user.company_id.id
            args.append(('company_id', '=', company_id))
        result = []
        if context.get('account_period_prefer_normal', True):
            # look for non-special periods first, and fallback to all if no result is found
            result = self.search(args + [('special', '=', False)])
        if not result:
            result = self.search(args)
        if not result:
            model, action_id = self.env['ir.model.data'].get_object_reference('deltatech_backwards',
                                                                              'action_account_period')
            msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods.') % dt
            raise RedirectWarning(msg, action_id, _('Go to the configuration panel'))
        return result

    """

    @api.multi
    def action_draft(self):
        mode = 'draft'
        for period in self:
            if period.fiscalyear_id.state == 'done':
                raise UserError( _('You can not re-open a period which belongs to closed fiscal year'))
        self.env.cr.execute('update account_journal_period set state=%s where period_id in %s', (mode, tuple(self.ids),))
        self.env.cr.execute('update account_period set state=%s where id in %s', (mode, tuple(self.ids),))
        self.invalidate_cache()
        return True


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('code', operator, name), ('name', operator, name)]
        else:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        res = self.search( expression.AND([domain, args]), limit=limit)
        return res.name_get()

    @api.multi
    def write(self,  vals ):
        if 'company_id' in vals:
            move_lines = self.env['account.move.line'].search([('period_id', 'in', self.ids)])
            if move_lines:
                raise UserError(_('This journal already contains items for this period, therefore you cannot modify its company field.'))
        return super(AccountPeriod, self).write( vals)


    @api.multi
    def build_ctx_periods(self,  period_from_id, period_to_id):
        if period_from_id == period_to_id:
            return [period_from_id]
        period_from = self.browse(  period_from_id)
        period_date_start = period_from.date_start
        company1_id = period_from.company_id.id
        period_to = self.browse(  period_to_id)
        period_date_stop = period_to.date_stop
        company2_id = period_to.company_id.id
        if company1_id != company2_id:
            raise UserError( _('You should choose the periods that belong to the same company.'))
        if period_date_start > period_date_stop:
            raise UserError( _('Start period should precede then end period.'))

        # /!\ We do not include a criterion on the company_id field below, to allow producing consolidated reports
        # on multiple companies. It will only work when start/end periods are selected and no fiscal year is chosen.

        #for period from = january, we want to exclude the opening period (but it has same date_from, so we have to check if period_from is special or not to include that clause or not in the search).
        if period_from.special:
            return self.search(  [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop)])
        return self.search(  [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop), ('special', '=', False)])

    """
