# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment


class commission_users(models.Model):
    _name = 'commission.users'
    _description = "Users commission"

    user_id = fields.Many2one('res.users', string='Salesperson', required=True)
    name = fields.Char(string='Name', related='user_id.name')
    rate = fields.Float(string="Rate", default=0.01)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
