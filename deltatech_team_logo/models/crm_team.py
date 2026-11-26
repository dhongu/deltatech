# Copyright (C) 2026 Terrabit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    logo = fields.Binary(
        string="Logo",
        attachment=True,
        help="Logo printed on the reports (invoice, quotation, delivery slip) issued for "
        "this sales team. If empty, the company logo is used.",
    )
