# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    team_id = fields.Many2one("crm.team", string="Sales Team")
