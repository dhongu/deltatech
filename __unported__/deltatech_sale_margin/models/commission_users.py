# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, tools, _



class commission_users(models.Model):
    _name = 'commission.users'
    _description = "Users commission"

    user_id = fields.Many2one('res.users', string='Salesperson', required=True)
    name = fields.Char(string='Name', related='user_id.name')
    rate = fields.Float(string="Rate", default=0.01)



