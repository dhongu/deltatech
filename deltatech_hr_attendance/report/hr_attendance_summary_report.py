# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.deltatech_hr_attendance.report_attendance_summary'

    def _get_header_info(self, start_date, holiday_type):
        st_date = fields.Date.from_string(start_date)
        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(st_date + relativedelta(days=59)),
        }
    
    def _date_is_day_off(self, date):
        return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)

    def _get_day(self, start_date, end_date):
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        days = (end_date - start_date).days
        for x in range(0, max(7,days)):
            color = '#ababab' if self._date_is_day_off(start_date) else ''
            res.append({'day_str': start_date.strftime('%a'), 'day': start_date.day , 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_months(self, start_date, end_date):
        # it works for geting month name between two dates.
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res

    def _get_attendance_summary(self, start_date, end_date, lines, empid):
        res = []
        count = 0
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        days = (end_date - start_date).days

        for index in range(0, max(7, days)):
            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': '', 'line':False})
            if self._date_is_day_off(current) :
                res[index]['color'] = '#ababab'
        # count and get leave summary details.

        for line in lines.filtered( lambda l: l.employee_id.id == empid):
            index_date = fields.Date.from_string(line.date)
            index = (index_date - start_date).days
            res[index]['line'] = line
            count += 1

        return res

    def _get_data_from_report(self, start_date, end_date, lines):
        res = []

        employees = self.env['hr.employee']
        for line in lines:
            employees |= line.employee_id



        for emp in employees.sorted(key=lambda r: r.name):
            res.append({
                'emp': emp.name,
                'display': self._get_attendance_summary( start_date, end_date, lines, emp.id),
                'sum': 0.0
            })
        return res

    def _float_time(self,val):
        return '%02d:%02d' % (int(str(val).split('.')[0]), int(float(str('%.2f' % val).split('.')[1])/100*60))

    def _get_holidays_status(self):
        res = []
        for holiday in self.env['hr.holidays.status'].search([]):
            res.append({'color': holiday.color_name, 'name': holiday.name})
        return res

    @api.model
    def get_report_values(self, docids, data=None):


        attendance_report = self.env['ir.actions.report']._get_report_from_name('deltatech_hr_attendance.report_attendance_summary')
        attendances = self.env['hr.attendance.sheet'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': attendance_report.model,
            'docs': attendances,

            'get_day': self._get_day,
            'get_months': self._get_months,
            'float_time': self._float_time,
            'get_data_from_report': self._get_data_from_report,
            'get_holidays_status': self._get_holidays_status(),
        }


