# ©  Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Location(models.Model):
    _inherit = "stock.location"

    analytic_id = fields.Many2one("account.analytic.account", string="Analytic account")
