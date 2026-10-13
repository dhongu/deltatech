# Copyright (C) 2026 Terrabit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    logo = fields.Binary(
        string="Logo",
        attachment=True,
        help="Logo afișat în rapoartele (factură, ofertă, aviz) emise pentru această "
        "echipă de vânzare. Dacă este gol, se folosește logo-ul firmei.",
    )
