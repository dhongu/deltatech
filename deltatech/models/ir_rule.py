# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class IrRule(models.Model):
    _inherit = "ir.rule"

    model_name = fields.Char(string="Model Name", related="model_id.model", readonly=True)
