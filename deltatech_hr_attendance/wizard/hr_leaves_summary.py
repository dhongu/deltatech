# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class LeavesSummary(models.TransientModel):
    _name = 'hr.leaves.summary'

    department_id = fields.Many2one('hr.department', string='Department', required=True)

    date_range_id = fields.Many2one('date.range', string='Date range')
    date_from = fields.Date('Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date('End Date', required=True, default=fields.Date.today)

    leave_id = fields.Many2one('hr.holidays.status', string='Leave')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    def do_compute(self):

        lines = self.env['hr.leaves.summary.line'].search([('report_id', '=', self.id)])
        lines.unlink()
        employees = self.env['hr.employee'].search([('department_id', 'child_of', self.department_id.id)])
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to),
                  ('department_id', 'child_of', self.department_id.id)]
        attendance_lines = self.env['hr.attendance.sheet.line'].search(domain)
        lines = {}
        for attendance_line in attendance_lines:
            employees |= attendance_line.employee_id


        if not self.leave_id:
            leaves = self.env['hr.holidays.status'].search([])
        else:
            leaves = self.leave_id


        for employee in employees:
            lines[employee] = {}

            for leave in leaves:
                lines[employee][leave.id] = {
                    'report_id': self.id,
                    'employee_id': employee.id,
                    'leave_id':leave.id,
                    'days':0.0
                }

            res = self.env['report.deltatech_hr_attendance.report_attendance_summary']._get_attendance_summary(
                start_date = self.date_from,
                end_date = self.date_to,
                lines = attendance_lines.filtered(lambda l: l.employee_id.id == employee.id),
                empid = employee.id
            )
            for leave in leaves:
                lines[employee][leave.id]['days'] = res['holiday'][leave.cod]


        for employee in employees:
            for leave in leaves:
                if lines[employee][leave.id]['days']:
                    line = self.env['hr.leaves.summary.line'].create(lines[employee][leave.id])




    def button_show(self):
        self.do_compute()
        action = self.env.ref('deltatech_hr_attendance.action_leaves_summary_line').read()[0]
        action['domain'] = [('report_id', '=', self.id)]
        action['context'] = {
            'active_id': self.id,
        }
        return action

    def button_print(self):
        self.do_compute()
        records = self
        report_name = 'deltatech_hr_attendance.action_leaves_summary_report'
        report = self.env.ref(report_name).report_action(records)
        return report



class LeavesSummaryLine(models.TransientModel):
    _name = 'hr.leaves.summary.line'


    report_id = fields.Many2one('hr.leaves.summary')

    employee_id = fields.Many2one('hr.employee', string='Employee', index=True)
    marca = fields.Char(string='Marca', related='employee_id.barcode')
    identification_id = fields.Char(string='Identification No', related='employee_id.identification_id')

    leave_id = fields.Many2one('hr.holidays.status', string='Leave', required=True)
    days = fields.Integer(string='Days')


