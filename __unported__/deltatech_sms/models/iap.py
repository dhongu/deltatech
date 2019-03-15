# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models



class IapAccount(models.Model):
    _inherit = 'iap.account'


    user_name = fields.Char()
    password = fields.Char()