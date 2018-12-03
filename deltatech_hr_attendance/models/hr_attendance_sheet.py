# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_round
import calendar
import time
from datetime import datetime, timedelta, date
import pytz


def utc_to_local(event_time):
    tz_name = "Europe/Bucharest"
    tz = pytz.timezone(tz_name)

    event_time = pytz.UTC.localize(event_time).astimezone(tz).replace(tzinfo=None)

    return event_time


class HrAttendanceSheet(models.Model):
    _name = "hr.attendance.sheet"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Note", states={'confirm': [('readonly', True)], 'done': [('readonly', True)]})
    company_id = fields.Many2one(comodel_name='res.company')
    date_from = fields.Date('Start Date', required=True, readonly=True, states={
        'draft': [('readonly', False)],
        'new': [('readonly', False)]})
    date_to = fields.Date('End Date', required=True, readonly=True, states={
        'draft': [('readonly', False)],
        'new': [('readonly', False)]})

    division_id = fields.Many2one('hr.department', string='Division', required=True, readonly=True,
                                  domain=[('type','=','div')],
                                  states={
        'draft': [('readonly', False)],
        'new': [('readonly', False)]})



    department_id = fields.Many2one('hr.department', string='Department', required=True, readonly=True,
                                    domain=[('type', '=', 'dep')],
                                    states={
        'draft': [('readonly', False)],
        'new': [('readonly', False)]})

    formation_id = fields.Many2one('hr.department', string='Formation', required=True, readonly=True,
                                    domain=[('type', '=', 'for')],
                                    states={
                                        'draft': [('readonly', False)],
                                        'new': [('readonly', False)]})

    state = fields.Selection([
        ('new', 'New'),
        ('draft', 'Open'),
        ('confirm', 'Waiting Approval'),
        ('done', 'Approved')], default='new', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Open\' status is used when a user is encoding a new and unconfirmed timesheet. '
             '\n* The \'Waiting Approval\' status is used to confirm the timesheet by user. '
             '\n* The \'Approved\' status is used when the users timesheet is accepted by his/her senior.')
    line_ids = fields.One2many('hr.attendance.sheet.line', 'sheet_id', readonly=True, states={
        'draft': [('readonly', False)]})

    employee_id = fields.Many2one('hr.employee', related='line_ids.employee_id', string='Employee' )





    @api.onchange('division_id')
    def onchange_division_id(self):
        if not self.division_id:
            return
        if self.division_id != self.department_id.parent_id:
            self.department_id = False
        return {
            'domain': {'department_id': [('parent_id', '=', self.division_id.id)]},
        }

    @api.onchange('department_id')
    def onchange_department_id(self):
        if not self.department_id:
            return
        self.division_id = self.department_id.parent_id
        if self.department_id != self.formation_id.parent_id:
            self.formation_id = False
        return {
            'domain': {'formation_id': [('parent_id', '=', self.department_id.id)]},
        }

    @api.onchange('formation_id')
    def onchange_formation_id(self):
        if not self.formation_id:
            return
        self.department_id = self.formation_id.parent_id



    @api.multi
    def name_get(self):
        # week number according to ISO 8601 Calendar
        return [(r['id'], _('Week ') + str(datetime.strptime(r['date_from'], '%Y-%m-%d').isocalendar()[1]))
                for r in self.read(['date_from'], load='_classic_write')]

    @api.model
    def default_get(self, fields_list):
        res = super(HrAttendanceSheet, self).default_get(fields_list)
        today = fields.Date.context_today(self)
        today = fields.Date.from_string(today)
        from_date = today + relativedelta(weekday=0, days=-7)
        to_date = today + relativedelta(weekday=6)
        # from_date = (today + relativedelta(day=1, months=0, days=0))
        # to_date = (today + relativedelta(day=1, months=1, days=-1))
        res['date_from'] = fields.Date.to_string(from_date)
        res['date_to'] = fields.Date.to_string(to_date)
        return res

    @api.onchange('date_from')
    def onchange_date_from(self):
        if self.date_from:
            date_from = fields.Date.from_string(self.date_from)
            date_to = date_from + relativedelta(days=6)
            self.date_to = fields.Date.to_string(date_to)

    @api.multi
    def do_compute(self):
        self.ensure_one()
        employees = self.env['hr.employee'].search([('department_id', '=', self.formation_id.id),
                                                    ('shift', 'in', ['F', 'T'])])
        attendances = self.env['hr.attendance'].search([('employee_id', 'in', employees.ids),
                                                      ('for_date', '>=', self.date_from),
                                                      ('for_date', '<=', self.date_to)])
        for attendance in attendances:
            date_time_in = fields.Datetime.from_string(attendance.check_in)
            date_time_in = utc_to_local(date_time_in)
            date_in = fields.Date.to_string(date_time_in)
            if date_in != attendance.for_date:
                attendance.write({'for_date': date_in})

        lines = self.line_ids.filtered(lambda x: x.state not in ('done'))
        lines.unlink()
        query = """
           SELECT   for_date, employee_id, sum(worked_hours), min(check_in), max(check_out), array_agg(hr_attendance.id)
              FROM hr_attendance JOIN hr_employee on hr_attendance.employee_id = hr_employee.id
                 WHERE for_date >= %s AND for_date <= %s and 
                 ( hr_employee.department_id = %s or hr_attendance.department_id = %s ) 
                 GROUP BY for_date, employee_id
                 ORDER BY for_date desc
        """
        params = (self.date_from, self.date_to, self.formation_id.id, self.formation_id.id)

        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            values = {
                'sheet_id': self.id,
                'department_id': self.formation_id.id,
                'date': row[0],
                'employee_id': row[1],
                'attendance_hours': row[2],
                'check_in': row[3],
                'check_out': row[4],
                'attendance_ids': [(6, 0, list(row[5]))]
            }
            line = self.env['hr.attendance.sheet.line'].search( [('date', '=', values['date']),
                                                                 ('employee_id', '=', values['employee_id'])])

            if len(line) == 1:
                if line.sheet_id.id != self.id:
                    line.write({'sheet_id': self.id})
            else:
                line.unlink()
                self.env['hr.attendance.sheet.line'].create(values)


        self.write({'state': 'draft'})

    def button_show(self):

        action = self.env.ref('deltatech_hr_attendance.action_hr_attendance_sheet_line').read()[0]
        action['domain'] = [('sheet_id', '=', self.id)]
        action['context'] = {'active_id': self.id, 'active_model': self._name }
        return action

    @api.multi
    def action_timesheet_draft(self):
        if not self.env.user.has_group('deltatech_hr_attendance.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse timesheets or reset them to draft.'))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_timesheet_confirm(self):
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_timesheet_done(self):
        if not self.env.user.has_group('deltatech_hr_attendance.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can approve timesheets.'))
        if self.filtered(lambda sheet: sheet.state != 'confirm'):
            raise UserError(_("Cannot approve a non-submitted timesheet."))
        self.write({'state': 'done'})

    @api.multi
    def button_show_grid(self):
        self.ensure_one()
        action = self.env.ref('deltatech_hr_attendance.action_attendance_summary')

        vals = action.read()[0]
        vals['context'] = {'active_id': self.id, 'active_model': self._name}
        return vals

    # @api.multi
    # def print_report(self, report_type='qweb'):
    #     res = self.env.ref('deltatech_hr_attendance.action_report_attendance_summary_pdf').report_action(self)
    #     return res

    @api.multi
    def print_report(self, report_type='qweb-pdf'):
        self.ensure_one()
        report_name = 'deltatech_hr_attendance.report_attendance_summary'
        context = dict(self.env.context)
        context['active_model'] = self._name
        action = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('model', '=', self._name),
             ('report_type', '=', report_type)], limit=1)
        return action.with_context(context).report_action(self)


    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            html = self.env.ref('deltatech_hr_attendance.action_attendance_summary_control').render_qweb_html(
                report.ids)
            result['html'] = html[0]

        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()


