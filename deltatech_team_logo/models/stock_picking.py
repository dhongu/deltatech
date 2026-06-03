# Copyright (C) 2026 Terrabit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    team_id = fields.Many2one(
        "crm.team",
        string="Sales Team",
        compute="_compute_team_id",
        store=False,
        help="Echipa de vânzare a comenzii sursă, folosită pentru logo-ul din rapoarte.",
    )

    @api.depends("sale_id", "sale_id.team_id")
    def _compute_team_id(self):
        for picking in self:
            picking.team_id = picking.sale_id.team_id
