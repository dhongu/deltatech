# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details



from odoo import models, fields, api, exceptions, _, SUPERUSER_ID


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"


    shift = fields.Selection([('S1', 'Shift 1'), ('S2', 'Shift 2'), ('S3', 'Shift 3'), ('T', 'Tesa'), ('F', 'Free')])
    hours_per_day = fields.Integer(string="Hours per day", default=8)