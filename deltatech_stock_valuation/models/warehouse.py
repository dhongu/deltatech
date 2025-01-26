# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area")
