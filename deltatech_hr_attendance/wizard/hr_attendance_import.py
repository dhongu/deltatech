# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details

import base64
import zipfile
import StringIO
import os

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp

import csv
import sys
import pytz, datetime


"""
Index,Event Type,Card Holder,Card Type,Card No.,Event Time,Direction,Event Source,MAC Address,Card Swiping Type,Card Reader Type,Remark
1,Fingerprint/Finger Vein Authentication Passed,Cristi,,'0000000001,2018-05-23 16:12:29,Exit,HiK:Usa2 - Iesire,,,,
2,Fingerprint/Finger Vein Authentication Passed,Cristi,,'0000000001,2018-05-23 16:12:26,Enter,HiK:Usa2 - Intrare,,,,
3,Fingerprint/Finger Vein Authentication Passed,Cristi,,'0000000001,2018-05-23 16:12:23,Exit,HiK:Usa1 - Iesire,,,,
4,Fingerprint/Finger Vein Authentication Passed,Cristi,,'0000000001,2018-05-23 16:12:20,Enter,HiK:Usa1 - Intrare,,,,

"""


class hr_attendance_import(models.TransientModel):
    _name = 'hr.attendance.import'
    _description = "HR Attendance Import"

    state = fields.Selection([('choose', 'choose'),
                              ('result', 'result')], default='choose')  # get the file

    attendance_file = fields.Binary(string='Attendance File')
    attendance_file_name = fields.Char(string='Attendance File Name')

    def add_attendance(self, event_time, barcode, direction ):
        employee = self.env['hr.employee'].search([('barcode', '=', barcode)])
        if not employee:
            barcode = barcode.replace("'", '')
            employee = self.env['hr.employee'].search([('barcode', '=', barcode)])
            if not employee:
                return
        attendance = self.env['hr.attendance'].search(
            [('employee_id', '=', employee.id), ('name', '=', event_time)])

        if attendance:
            return

        tz_name = self._context.get('tz') or self.env.user.tz or  "Europe/Bucharest"
        local = pytz.timezone(tz_name)
        local_dt = local.localize(fields.Datetime.from_string(event_time), is_dst=None)
        event_time = fields.Datetime.to_string( local_dt.astimezone(pytz.utc) )


        attendance = self.env['hr.attendance']
        values = {
            'name': event_time,
            'employee_id': employee.id,
            'action':direction
        }


        is_ok = True

        prev_atts = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('name', '<', event_time),
                                                      ('action', 'in', ('sign_in', 'sign_out'))], limit=1,
                                                     order='name DESC')
        next_atts = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('name', '>', event_time),
                                                      ('action', 'in', ('sign_in', 'sign_out'))], limit=1,
                                                     order='name ASC')

        # check for alternance, return False if at least one condition is not satisfied
        if prev_atts and prev_atts[0].action == values['action']:  # previous exists and is same action
            is_ok = False
        if next_atts and next_atts[0].action == values['action']:  # next exists and is same action
            is_ok = False
        if (not prev_atts) and (not next_atts) and values['action'] != 'sign_in':  # first attendance must be sign_in
            is_ok = False

        if is_ok:
            return self.env['hr.attendance'].create(values)

        return False

    @api.multi
    def do_import(self):
        attendance_file = base64.decodestring(self.attendance_file)
        buff = StringIO.StringIO(attendance_file)

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
            attendance = self.add_attendance(event_time=row['Event Time'], barcode=row['Card No.'],  direction = direction )
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





