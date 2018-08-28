# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.deltatech_hr_attendance.report_attendance_summary'
    _template = 'deltatech_hr_attendance.report_attendance_summary'

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
        days = (end_date - start_date).days + 1
        for x in range(0, max(7, days)):
            color = '#f2f2f2' if self._date_is_day_off(start_date) else ''
            res.append({'day_str': start_date.strftime('%a'), 'day': start_date.day, 'color': color})
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
        res = {
            'days': [],
            'worked_hours': 0.0,
            'overtime': 0.0,
            'night_hours': 0.0,
            'rows': 3,
        }
        count = 0
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        days = (end_date - start_date).days + 1

        work_day = 0
        for index in range(0, max(7, days)):
            current = start_date + timedelta(index)
            res['days'].append({'day': current.day, 'color': '', 'line': False, 'text': '','date':fields.Date.to_string( current)})
            if self._date_is_day_off(current):
                res['days'][index]['color'] = '#f2f2f2'
            else:
                work_day += 1
        # count and get leave summary details.

        holiday_type = ['confirm', 'validate']
        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', empid), ('state', 'in', holiday_type),
            ('type', '=', 'remove'), ('date_from', '<=', str(end_date)),
            ('date_to', '>=', str(start_date))
        ])
        res['holiday'] = {}
        for holiday in self.env['hr.holidays.status'].search([]):
            res['holiday'][holiday.cod] = 0

        for holiday in holidays:
            # Convert date to user timezone, otherwise the report will not be consistent with the
            # value displayed in the interface.
            date_from = fields.Datetime.from_string(holiday.date_from)
            date_from = fields.Datetime.context_timestamp(holiday, date_from).date()
            date_to = fields.Datetime.from_string(holiday.date_to)
            date_to = fields.Datetime.context_timestamp(holiday, date_to).date()
            for index in range(0, ((date_to - date_from).days + 1)):
                #res['days'][(date_from - start_date).days]['text'] = ''
                if date_from >= start_date and date_from <= end_date:
                    if not self._date_is_day_off(date_from):
                        res['days'][(date_from - start_date).days]['color'] = holiday.holiday_status_id.color_name
                        res['days'][(date_from - start_date).days]['text'] = holiday.holiday_status_id.cod
                        work_day -= 1
                        res['holiday'][holiday.holiday_status_id.cod] += 1
                date_from += timedelta(1)

            count += abs(holiday.number_of_days)

        for line in lines.filtered(lambda l: l.employee_id.id == empid):
            index_date = fields.Date.from_string(line.date)
            index = (index_date - start_date).days
            res['days'][index]['line'] = line

            #res['days'][index]['text'] = line.total_hours
            res['worked_hours'] += round(line.worked_hours)
            res['overtime'] += round(line.overtime_granted)
            res['night_hours'] += round(line.night_hours)

        res['norma'] = work_day * 8
        if res['worked_hours'] < res['norma']:
            dif = res['norma'] - res['worked_hours']
            if dif < res['overtime']:
                res['worked_hours'] = res['norma']
                res['overtime'] = res['overtime'] - dif
            else:
                res['worked_hours'] = res['worked_hours'] + res['overtime']
                res['overtime'] = 0
        if res['worked_hours'] > res['norma']:
            dif =  res['worked_hours'] - res['norma']
            res['worked_hours'] = res['norma']
            res['overtime'] = res['overtime'] + dif

        if not res['overtime']:
            res['rows'] -= 1
        if not res['night_hours']:
            res['rows'] -= 1

        return res

    def _get_data_from_report(self, start_date, end_date, lines):
        res = []

        employees = self.env['hr.employee']
        for line in lines:
            employees |= line.employee_id

        for emp in employees.sorted(key=lambda r: r.name):
            res.append({
                'emp': emp,
                'display': self._get_attendance_summary(start_date, end_date, lines, emp.id),
                'sum': 0.0
            })
        return res

    def _float_time(self, val):
        if val == 8.0:
            res = '8'
        else:
            res = '%2d:%02d' % (int(str(val).split('.')[0]), int(float(str('%.2f' % val).split('.')[1]) / 100 * 60))
        return res

    def _get_holidays_status(self):
        res = []
        for holiday in self.env['hr.holidays.status'].search([]):
            res.append({'color': holiday.color_name,
                        'name': holiday.name,
                        'cod': holiday.cod})
        return res

    @api.model
    def get_report_values(self, docids, data=None):

        attendance_report = self.env['ir.actions.report']._get_report_from_name(self._template)
        attendances = self.env['hr.attendance.sheet'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': attendance_report.model,
            'docs': attendances,
            'doc': attendances,
            'get_day': self._get_day,
            'get_months': self._get_months,
            'float_time': self._float_time,
            'get_data_from_report': self._get_data_from_report,
            'get_holidays_status': self._get_holidays_status,

        }


class HrAttendanceSummaryControl(HrAttendanceSummaryReport):
    _name = 'report.deltatech_hr_attendance.control_attendance_summary'
    _template = 'deltatech_hr_attendance.control_attendance_summary'
