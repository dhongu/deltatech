# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import copy


class HrAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.deltatech_hr_attendance.report_attendance_summary'
    _template = 'deltatech_hr_attendance.report_attendance_summary'
    _inherit = 'report.attendance_summary_xlsx'

    _holiday = {}
    _empty_row = {}
    _days = []



    def _get_header_info(self, start_date, holiday_type):
        st_date = fields.Date.from_string(start_date)
        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(st_date + relativedelta(days=59)),
        }

    def _date_is_day_off(self, date):
        return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)

    def _date_is_global_leave(self, date):
        if not isinstance(date, str):
            date = fields.Date.to_string(date) + ' 12:00:00'
        leaves = self.env['resource.calendar.leaves'].search([
            ('resource_id', '=', False),
            ('date_from', '<=', date),
            ('date_to', '>=', date)
        ])
        return leaves and True or False

    def _get_day(self, start_date, end_date):

        res = []
        dayofweek = [ _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        days = (end_date - start_date).days + 1
        for x in range(0, max(2, days)):
            global_leave = self._date_is_global_leave(start_date)
            is_day_off = self._date_is_day_off(start_date)
            if is_day_off or global_leave:
                color = '#f2f2f2'
            elif global_leave:
                color = '#f2f2f2'
            else:
                color = ''
            # todo: de adus string in functie de setarile locale
            res.append({
                'day_str': dayofweek[start_date.weekday()],
                'day': start_date.day,
                'color': color,
                'global_leave': global_leave,
                'is_day_off':is_day_off
            })
            start_date = start_date + relativedelta(days=1)
        self._days = res
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

    def get_holidays_status(self):
        res = {}
        res['holiday'] = {}
        for holiday in self.env['hr.holidays.status'].search([]):
            res['holiday'][holiday.cod] = 0
            if holiday.global_leave:
                res['holiday_global_leave'] = holiday
        return res

    def get_empty_row(self, start_date, end_date):
        res = {
            'days': [],
            'worked_hours': 0.0,
            'overtime': 0.0,
            'night_hours': 0.0,
            'rows': 3,
            'work_day': 0
        }

        days = (end_date - start_date).days + 1

        for index in range(0, max(2, days)):
            current = start_date + timedelta(index)
            res['days'].append({
                'day': current.day,
                'color': '',
                'line': False,
                'text': '',
                'date': fields.Date.to_string(current),
                'holiday_id': False,
                'holiday': False,
            })
            if self._date_is_day_off(current):
                res['days'][index]['color'] = '#f2f2f2'
            else:
                res['work_day'] += 1

        return res

    def _get_attendance_summary(self, start_date, end_date, lines, empid):

        if not self._days:
            self._get_day(start_date, end_date)

        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        days = (end_date - start_date).days + 1

        # work_day = 0
        to_retrieve = 0


        # count and get leave summary details.

        if not self._empty_row or not self._holiday:
            self._empty_row = self.get_empty_row(start_date, end_date)
            self._holiday = self.get_holidays_status()

            holiday_global_leave = self._holiday['holiday_global_leave']
            if holiday_global_leave:
                for index in range(0, max(2, days)):
                    current = start_date + timedelta(index)
                    #if self._date_is_global_leave(current) and not self._date_is_day_off(current):
                    if self._days[index]['global_leave'] and not self._days[index]['is_day_off']:
                        self._empty_row['days'][index]['color'] = holiday_global_leave.color_name
                        self._empty_row['days'][index]['text'] = holiday_global_leave.cod
                        self._empty_row['days'][index]['holiday'] = True
                        self._empty_row['work_day'] -= 1
                        self._holiday['holiday'][holiday_global_leave.cod] += 1

        res = copy.deepcopy(self._empty_row)
        res['holiday'] = copy.deepcopy(self._holiday['holiday'])

        holiday_global_leave = self._holiday['holiday_global_leave']


        holiday_type = ['confirm', 'validate']
        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', empid), ('state', 'in', holiday_type),
            ('type', '=', 'remove'), ('date_from', '<=', str(end_date)),
            ('date_to', '>=', str(start_date))
        ])

        holiday_to_retrieve = []
        for holiday in holidays.sorted(lambda x: x.holiday_status_id.sequence):
            # Convert date to user timezone, otherwise the report will not be consistent with the
            # value displayed in the interface.
            date_from = fields.Datetime.from_string(holiday.date_from)
            date_from = fields.Datetime.context_timestamp(holiday, date_from).date()
            date_to = fields.Datetime.from_string(holiday.date_to)
            date_to = fields.Datetime.context_timestamp(holiday, date_to).date()
            for index in range(0, ((date_to - date_from).days + 1)):
                index_d = (date_from - start_date).days
                # res['days'][(date_from - start_date).days]['text'] = ''
                if date_from >= start_date and date_from <= end_date:
                    if not self._date_is_day_off(date_from) and not res['days'][index_d]['holiday']:
                        res['days'][index_d]['color'] = holiday.holiday_status_id.color_name
                        res['days'][index_d]['text'] = holiday.holiday_status_id.cod
                        res['work_day'] -= 1
                        res['holiday'][holiday.holiday_status_id.cod] += 1
                        res['days'][index_d]['holiday_id'] = holiday.id
                        res['days'][index_d]['holiday'] = True
                        if holiday.holiday_status_id.retrieve:
                            to_retrieve += 1
                            holiday_to_retrieve += [holiday.holiday_status_id.cod]

                date_from += timedelta(1)

        working_day = 0
        for line in lines.filtered(lambda l: l.employee_id.id == empid):
            index_date = fields.Date.from_string(line.date)
            index = (index_date - start_date).days
            res['days'][index]['line'] = line

            # res['days'][index]['text'] = line.total_hours
            if line.worked_hours >= 1:
                res['worked_hours'] += round(line.worked_hours)

            res['overtime'] += round(line.overtime_granted)
            res['night_hours'] += round(line.night_hours)
            if not res['days'][index]['holiday'] and line.worked_hours >= 5 and not self._date_is_day_off(index_date):
                working_day += 1
                if line.working_day != 1.0:
                    line.write({'working_day': 1.0})
            else:
                if line.working_day != 0.0:
                    line.write({'working_day': 0.0})

        retrieved = res['overtime'] * 8
        res['norma'] = (to_retrieve + working_day) * 8
        res['work_day'] = working_day
        if res['worked_hours'] < res['norma']:
            dif = res['norma'] - res['worked_hours']
            if dif < res['overtime']:
                res['worked_hours'] = res['norma']
                res['overtime'] = res['overtime'] - dif
            else:
                res['worked_hours'] = res['worked_hours'] + res['overtime']
                res['overtime'] = 0
        if res['worked_hours'] > res['norma']:
            dif = res['worked_hours'] - res['norma']
            res['worked_hours'] = res['norma']
            res['overtime'] = res['overtime'] + dif

        retrieved = retrieved - res['overtime'] * 8

        # res['work_day'] = res['worked_hours'] / 8   # nu se mai calculeaza ca numarul de zile

        if not res['overtime']:
            res['rows'] -= 1
        if not res['night_hours']:
            res['rows'] -= 1

        return res

    def _get_data_from_report(self, report):
        res = []
        lines = report.line_ids
        employees = self.env['hr.employee'].search([('department_id', 'child_of', report.formation_id.id)])
        # mai sunt si angazati inactivi care totusi apar in pontaj si care trebuie afisati in raport
        for line in report.line_ids:
            employees |= line.employee_id

        for emp in employees.sorted(key=lambda r: r.name):
            res.append({
                'emp': emp,
                'display': self._get_attendance_summary(report.date_from, report.date_to, lines, emp.id),
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
        #active_model = self.env.context.get('model', attendance_report.model)
        attendances = self.env[attendance_report.model].browse(docids)
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



    def _get_report_name(self):
        return _('Attendance Summary')

    def _get_report_filters(self, report):
        return [
            [_('Date from'), report.date_from],
            [_('Date to'), report.date_to],
        ]

    def _get_report_columns(self, report):
        columns = {
            0: {'header': _('Marca'),
                'field': '["emp"].barcode',
                'width': 5},
            1: {'header': _('Employees'),
                'field': '["emp"].name',
                'width': 10},
            2: {'header': _('Type'),
                'width': 7},
        }
        days = self._get_day(report.date_from, report.date_to)
        col = 3
        for day in days:
            columns[col] = {
                'header': ('%s %s') % (day['day'], day['day_str']),
                'width': 7
            }
            col += 1
        columns[col] = {'header': _('Sum'),
                        'width': 7}
        col += 1
        columns[col] = {'header': _('Norm'),
                        'width': 7}
        col += 1
        columns[col] = {'header': _('Wd'),
                        'width': 7}
        col += 1
        for holiday in self._get_holidays_status():
            columns[col] = {
                'header': holiday['cod'],
                'width': 5
            }
            col += 1
        return columns

    def _generate_report_content(self, workbook, report):

        self.write_array_header(workbook)
        for obj in self._get_data_from_report(report):
            self.sheet.write_string(self.row_pos, 0, obj['emp'].barcode or '', workbook.add_format({}))
            self.sheet.write_string(self.row_pos, 1, obj['emp'].name or '', workbook.add_format({}))
            self.sheet.write_string(self.row_pos, 2, 'normal' or '', workbook.add_format({}))
            col_pos = 3
            for details in obj['display']['days']:
                line = details['line']
                if line:
                    if int(line.total_hours) >= 1:
                        self.sheet.write_number(self.row_pos, col_pos, int(line.total_hours), workbook.add_format({}))
                    if details['text']:
                        if int(line.total_hours) >= 1:
                            text = "%s  / %s" % (int(line.total_hours), details['text'])
                        else:
                            text = details['text']

                        self.sheet.write_string(self.row_pos, col_pos, text, workbook.add_format({}))
                else:
                    if details['text']:
                        text = details['text']
                        self.sheet.write_string(self.row_pos, col_pos, text, workbook.add_format({}))
                col_pos += 1
            self.sheet.write_number(self.row_pos, col_pos, int(obj['display']['worked_hours']), workbook.add_format({}))
            col_pos += 1
            self.sheet.write_number(self.row_pos, col_pos, int(obj['display']['norma']), workbook.add_format({}))
            col_pos += 1
            self.sheet.write_number(self.row_pos, col_pos, int(obj['display']['work_day']), workbook.add_format({}))
            col_pos += 1
            for holiday in self._get_holidays_status():

                nr = obj['display']['holiday'][holiday['cod']]
                if nr:
                    self.sheet.write_number(self.row_pos, col_pos, nr, workbook.add_format({}))
                col_pos += 1

            self.row_pos += 1

    def write_line(self, workbook, line_object, formats):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.items():
            value = getattr(line_object, column['field'])
            cell_type = column.get('type', 'string')
            if cell_type == 'string':
                self.sheet.write_string(self.row_pos, col_pos, value or '', workbook.add_format(formats))
            elif cell_type == 'amount':
                self.sheet.write_number(
                    self.row_pos, col_pos, float(value),
                    workbook.add_format(formats)
                )
        self.row_pos += 1


class HrAttendanceSummaryControl(HrAttendanceSummaryReport):
    _name = 'report.deltatech_hr_attendance.control_attendance_summary'
    _template = 'deltatech_hr_attendance.control_attendance_summary'


class HrAttendanceSummaryControl2(HrAttendanceSummaryReport):
    _name = 'report.deltatech_hr_attendance.control_attendance_summary2'
    _template = 'deltatech_hr_attendance.control_attendance_summary2'

class HrAttendanceSummaryReport2(HrAttendanceSummaryReport):
    _name = 'report.deltatech_hr_attendance.report_attendance_summary2'
    _template = 'deltatech_hr_attendance.report_attendance_summary2'