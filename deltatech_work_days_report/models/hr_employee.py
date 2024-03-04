from odoo import fields, models


class HREmployee(models.Model):
    _inherit = "hr.employee"

    hours_per_day = fields.Selection(
        [("2", "2 Hours"), ("4", "4 Hours"), ("6", "6 Hours"), ("8", "8 Hours")], string="Hours per Day", default="8"
    )


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    type_code = fields.Char(string="Code", default="L")
