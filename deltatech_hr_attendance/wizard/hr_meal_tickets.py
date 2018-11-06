# coding=utf-8
# -*- coding: utf-8 -*-
# ©  2008-2018 Fekete Mihai <mihai.fekete@forbiom.eu>
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class MealTicketReport(models.TransientModel):
    _name = 'hr.meal.ticket'

    department_id = fields.Many2one('hr.department', string='Department', required=True)

    date_range_id = fields.Many2one('date.range', string='Date range')
    date_from = fields.Date('Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date('End Date', required=True, default=fields.Date.today)

    price = fields.Float()

    two_fields_employee = fields.Boolean(default=True)
    hours_details = fields.Boolean()

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    def do_compute(self):

        lines = self.env['hr.meal.ticket.line'].search([('report_id', '=', self.id)])
        lines.unlink()
        employees = self.env['hr.employee'].search([('department_id', 'child_of', self.department_id.id)])
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to),
                  ('department_id', 'child_of', self.department_id.id)]
        attendance_lines = self.env['hr.attendance.sheet.line'].search(domain)
        lines = {}
        for attendance_line in attendance_lines:
            employees |= attendance_line.employee_id

        for employee in employees:
            lines[employee] = {
                'report_id': self.id,
                'employee_id': employee.id,
                'tickets': 0.0,
                'worked_hours': 0.0,
                'overtime': 0.0,
            }

        for attendance_line in attendance_lines:
            lines[attendance_line.employee_id]['tickets'] += attendance_line.working_day
            lines[attendance_line.employee_id]['worked_hours'] += attendance_line.worked_hours
            lines[attendance_line.employee_id]['overtime'] += attendance_line.overtime_granted

        for employee in employees:
            lines[employee]['price'] = self.price


            tickets = (lines[employee]['worked_hours'] + lines[employee]['overtime']) / 8
            diff = lines[employee]['tickets'] - tickets
            if 0.5 < diff < 0.99:
                lines[employee]['tickets'] = round(tickets)

            lines[employee]['amount'] = self.price * lines[employee]['tickets']
            line = self.env['hr.meal.ticket.line'].create(lines[employee])
            line._compute_first_last_name()



    def button_show(self):
        self.do_compute()
        action = self.env.ref('deltatech_hr_attendance.action_meal_ticket_line').read()[0]
        action['domain'] = [('report_id', '=', self.id)]
        action['context'] = {
            'active_id': self.id,
            'hours_details': self.hours_details,
            'two_fields_employee': self.two_fields_employee
        }
        return action

    def button_print(self):
        self.do_compute()
        records = self
        report_name = 'deltatech_hr_attendance.action_meal_ticket_report'
        report = self.env.ref(report_name).report_action(records)
        return report


class MealTicketReportLine(models.TransientModel):
    _name = 'hr.meal.ticket.line'

    report_id = fields.Many2one('hr.meal.ticket')

    employee_id = fields.Many2one('hr.employee', string='Employee', index=True)

    first_name = fields.Char(_compute='_compute_first_last_name')
    last_name = fields.Char(_compute='_compute_first_last_name')
    identification_id = fields.Char(string='Identification No', related='employee_id.identification_id')

    worked_hours = fields.Float(string='Worked Hours')
    overtime = fields.Float(string='Overtime')

    tickets = fields.Integer(default=1, string="Tickets")
    price = fields.Float()
    amount = fields.Float()

    @api.multi
    @api.depends('employee_id')
    def _compute_first_last_name(self):
        for line in self:
            first_name = line.employee_id.name
            last_name = ''
            if ' ' in line.employee_id.name:
                first_name, last_name = line.employee_id.name.split(' ', 1)
            line.first_name = first_name
            line.last_name = last_name
