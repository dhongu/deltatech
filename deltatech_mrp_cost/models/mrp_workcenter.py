# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    # costs_hour = fields.Float(string='Cost per hour', help="Specify cost of work center per hour.")
    costs_hour_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        help="Fill this only if you want automatic analytic accounting entries on production orders.",
    )
