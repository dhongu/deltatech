# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _




class HrAttendanceSummary(models.TransientModel):
    _name = 'hr.attendance.summary'

    formation_id = fields.Many2one('hr.department', string='Department', required=True)

    date_range_id = fields.Many2one('date.range', string='Date range')
    date_from = fields.Date('Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date('End Date', required=True, default=fields.Date.today)

    line_ids = fields.Many2many('hr.attendance.sheet.line', compute='_compute_line_ids')


    @api.multi
    def _compute_line_ids(self):
        for doc in self:
            domain = [('date', '>=', doc.date_from), ('date', '<=', doc.date_to),
                      ('department_id', 'child_of', doc.formation_id.id)]
            doc.line_ids = self.env['hr.attendance.sheet.line'].search(domain)


    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    def do_compute(self):
        employees = self.env['hr.employee'].search([('department_id', 'child_of', self.formation_id.id)])
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to),
                  ('department_id', 'child_of', self.formation_id.id)]
        attendance_lines = self.env['hr.attendance.sheet.line'].search(domain)


    def button_show(self):

        self.ensure_one()
        action = self.env.ref('deltatech_hr_attendance.action_attendance_summary2')
        vals = action.read()[0]
        vals['context'] = {'active_id': self.id, 'active_model': self._name}
        return vals

    def button_print(self):
        return self.print_report()


    @api.multi
    def print_report(self, report_type='qweb-pdf'):
        self.ensure_one()
        report_name = 'deltatech_hr_attendance.report_attendance_summary2'
        context = dict(self.env.context)

        context['active_model'] = self._name
        action = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('model','=',self._name),
             ('report_type', '=', report_type)], limit=1)
        return action.with_context(context).report_action(self)


    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            action =  self.env.ref('deltatech_hr_attendance.action_attendance_summary_control2')
            html = action.render_qweb_html( report.ids)
            result['html'] = html[0]

        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()