# ©  2017 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models, tools
from odoo.api import Environment
from odoo.exceptions import RedirectWarning, Warning, except_orm

import odoo.addons.decimal_precision as dp


class commission_users(models.Model):
    _name = "commission.users"
    _description = "Users commission"

    user_id = fields.Many2one("res.users", string="Salesperson", required=True)
    name = fields.Char(string="Name", related="user_id.name")
    rate = fields.Float(string="Rate", default=0.01)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
