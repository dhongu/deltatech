from odoo import fields, models


class BOM(models.Model):
    _inherit = "mrp.bom"

    overhead_amount = fields.Float(string="Overhead", default="0.0")
    duration = fields.Float(string="Duration")
    utility_consumption = fields.Float(string="Utility consumption", help="Utilities consumption per hour")
    net_salary_rate = fields.Float(string="Net Salary Rate")
    salary_contributions = fields.Float(string="Salary Contributions")
