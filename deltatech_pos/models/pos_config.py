# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    ecr_type = fields.Selection([('datecs18',"Datecs 2018"),('optima','Optima')], default='datecs18')
    file_prefix = fields.Char(string='File prefix', default='order')
    file_ext = fields.Char(string='File extension', default='inp')