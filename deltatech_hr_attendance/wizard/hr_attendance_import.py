# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details

import base64
from io import StringIO
import os

from odoo import models, fields, api, _, registry
from odoo.exceptions import Warning, RedirectWarning, ValidationError, UserError
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
import csv
import sys
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import threading
import logging
_logger = logging.getLogger(__name__)





class hr_attendance_import(models.TransientModel):
    _name = 'hr.attendance.import'
    _description = "HR Attendance Import"

    employees = {}

    background = fields.Boolean('Run in background', default=False)

    state = fields.Selection([('choose', 'choose'),
                              ('result', 'result')], default='choose')  # get the file

    attendance_file = fields.Binary(string='Attendance File')
    attendance_file_name = fields.Char(string='Attendance File Name')

    def add_attendance(self, event_time, barcode, direction):
        employee_data = self.employees.get(barcode, False)

        if not employee_data:
            employee = self.env['hr.employee'].search([('barcode', '=', barcode)])
            if not employee:
                employee = self.env['hr.employee'].with_context(active_test=False).search([('barcode', '=', barcode)])
                if not employee:
                    return
            last_attendance = False
        else:
            employee = employee_data['employee']
            last_attendance = employee_data['last_attendance']

        tz_name = self._context.get('tz') or self.env.user.tz or "Europe/Bucharest"
        local = pytz.timezone(tz_name)
        local_dt = local.localize(fields.Datetime.from_string(event_time), is_dst=None)
        event_time = fields.Datetime.to_string(local_dt.astimezone(pytz.utc))

        attendance = self.env['hr.attendance']
        values = {
            'employee_id': employee.id,
            'check_in': event_time
        }

        is_ok = True


        if not last_attendance:
            last_attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '<=', event_time),
            ], order='check_in desc', limit=1)


            attendance_future = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>', event_time),
             ], limit=1)
            if attendance_future:
                return False

        if direction == 'sign_in' and  last_attendance :
            if  last_attendance.check_out and last_attendance.check_out > event_time:
                is_ok = False


        if direction == 'sign_in':
            if last_attendance:
                if last_attendance.check_in == event_time:
                    is_ok = False
                else:
                    if not last_attendance.check_out:
                        event_time_out = fields.Datetime.from_string(last_attendance.check_in)
                        event_time_out = event_time_out + relativedelta(seconds=1)
                        event_time_out = fields.Datetime.to_string(event_time_out)
                        try:
                            last_attendance.write({'check_out': event_time_out, 'state': 'no_out'})
                        except ValidationError as e:
                            _logger.info('Corectie:', str(e), 'event_time', event_time)


        else:
            if not last_attendance or last_attendance.check_in > event_time:
                is_ok = False

            if last_attendance and is_ok:
                check_in = fields.Datetime.from_string(last_attendance.check_in)
                check_out = fields.Datetime.from_string(event_time)
                t_diff = relativedelta(check_out, check_in)
                worked_hours = t_diff.days * 24 + t_diff.hours + t_diff.minutes / 60 + t_diff.seconds / 60 / 60
                if worked_hours > 24:
                    _logger.info('Work > 24 h')
                    event_time_out = check_in + relativedelta(seconds=1)
                    event_time_out = fields.Datetime.to_string(event_time_out)
                    last_attendance.write({'check_out': event_time_out, 'state': 'no_out'})
                    event_time_in = check_out + relativedelta(seconds=-1)
                    event_time_in = fields.Datetime.to_string(event_time_in)
                    values = {
                        'check_in': event_time_in,
                        'check_out': event_time,
                        'state': 'no_in',
                    }
        if is_ok:
            if direction == 'sign_in':
                try:
                    last_attendance = self.env['hr.attendance'].create(values)
                except ValidationError as e:
                    last_attendance = False
                    _logger.info('Error In', str(e), values)

            else:
                try:
                    last_attendance.write({'check_out': event_time})
                    if self.background:
                        self._cr.commit()
                except ValidationError as e:
                    last_attendance = False
                    _logger.info('Error out', str(e),)

            self.employees[barcode] = {'employee': employee,
                                  'last_attendance': last_attendance}
        return last_attendance

    @api.multi
    def do_import(self):
        self.employees = {}
        if self.background:
            threaded_import = threading.Thread(target=self._do_import_background, args=())
            threaded_import.start()
            return {'type': 'ir.actions.act_window_close'}
        else:
            return self._do_import()

    @api.multi
    def _do_import_background(self):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            job = self.with_env(self.env(cr=new_cr))
            job._do_import()
            new_cr.commit()
            new_cr.close()

    @api.multi
    def _do_import(self):
        attendance_file = base64.decodestring(self.attendance_file)
        buff = StringIO(attendance_file)

        reader = csv.DictReader(buff, quoting=csv.QUOTE_NONE, delimiter=',')
        attendances = self.env['hr.attendance']
        sortedlist = sorted(reader, key=lambda row: row['Event Time'])
        for row in sortedlist:
            if row['Direction'] == 'Enter':
                direction = 'sign_in'
            elif row['Direction'] == 'Exit':
                direction = 'sign_out'
            else:
                direction = 'action'
            attendance = self.add_attendance(event_time=row['Event Time'], barcode=row['Card No.'], direction=direction)
            if attendance:
                attendances |= attendance

        return {
            'domain': "[('id','in', [" + ','.join(map(str, attendances.ids)) + "])]",
            'name': _('Imported Attendances'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.attendance',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