class HrAttendanceSheetLine(models.Model):
    _name = "hr.attendance.sheet.line"
    _description = "Daily Attendance"
    _order = 'check_in'

    sheet_id = fields.Many2one('hr.attendance.sheet',  ondelete='set null', index=True)

    department_id = fields.Many2one('hr.department', string='Formation', required=True,
                                    domain="[('type','=','for')]")
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True)
    date = fields.Date(index=True)
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    hour_from = fields.Float(string='Work from', compute="_compute_hours", store=True)
    hour_to = fields.Float(string='Work to', compute="_compute_hours", store=True)

    attendance_ids = fields.Many2many("hr.attendance", ondelete='restrict')
    attendance_hours = fields.Float(string='Attendance Hours', readonly=True)
    effective_hours = fields.Float(string='Effective Hours', compute="_compute_hours", store=True, readonly=False)

    worked_hours = fields.Float(string='Worked Hours', compute="_compute_hours", store=True, readonly=False)
    overtime = fields.Float(string='Overtime', compute="_compute_hours", store=True, readonly=False)
    overtime_granted = fields.Float(string='Overtime Granted', compute="_compute_hours", store=True, readonly=False)
    total_hours = fields.Float(string='Total Hours', compute="_compute_total_hours", store=True)
    night_hours = fields.Float(string='Night Hours', compute="_compute_hours", store=True, readonly=False)

    shift = fields.Selection([('S1', 'Shift 1'), ('S2', 'Shift 2'), ('S3', 'Shift 3'), ('T', 'Tesa'), ('F', 'Free')],
                             compute="_compute_hours", store=True, readonly=False)
    late_in = fields.Float(compute="_compute_hours", store=True, readonly=False)
    early_out = fields.Float(compute="_compute_hours", store=True, readonly=False)
    late_out = fields.Float(compute="_compute_hours", store=True, readonly=False)
    early_in = fields.Float(compute="_compute_hours", store=True, readonly=False)
    breaks = fields.Float(compute="_compute_hours", store=True, readonly=False)

    state = fields.Selection([('draft', 'Draft'), ('ok', 'Ok'), ('not_ok', 'Not OK'),
                              ('need', 'Need attention'), ('done', 'Confirmed')],
                             default='draft', compute="_compute_hours", store=True)
    working_day = fields.Float(default=1, string="Working Day")
    comments = fields.Char()

    #holiday_id = fields.Many2one('hr.holidays')

    def _date_is_day_off(self, date):
        if isinstance(date,str):
            date = fields.Date.from_string(date)
        return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)

    @api.multi
    def adjust_grid(self, row_domain, column_field, column_value, cell_field, change):
        if column_field != 'date' or cell_field != 'unit_amount':
            raise ValueError(
                "{} can only adjust unit_amount (got {}) by date (got {})".format(
                    self._name,
                    cell_field,
                    column_field,
                ))

        additionnal_domain = self._get_adjust_grid_domain(column_value)
        domain = expression.AND([row_domain, additionnal_domain])
        line = self.search(domain)
        if len(line) > 1:
            raise UserError(_(
                'Multiple timesheet entries match the modified value. Please '
                'change the search options or modify the entries individually.'
            ))

        if line:  # update existing line
            line.write({
                cell_field: line[cell_field] + change
            })
        else:  # create new one
            day = column_value.split('/')[0]
            self.search(row_domain, limit=1).copy({
                'name': False,
                column_field: day,
                cell_field: change
            })
        return False

    def _get_adjust_grid_domain(self, column_value):
        # span is always daily and value is an iso range
        day = column_value.split('/')[0]
        return [('name', '=', False), ('date', '=', day)]

    @api.multi
    @api.depends('worked_hours', 'overtime_granted')
    def _compute_total_hours(self):
        for item in self:
            item.total_hours = item.worked_hours + item.overtime_granted

    @api.model
    def calcul(self, prog, prog_out):
        line = self
        values = {}
        if not line.check_in:
            return values

        check_in = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(line.check_in))
        hour_from = check_in.hour + check_in.minute / 60.0
        diff = {
            'S1': abs(prog['S1'] - hour_from),
            'S2': abs(prog['S2'] - hour_from),
            'S3': abs(prog['S3'] - hour_from),
            'T': abs(prog['T'] - hour_from),
        }
        shift = min(diff, key=diff.get)
        values['shift'] = shift
        diff = prog[shift] - hour_from
        if abs(diff) > 1:
            values['hour_from'] = hour_from
            values['state'] = 'not_ok'

        check_out = fields.Datetime.from_string(line.check_out or line.check_in)
        check_out = fields.Datetime.context_timestamp(self, check_out)
        hour_to = check_out.hour + check_out.minute / 60.0

        diff = {
            'S1': abs(prog_out['S1'] - hour_to),
            'S2': abs(prog_out['S2'] - hour_to),
            'S3': abs(prog_out['S3'] - hour_to),
            'T': abs(prog_out['T'] - hour_to),
        }

        shift = min(diff, key=diff.get)

        if values['shift'] != shift:
            values['shift'] = False
            values['hour_from'] = hour_from
            values['hour_to'] = hour_to
            values['state'] = 'not_ok'
            values.update(self.compute_witout_shift())
        else:
            values.update(self.compute_on_shift(shift))

        if values['state'] == 'ok' and values['worked_hours'] != 8:
            values['state'] = 'need'

        return values

    @api.depends('check_in', 'check_out')
    @api.multi
    def _compute_hours(self):
        prog, prog_out = self.get_shifts()
        for line in self:
            if line.employee_id.shift:
                values = line.compute_on_shift(line.employee_id.shift)
            else:
                values = line.calcul(prog, prog_out)
            line.update(values)

    def get_shifts(self):
        day_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_start', 6)
        day_tesa_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_tesa_start', 8)
        prog = {
            'S1': day_start,
            'S2': day_start + 8,
            'S3': day_start + 16,
            'T': day_tesa_start,
            'F': 0
        }
        prog_out = {
            'S1': (prog['S1'] + 8) % 24,
            'S2': (prog['S2'] + 8) % 24,
            'S3': (prog['S3'] + 8) % 24,
            'T': (prog['T'] + 8) % 24,
            'F': 24
        }
        return prog, prog_out

    @api.model
    def compute_witout_shift(self):
        values = {}
        worked_hours = self.attendance_hours
        if worked_hours > 8:
            values['overtime'] = worked_hours - 8
            values['worked_hours'] = 8
        else:
            values['worked_hours'] = worked_hours

        return values



    @api.model
    def compute_on_shift(self, shift):

        values = {'shift': shift}

        prog, prog_out = self.get_shifts()

        check_in = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.check_in))
        hour_from = check_in.hour + check_in.minute / 60.0
        check_out = fields.Datetime.context_timestamp(self,
                                                      fields.Datetime.from_string(self.check_out or self.check_in))
        hour_to = check_out.hour + check_out.minute / 60.0

        t_diff = relativedelta(check_out, check_in)

        worked_hours = 24*t_diff.days +  t_diff.hours + t_diff.minutes / 60 + t_diff.seconds / 60 / 60
        if worked_hours > 24:
            values['state'] = 'not_ok'
        else:
            values['state'] = 'ok'

        for attendance in self.attendance_ids:
            if attendance.state != 'ok':
                values['state'] = 'not_ok'

        breaks = worked_hours - self.attendance_hours
        effective_hours = self.attendance_hours

        values['hour_from'] = prog[shift]
        values['hour_to'] = prog_out[shift]

        norm_work_hours = 7 + 40 / 60
        overtime = 0
        if shift == 'F':
            values['night_hours'] = 0
            values['hour_from'] = hour_from
            values['hour_to'] = hour_to
            if effective_hours > norm_work_hours:
                overtime = effective_hours - norm_work_hours
            diff = prog['S1'] - hour_from
            if diff > 0:
                values['night_hours'] += diff
            diff = hour_to - prog['S3']
            if diff > 0:
                values['night_hours'] += diff
        else:
            diff = prog[shift] - hour_from

            if diff < 0:
                values['late_in'] = abs(diff)
                values['early_in'] = 0
            else:
                values['late_in'] = 0
                values['early_in'] = diff
                if diff >= 1:  # daca a venit cu mai mult de o ora mai devreme se considera ora suplimentara
                    overtime += diff
                effective_hours = effective_hours - diff

            diff = hour_to - prog_out[shift]
            if diff < 0:
                values['late_out'] = 0
                values['early_out'] = abs(diff)
            else:
                values['late_out'] = diff
                values['early_out'] = 0
                overtime += diff
                effective_hours = effective_hours - diff

        # 7:40  trebuie sa sta in pauza
        # rotunjurea la ora suplimentara

        if effective_hours >= 7 or worked_hours >= 8:
            worked_hours = 8.0

        values['effective_hours'] = effective_hours
        values['breaks'] = float_round(breaks, precision_rounding=0.1)

        values['overtime'] = overtime
        values['overtime_granted'] = float_round(overtime, precision_rounding=1)
        values['worked_hours'] = worked_hours

        if shift[0] == 'S':
            if values['breaks'] > 25 / 60 and overtime < 1:
                values['worked_hours'] = worked_hours - max(values['breaks'], 1) + values['overtime_granted']
                values['state'] = 'need'
                values['overtime_granted'] = 0.0

            if overtime >= 1 and values['breaks'] > 25 / 60:
                values['worked_hours'] = worked_hours
                values['overtime'] = overtime - (values['breaks'] - 20 / 60)
                values['overtime_granted'] = float_round(values['overtime'], precision_rounding=1)

        if shift == 'S1' and values['early_in'] >= 1:
            values['night_hours'] = values['early_in']

        if shift == 'S2' and values['late_out'] > 0.5:
            values['night_hours'] = values['late_out']

        if shift == 'S3':
            values['night_hours'] = values['worked_hours']

        if shift == 'T':  # tesa
            values['worked_hours'] = min(8, worked_hours)
            values['overtime_granted'] = 0.0
            values['night_hours'] = 0.0

        if self._date_is_day_off(self.date):
            values['overtime_granted'] = values['overtime'] + values['worked_hours']
            values['worked_hours'] = 0


        return values

    @api.onchange('shift')
    def onchange_shift(self):
        if not self.shift:
            return
        values = self.compute_on_shift(self.shift)
        self.update(values)

    @api.multi
    def action_confirm(self):
        if not self.shift:
            self.write({'state': 'done', 'shift': 'F'})
        else:
            self.write({'state': 'done'})

    @api.multi
    def action_invalidate(self):
        for item in self:
            if item.shift:
                values = self.compute_on_shift(item.shift)
                item.write(values)
            else:
                self.write({'state': 'not_ok'})

    @api.multi
    def action_set_shift(self):
        self.ensure_one()
        self.employee_id.write({'shift': self.shift})

    @api.multi
    def action_attendance_details(self):
        self.ensure_one()
        # hr_attendance_action
        context = {'display_button_add_minus': True}
        action = {
            'name': _('Attendance'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': context,
            'res_model': 'hr.attendance',
            'domain': [('id', 'in', self.attendance_ids.ids)]
        }

        return action

    @api.multi
    def name_get(self):
        result = []
        for line in self:
            result.append((line.id, ('%s %s') % (line.employee_id.name, line.date)))

        return result

    @api.multi
    def unlink(self):
        for line in self:
            if line.state == 'done':
                raise UserError(_('Cannot delete a daily attendance for % in Confirmed state in date %s') % (line.employee_id.name, line.date))
        # if any(line.state == 'done' for line in self):
        #     raise UserError(_('Cannot delete a daily attendance in Confirmed state '))
        return super(HrAttendanceSheetLine, self).unlink()