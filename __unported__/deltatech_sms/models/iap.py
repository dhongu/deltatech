# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models



class IapAccount(models.Model):
    _inherit = 'iap.account'


    user_name = fields.Char()
    password = fields.Char()