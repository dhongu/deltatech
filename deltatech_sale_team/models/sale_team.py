# See README.rst file on addons root folder for license details

from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    team_type = fields.Selection(
        [("sales", "Sales"), ("website", "Website")],
        string="Team Type",
        default="sales",
        required=True,
        help="The type of this channel, it will define the resources this channel uses.",
    )
