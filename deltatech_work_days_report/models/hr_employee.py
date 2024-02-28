from odoo import fields, models


class HREmployee(models.Model):
    _inherit = "hr.employee"

    hours_per_day = fields.Selection(
        [("4", "4 Hours"), ("6", "6 Hours"), ("8", "8 Hours")], string="Hours per Day", default="8"
    )
