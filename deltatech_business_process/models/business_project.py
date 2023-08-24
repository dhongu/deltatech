# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProject(models.Model):
    _name = "business.project"
    _description = "Business project"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)
    state = fields.Selection(
        [
            ("preparation", "Preparation"),
            ("exploitation", "Exploitation"),
            ("realization", "Realization"),
            ("deployment", "Deployment"),
            ("running", "Running"),
            ("closed", "Closed"),
        ],
        string="State",
        default="preparation",
    )
