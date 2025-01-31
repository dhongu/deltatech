from odoo import fields, models


class OperatingUnit(models.Model):
    _name = "deltatech.operating.unit"
    _description = "Operating Unit"

    name = fields.Char(string="Name", required=True)
    groups_ids = fields.Many2many("res.groups", string="Groups")
