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

    @api.multi
    def do_import(self):
        attendance_file = base64.decodestring(self.attendance_file)
        buff = StringIO.StringIO(attendance_file)

        reader = csv.DictReader(buff, quoting=csv.QUOTE_NONE, delimiter=',')
        for row in reader:
            print row
            employee = self.env['hr.employee'].search([('barcode','=',row['Card No.'])])
            if not employee:
                continue
            attendance = self.env['hr.attendance'].search([('employee_id','=',employee.id),('name','=',row['Event Time'])])
            if attendance:
                continue
            values = {
                'name':row['Event Time'],
              #  'action_desc':row['Event Source'],
                'employee_id':employee.id,
            }
            if row['Direction'] == 'Enter':
                values['action'] = 'sign_in'
            elif row['Direction'] == 'Exit':
                values['action'] = 'sign_out'
            else:
                values['action'] = 'action'
            self.env['hr.attendance'].create(values)




