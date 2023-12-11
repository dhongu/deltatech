# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # valuation_level se poate modifica daca nu sunt facute miscari de stoc
    valuation_area_level = fields.Selection(
        [("company", "Company"), ("warehouse", "Warehouse"), ("location", "Location")],
        string="Valuation Area Level",
        default="company",
    )
    valuation_lot_level = fields.Boolean(string="Valuation Lot Level", default=False)
    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area")
