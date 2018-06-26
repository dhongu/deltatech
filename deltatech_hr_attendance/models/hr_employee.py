# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details



from odoo import models, fields, api, exceptions, _, SUPERUSER_ID


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    type_contract = fields.Selection([('acord', 'Acord'), ('regie', 'Regie')], default='')
