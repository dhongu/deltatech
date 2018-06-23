# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


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
    department_id = fields.Many2one('hr.department', string='Department', required=True, readonly=True, states={
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

    @api.constrains('date_to', 'date_from', 'department_id')
    def _check_sheet_date(self ):
        for sheet in self:
                self.env.cr.execute('''
                     SELECT id
                     FROM hr_attendance_sheet
                     WHERE (date_from <= %s and %s <= date_to)
                         AND department_id=%s
                         AND id <> %s''',
                                    (sheet.date_to, sheet.date_from, sheet.department_id.id, sheet.id))
                if any(self.env.cr.fetchall()):
                    raise ValidationError(_( 'You cannot have 2 timesheets that overlap!'))

    @api.model
    def default_get(self, fields_list):
        res = super(HrAttendanceSheet, self).default_get(fields_list)
        today = fields.Date.context_today(self)
        today = fields.Date.from_string(today)

        from_date = (today + relativedelta(day=1, months=0, days=0))
        to_date = (today + relativedelta(day=1, months=1, days=-1))
        res['date_from'] = fields.Date.to_string(from_date)
        res['date_to'] = fields.Date.to_string(to_date)
        return res

    @api.multi
    def do_compute(self):
        self.line_ids.unlink()
        query = """
           SELECT   for_date, employee_id, sum(worked_hours), min(check_in), max(check_out), array_agg(hr_attendance.id)
              FROM hr_attendance JOIN hr_employee on hr_attendance.employee_id = hr_employee.id
                 WHERE for_date > %s AND for_date < %s and hr_employee.department_id = %s 
                 GROUP BY for_date, employee_id
                 ORDER BY for_date desc
        """
        params = (self.date_from, self.date_to, self.department_id.id)

        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            values = {
                'sheet_id': self.id,
                'department_id': self.department_id.id,
                'date': row[0],
                'employee_id': row[1],
                'attendance_hours': row[2],
                'check_in': row[3],
                'check_out': row[4],
                'attendance_ids': [(6, 0, list(row[5]))]
            }
            self.env['hr.attendance.sheet.line'].create(values)
        self.write({'state':'draft'})

    def button_show(self):
        self.do_compute()
        action = self.env.ref('deltatech_hr_attendance.action_hr_attendance_sheet_line').read()[0]
        action['domain'] = [('sheet_id', '=', self.id)]
        action['context'] = {'active_id': self.id}
        return action


    @api.multi
    def action_timesheet_draft(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse timesheets or reset them to draft.'))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_timesheet_confirm(self):
        for sheet in self:
            if sheet.employee_id and sheet.employee_id.parent_id and sheet.employee_id.parent_id.user_id:
                self.message_subscribe_users(user_ids=[sheet.employee_id.parent_id.user_id.id])
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_timesheet_done(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can approve timesheets.'))
        if self.filtered(lambda sheet: sheet.state != 'confirm'):
            raise UserError(_("Cannot approve a non-submitted timesheet."))
        self.write({'state': 'done'})



class HrAttendanceSheetLine(models.TransientModel):
    _name = "hr.attendance.sheet.line"
    _order = 'check_in'

    sheet_id = fields.Many2one('hr.attendance.sheet')

    department_id = fields.Many2one('hr.department', string='Department', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date()
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    hour_from = fields.Float(string='Work from', compute="_compute_hours", store=True)
    hour_to = fields.Float(string='Work to', compute="_compute_hours", store=True)

    attendance_ids = fields.Many2many("hr.attendance")
    attendance_hours = fields.Float(string='Attendance Hours')
    worked_hours = fields.Float(string='Worked Hours', compute="_compute_hours", store=True, readonly=False)
    shift = fields.Selection([('S1', 'Shift 1'), ('S2', 'Shift 2'), ('S3', 'Shift 3'), ('T', 'Tesa')],
                             compute="_compute_hours", store=True, readonly=False)
    late_in = fields.Float(compute="_compute_hours", store=True, readonly=False)
    early_out = fields.Float(compute="_compute_hours", store=True, readonly=False)
    late_out = fields.Float(compute="_compute_hours", store=True, readonly=False)
    early_in = fields.Float(compute="_compute_hours", store=True, readonly=False)
    breaks = fields.Float(compute="_compute_hours", store=True, readonly=False)

    # is_ok = fields.Boolean()

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


    @api.depends('check_in', 'check_out')
    @api.multi
    def _compute_hours(self):
        day_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_start', 6)
        day_tesa_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_tesa_start', 8)
        prog = {
            'S1': day_start,
            'S2': day_start + 8,
            'S3': day_start + 16,
            'T': day_tesa_start
        }
        prog_out = {
            'S1': (prog['S1'] + 8) % 24,
            'S2': (prog['S2'] + 8) % 24,
            'S3': (prog['S3'] + 8) % 24,
            'T': (prog['T'] + 8) % 24,
        }

        for line in self:
            effective_hours = line.attendance_hours
            if line.attendance_hours > 7.0 and line.attendance_hours < 9.0:
                worked_hours = 8.0
            else:
                worked_hours = line.attendance_hours

            check_in = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(line.check_in))

            hour_from = check_in.hour + check_in.minute / 60.0
            diff = {
                'S1': abs(prog['S1'] - hour_from),
                'S2': abs(prog['S2'] - hour_from),
                'S3': abs(prog['S3'] - hour_from),
                'T': abs(prog['T'] - hour_from),
            }
            shift = min(diff, key=diff.get)
            diff = prog[shift] - hour_from
            if abs(diff) < 1:
                line.shift = shift
                line.hour_from = prog[shift]
                line.hour_to = prog_out[shift]
                if diff < 0:
                    line.late_in = abs(diff)
                    if diff < -5 / 60:
                        worked_hours = worked_hours - max(abs(diff), 1)
                else:
                    line.early_in = diff
                    effective_hours = effective_hours - diff
            else:
                line.hour_from = hour_from

            check_out = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(line.check_out))
            hour_to = check_out.hour + check_out.minute / 60.0

            diff = {
                'S1': abs(prog_out['S1'] - hour_to),
                'S2': abs(prog_out['S2'] - hour_to),
                'S3': abs(prog_out['S3'] - hour_to),
                'T': abs(prog_out['T'] - hour_to),
            }

            shift = min(diff, key=diff.get)
            diff = hour_to - prog_out[shift]
            if line.shift != shift:
                line.shift = False
                line.hour_to = hour_to
            else:
                if abs(diff) < 1:
                    line.hour_to = prog_out[shift]
                    if diff < 0:
                        line.early_out = abs(diff)
                        if diff < -5 / 60:
                            worked_hours = worked_hours - max(abs(diff), 1)
                    else:
                        line.late_out = diff
                        effective_hours = effective_hours - diff
                else:
                    line.hour_to = hour_to

            if worked_hours > effective_hours:
                line.breaks = worked_hours - effective_hours
            line.worked_hours = worked_hours

    @api.multi
    def action_attendance_details(self):
        self.ensure_one()
        # hr_attendance_action
        action = {
            'name': _('Attendance'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self.env.context,
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
