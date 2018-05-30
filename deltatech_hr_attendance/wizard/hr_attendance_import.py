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
        attendances = self.env['hr.attendance']
        sortedlist = sorted(reader, key=lambda row: row['Event Time'])
        for row in sortedlist:
            print row
            barcode = row['Card No.']
            employee = self.env['hr.employee'].search([('barcode','=',barcode)])
            if not employee:
                barcode = barcode.replace("'",'')
                employee = self.env['hr.employee'].search([('barcode', '=', barcode)])
                if not employee:
                    continue
            attendance = self.env['hr.attendance'].search([('employee_id','=',employee.id),('name','=',row['Event Time'])])


            if attendance:
                continue


            #attendance = self.env['hr.attendance'].search(  [('employee_id', '=', employee.id), ('name', '<', row['Event Time'])], limit=1, order='name DESC')
            attendance = self.env['hr.attendance']
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

            is_ok = True

            prev_atts = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('name', '<', values['name']),
                                        ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name DESC')
            next_atts = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('name', '>', values['name']),
                                        ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name ASC')

            # check for alternance, return False if at least one condition is not satisfied
            if prev_atts and prev_atts[0].action == values['action']:  # previous exists and is same action
                is_ok = False
            if next_atts and next_atts[0].action == values['action']:  # next exists and is same action
                is_ok = False
            if (not prev_atts) and ( not next_atts) and  values['action'] != 'sign_in':  # first attendance must be sign_in
                is_ok = False


            if is_ok:
                attendances |= self.env['hr.attendance'].create(values)


        return {
            'domain': "[('id','in', [" + ','.join(map(str, attendances.ids)) + "])]",
            'name': _('Imported Attendances'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.attendance',
            'view_id': False,
            'type': 'ir.actions.act_window',

        }





